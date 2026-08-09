# routes/partner/__init__.py
# Partner/NGO Portal Blueprint

from flask import Blueprint

partner_bp = Blueprint('partner', __name__, template_folder='../../templates/partner')

# Import routes to register them
from . import dashboard
