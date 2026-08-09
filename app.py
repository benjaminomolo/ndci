# app.py

import os
import time
import logging
import click
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify
)
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_mail import Mail
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session

import config as app_config
from config import (
    SECRET_KEY, DEBUG, SQLALCHEMY_DATABASE_URI,
    MAX_CONTENT_LENGTH, cache,
    NDCI_NAME, NDCI_SHORT_NAME, BASE_DIR
)
from models import Base, User


# app.py
# NDCI - National Development Consortium Initiative
# Main Application Factory


def setup_logging(app):
    """Configure application logging"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Set the base logging level
    app.logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Remove default Flask handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    app.logger.addHandler(console_handler)

    # File handler (for persistent logs)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'ndci.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    app.logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    app.logger.addHandler(error_handler)

    app.logger.info(f"NDCI logging initialized. Debug mode: {DEBUG}")


def create_app():
    app = Flask(__name__)
    app.config.from_object(app_config)

    # Database engine
    engine = create_engine(SQLALCHEMY_DATABASE_URI, **app_config.SQLALCHEMY_ENGINE_OPTIONS)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    csrf = CSRFProtect()
    csrf.init_app(app)
    cache.init_app(app)
    mail = Mail()
    mail.init_app(app)

    # Register blueprints
    from routes import register_blueprints
    register_blueprints(app)

    # Database session per request
    @app.before_request
    def create_db_session():
        g.start_time = time.time()
        g.db = Session()

    @app.teardown_appcontext
    def close_db_session(exception=None):
        db_session = g.pop('db', None)
        if db_session is not None:
            if exception:
                db_session.rollback()
            db_session.close()

    # Auth check
    @app.before_request
    def check_auth():
        public_endpoints = [
            'public.home',
            'public.register_page',
            'public.get_counties',
            'public.get_document_requirements',
            'auth.login',
            'auth.logout',
            'registrations.submit_registration',  # ← Add this
            'registrations.confirmation',         # ← Add this
            'static',
            'get_csrf_token',
            'health_check'
        ]

        if request.endpoint in public_endpoints:
            return None

        if not current_user.is_authenticated:
            session['next_url'] = request.url
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

    # Context processor
    @app.context_processor
    def inject_globals():
        return {
            'ndci_name': NDCI_NAME,
            'ndci_short_name': NDCI_SHORT_NAME,
            'current_year': datetime.now(timezone.utc).year,
            'current_user': current_user
        }

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return g.db.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Basic routes
    @app.route('/get-csrf-token')
    def get_csrf_token():
        return jsonify({'csrf_token': generate_csrf()})

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'ok'})

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        if hasattr(g, 'db'):
            g.db.rollback()
        return render_template('errors/500.html'), 500

    # ============================================================
    # CLI COMMANDS
    # ============================================================
    @app.cli.command('init-db')
    def init_db():
        """Create all database tables"""
        Base.metadata.create_all(bind=engine)
        click.echo("✅ Database tables created successfully.")

    @app.cli.command('reset-db')
    def reset_db():
        """Drop and recreate all tables (DEVELOPMENT ONLY)"""
        if click.confirm("⚠️  This will DELETE ALL DATA. Are you sure?"):
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            click.echo("✅ Database reset complete.")

    @app.cli.command('seed-db')
    def seed_db():
        """Seed database with initial data"""
        db = Session()
        try:
            from seed_data import seed_database
            seed_database(db)
            db.commit()
            click.echo("✅ Database seeded successfully.")
        except Exception as e:
            db.rollback()
            click.echo(f"❌ Error: {e}")
        finally:
            db.close()

    @app.cli.command('create-admin')
    def create_admin():
        """Create super admin user"""
        import getpass

        first_name = click.prompt("First name")
        last_name = click.prompt("Last name")
        email = click.prompt("Email")
        phone = click.prompt("Phone", default="")
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            click.echo("❌ Passwords don't match!")
            return

        db = Session()
        try:
            from models import Role

            role = db.query(Role).filter_by(name='Super Admin').first()
            if not role:
                role = Role(name='Super Admin', description='Full system access')
                db.add(role)
                db.flush()

            user = User(
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                email=email,
                phone=phone,
                role_id=role.id,
                is_active=True,
                is_verified=True,
                must_change_password=False
            )
            user.set_password(password)
            db.add(user)
            db.commit()
            click.echo(f"✅ Admin '{email}' created!")
        finally:
            db.close()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5000)), debug=DEBUG)
