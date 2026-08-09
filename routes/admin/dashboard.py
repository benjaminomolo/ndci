# routes/admin/dashboard.py

from datetime import datetime, timezone
from flask import render_template, g
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models import (
    Organisation, OrganisationApplication, ApplicationStatus,
    ConsortiumMembership, Document, User
)
from routes.admin import admin_bp
from utils.decorators import admin_required


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard - Overview"""

    # Overall stats
    total_organisations = g.db.query(Organisation).filter(
        Organisation.is_active == True
    ).count()

    pending_registrations = g.db.query(OrganisationApplication).join(
        ApplicationStatus
    ).filter(
        ApplicationStatus.code.in_(['submitted', 'under_review'])
    ).count()

    approved_registrations = g.db.query(OrganisationApplication).join(
        ApplicationStatus
    ).filter(
        ApplicationStatus.code == 'approved'
    ).count()

    total_users = g.db.query(User).filter(
        User.is_active == True
    ).count()

    # Document stats
    accepted_docs = g.db.query(Document).filter(
        Document.status == 'accepted'
    ).count()

    pending_docs = g.db.query(Document).filter(
        Document.status == 'submitted'
    ).count()

    rejected_docs = g.db.query(Document).filter(
        Document.status == 'rejected'
    ).count()

    incomplete_count = g.db.query(OrganisationApplication).join(
        ApplicationStatus
    ).filter(
        ApplicationStatus.code.in_(['submitted', 'info_requested'])
    ).count()

    # Recent registrations
    recent_registrations = g.db.query(OrganisationApplication).options(
        joinedload(OrganisationApplication.organisation),
        joinedload(OrganisationApplication.status)
    ).order_by(
        OrganisationApplication.created_at.desc()
    ).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_organisations=total_organisations,
        pending_registrations=pending_registrations,
        approved_registrations=approved_registrations,
        total_users=total_users,
        accepted_docs=accepted_docs,
        pending_docs=pending_docs,
        rejected_docs=rejected_docs,
        incomplete_count=incomplete_count,
        recent_registrations=recent_registrations
    )
