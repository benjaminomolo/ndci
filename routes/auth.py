# routes/auth.py
# Authentication routes

from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, g
)
from flask_login import (
    login_user, logout_user, current_user, login_required
)
from sqlalchemy import func
from models import User
from utils.audit import log_audit_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        # Already logged in - redirect based on role
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        # Validate input
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')

        # Find user by email (case-insensitive)
        user = g.db.query(User).filter(
            func.lower(User.email) == email
        ).first()

        # Check credentials
        if user and user.check_password(password):
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact NDCI administration.', 'danger')
                log_audit_action('login_failed', 'User', user.id, f'Deactivated account: {email}')
                return render_template('auth/login.html')

            # Log user in
            login_user(user, remember=remember)
            user.last_login = datetime.now(timezone.utc)
            g.db.commit()

            log_audit_action('login', 'User', user.id, f'User {user.email} logged in')
            flash(f'Welcome back, {user.first_name}!', 'success')

            # Redirect to originally requested page if any
            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            # Redirect based on role
            return _redirect_by_role(user)

        # Failed login
        flash('Invalid email or password.', 'danger')
        log_audit_action('login_failed', 'User', None, f'Failed login attempt: {email}')

    return render_template('auth/login.html')


def _redirect_by_role(user):
    """Redirect user to appropriate dashboard based on role"""
    role_name = user.role.name if user.role else ''

    # Admin roles → Admin dashboard
    admin_roles = [
        'Super Admin',
        'NDCI Admin',
        'Board Member',
        'Technical Expert',
        'Ministry User',
        'Regional Coordinator'
    ]

    # Donor roles → Admin dashboard (or donor dashboard later)
    donor_roles = ['Donor Viewer']

    # NGO roles → Partner dashboard
    ngo_roles = ['NGO Admin', 'NGO User']

    if role_name in admin_roles:
        return redirect(url_for('admin.dashboard'))
    elif role_name in donor_roles:
        return redirect(url_for('admin.dashboard'))  # Change to donor.dashboard later
    elif role_name in ngo_roles:
        return redirect(url_for('partner.dashboard'))
    else:
        # Fallback
        return redirect(url_for('public.home'))

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    if current_user.is_authenticated:
        log_audit_action('logout', 'User', current_user.id, f'User {current_user.email} logged out')

    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('public.home'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        position = request.form.get('position', '').strip()
        gender = request.form.get('gender', '').strip()

        # Validate required fields
        if not first_name or not last_name:
            flash('First name and last name are required.', 'danger')
            return render_template('auth/edit_profile.html', user=current_user)

        # Update user fields
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.full_name = f"{first_name} {last_name}"
        current_user.phone = phone
        current_user.position = position
        current_user.gender = gender

        # Handle password change
        new_password = request.form.get('new_password', '')
        if new_password:
            current_password = request.form.get('current_password', '')

            # Verify current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/edit_profile.html', user=current_user)

            # Validate new password
            if len(new_password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return render_template('auth/edit_profile.html', user=current_user)

            # Optional: Add more password validation
            # if not any(c.isupper() for c in new_password):
            #     flash('Password must contain at least one uppercase letter.', 'danger')
            #     return render_template('auth/edit_profile.html', user=current_user)

            current_user.set_password(new_password)
            current_user.must_change_password = False
            flash('Password updated successfully.', 'success')

        try:
            g.db.commit()
            log_audit_action('update', 'User', current_user.id, 'Profile updated')
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            g.db.rollback()
            flash('An error occurred while updating your profile. Please try again.', 'danger')
            return render_template('auth/edit_profile.html', user=current_user)

    return render_template('auth/edit_profile.html', user=current_user)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = g.db.query(User).filter(
            func.lower(User.email) == email
        ).first()

        if user:
            # Generate reset token
            import secrets
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
            g.db.commit()

            # TODO: Send email with reset link
            # send_password_reset_email(user.email, user.reset_token)

            log_audit_action('password_reset_requested', 'User', user.id, f'Reset requested for {email}')

        # Always show success message (don't reveal if email exists)
        flash('If an account with that email exists, a password reset link has been sent.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user = g.db.query(User).filter(
        User.reset_token == token
    ).first()

    if not user:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.login'))

    if datetime.now(timezone.utc) > user.reset_token_expiry:
        flash('Reset token has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        # Reset password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        user.must_change_password = False
        g.db.commit()

        log_audit_action('password_reset_completed', 'User', user.id, 'Password reset completed')
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page (for already logged-in users)"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate
        if not current_password:
            flash('Please enter your current password.', 'danger')
            return render_template('auth/change_password.html')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')

        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/change_password.html')

        # Update password
        current_user.set_password(new_password)
        current_user.must_change_password = False
        g.db.commit()

        log_audit_action('password_changed', 'User', current_user.id, 'Password changed')
        flash('Password changed successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html')
