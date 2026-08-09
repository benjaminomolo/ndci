# routes/admin/settings.py

from flask import render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from models import DocumentType, Sector, RegistrationAuthority, OrganisationType
from routes.admin import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Settings page with tabs"""
    tab = request.args.get('tab', 'documents')

    document_types = g.db.query(DocumentType).filter(
        DocumentType.is_active == True
    ).order_by(DocumentType.name).all()

    sectors = g.db.query(Sector).filter(
        Sector.is_active == True
    ).order_by(Sector.name).all()

    authorities = g.db.query(RegistrationAuthority).filter(
        RegistrationAuthority.is_active == True
    ).order_by(RegistrationAuthority.name).all()

    org_types = g.db.query(OrganisationType).filter(
        OrganisationType.is_active == True
    ).order_by(OrganisationType.name).all()

    return render_template(
        'admin/settings.html',
        tab=tab,
        document_types=document_types,
        sectors=sectors,
        authorities=authorities,
        org_types=org_types
    )
