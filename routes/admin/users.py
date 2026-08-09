# routes/admin/users.py

from flask import render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from models import User, Role, Organisation
from routes.admin import admin_bp
from utils.decorators import admin_required
from utils.audit import log_audit_action


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """List all users"""
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = g.db.query(User)

    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)

    if search:
        query = query.filter(
            User.full_name.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    roles = g.db.query(Role).order_by(Role.name).all()

    return render_template(
        'admin/users/list.html',
        users=users,
        roles=roles,
        role_filter=role_filter,
        search=search,
        page=page,
        total=total,
        per_page=per_page
    )


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    roles = g.db.query(Role).order_by(Role.name).all()
    organisations = g.db.query(Organisation).filter(
        Organisation.is_active == True
    ).order_by(Organisation.name).all()

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        position = request.form.get('position', '').strip()
        role_id = request.form.get('role_id', type=int)
        organisation_id = request.form.get('organisation_id', type=int) or None
        password = request.form.get('password', '')

        errors = []
        if not first_name or not last_name or not email or not password or not role_id:
            errors.append('All required fields must be filled.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        existing = g.db.query(User).filter(User.email == email).first()
        if existing:
            errors.append('A user with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/users/form.html', user=None, roles=roles, organisations=organisations)

        user = User(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            email=email,
            phone=phone,
            position=position,
            role_id=role_id,
            organisation_id=organisation_id,
            is_active=True,
            is_verified=True,
            must_change_password=True
        )
        user.set_password(password)
        g.db.add(user)
        g.db.commit()

        log_audit_action('create', 'User', user.id, f'Admin created user {user.email}')
        flash(f'User {user.full_name} created successfully!', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users/form.html', user=None, roles=roles, organisations=organisations)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    user = g.db.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users_list'))

    roles = g.db.query(Role).order_by(Role.name).all()
    organisations = g.db.query(Organisation).filter(
        Organisation.is_active == True
    ).order_by(Organisation.name).all()

    if request.method == 'POST':
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.full_name = f"{user.first_name} {user.last_name}"
        user.email = request.form.get('email', '').strip().lower()
        user.phone = request.form.get('phone', '').strip()
        user.position = request.form.get('position', '').strip()
        user.role_id = request.form.get('role_id', type=int)
        user.organisation_id = request.form.get('organisation_id', type=int) or None

        existing = g.db.query(User).filter(
            User.email == user.email,
            User.id != user.id
        ).first()
        if existing:
            flash('Email already in use by another user.', 'danger')
            return render_template('admin/users/form.html', user=user, roles=roles, organisations=organisations)

        g.db.commit()
        log_audit_action('update', 'User', user.id, f'User edited by {current_user.email}')
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users/form.html', user=user, roles=roles, organisations=organisations)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Activate/deactivate user"""
    user = g.db.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('You cannot deactivate yourself.', 'danger')
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    g.db.commit()

    action = 'activated' if user.is_active else 'deactivated'
    log_audit_action('update', 'User', user.id, f'User {action} by {current_user.email}')
    flash(f'User {user.full_name} {action}.', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset user password"""
    user = g.db.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users_list'))

    new_password = request.form.get('new_password', '')
    if len(new_password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return redirect(url_for('admin.users_list'))

    user.set_password(new_password)
    user.must_change_password = True
    g.db.commit()

    log_audit_action('update', 'User', user.id, f'Password reset by {current_user.email}')
    flash(f'Password reset for {user.full_name}.', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = g.db.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users_list'))

    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.users_list'))

    user_name = user.full_name
    g.db.delete(user)
    g.db.commit()

    log_audit_action('delete', 'User', user_id, f'User {user_name} deleted by {current_user.email}')
    flash(f'User {user_name} deleted.', 'success')
    return redirect(url_for('admin.users_list'))
