# routes/__init__.py
# Blueprint registration

from routes.public import public_bp
from routes.auth import auth_bp
from routes.registrations import registrations_bp
from routes.partner import partner_bp
from routes.admin import admin_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(partner_bp, url_prefix='/partner')
    app.register_blueprint(admin_bp, url_prefix='/admin')
