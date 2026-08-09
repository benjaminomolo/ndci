# utils/decorators.py

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Allow: Super Admin, NDCI Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role.name not in ['Super Admin', 'NDCI Admin']:
            flash('Admin access required.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function


def board_required(f):
    """Allow: Super Admin, NDCI Admin, Board Member"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role.name not in ['Super Admin', 'NDCI Admin', 'Board Member']:
            flash('Board access required.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function


def technical_required(f):
    """Allow: Super Admin, NDCI Admin, Technical Expert"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role.name not in ['Super Admin', 'NDCI Admin', 'Technical Expert']:
            flash('Technical access required.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function


def ministry_required(f):
    """Allow: Super Admin, NDCI Admin, Ministry User"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role.name not in ['Super Admin', 'NDCI Admin', 'Ministry User']:
            flash('Ministry access required.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function


def any_admin_required(f):
    """Allow: Any admin-type role (not NGO user, not donor)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        admin_roles = ['Super Admin', 'NDCI Admin', 'Board Member',
                       'Technical Expert', 'Ministry User', 'Regional Coordinator']
        if current_user.role.name not in admin_roles:
            flash('Access denied.', 'danger')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function
