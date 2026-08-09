# routes/admin/__init__.py
# Admin Portal Blueprint

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='../../templates/admin')

# Import routes to register them
from routes.admin import dashboard, applications, settings, documents, users
