# routes/admin/registrations.py
# Admin - Application Review & Management
import os
from datetime import datetime, timezone
from flask import render_template, request, redirect, url_for, flash, g, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from models import (
    OrganisationApplication, Organisation, ApplicationStatus,
    ApplicationStatusLog, ApplicationSector, ApplicationNote,
    OrganisationSector, OrganisationCoverage,
    ConsortiumMembership, MembershipStatus,
    Document, DocumentType, Sector
)
from config import (
    APPLICATION_STATUS_APPROVED, APPLICATION_STATUS_REJECTED,
    APPLICATION_STATUS_INFO_REQUESTED, APPLICATION_STATUS_TRANSITIONS
)
from routes.admin import admin_bp
from utils.decorators import admin_required
from utils.audit import log_audit_action


@admin_bp.route('/registrations')
@login_required
@admin_required
def registrations_list():
    """List all applications with filtering"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = g.db.query(OrganisationApplication).options(
        joinedload(OrganisationApplication.organisation),
        joinedload(OrganisationApplication.status)
    )

    if status_filter:
        query = query.join(ApplicationStatus).filter(
            ApplicationStatus.code == status_filter
        )

    if search:
        query = query.join(Organisation).filter(
            Organisation.name.ilike(f'%{search}%') |
            OrganisationApplication.reference_number.ilike(f'%{search}%')
        )

    total = query.count()
    applications = query.order_by(
        OrganisationApplication.created_at.desc()
    ).offset((page - 1) * per_page).limit(per_page).all()

    statuses = g.db.query(ApplicationStatus).filter(
        ApplicationStatus.is_active == True
    ).order_by(ApplicationStatus.sort_order).all()

    return render_template(
        'admin/applications/list.html',
        applications=applications,
        statuses=statuses,
        current_status=status_filter,
        search=search,
        page=page,
        total=total,
        per_page=per_page
    )


@admin_bp.route('/registrations/<int:registration_id>')
@login_required
@admin_required
def registration_detail(application_id):
    """View application details with documents"""
    application = g.db.query(OrganisationApplication).options(
        joinedload(OrganisationApplication.organisation),
        joinedload(OrganisationApplication.status),
        joinedload(OrganisationApplication.sectors).joinedload(ApplicationSector.sector),
        joinedload(OrganisationApplication.documents).joinedload(Document.document_type),
        joinedload(OrganisationApplication.status_logs).joinedload(ApplicationStatusLog.status),
        joinedload(OrganisationApplication.status_logs).joinedload(ApplicationStatusLog.user),
        joinedload(OrganisationApplication.notes).joinedload(ApplicationNote.user),
        joinedload(OrganisationApplication.due_diligence_reviews)
    ).get_or_404(application_id)

    organisation = application.organisation

    # Get coverage
    coverage = g.db.query(OrganisationCoverage).filter(
        OrganisationCoverage.organisation_id == organisation.id
    ).all()

    # Get all document types (to check what's missing)
    all_doc_types = g.db.query(DocumentType).filter(
        DocumentType.is_active == True
    ).all()

    # Get submitted documents for this application
    submitted_docs = {doc.document_type_id: doc for doc in application.documents}

    # Get available status transitions
    current_code = application.status.code
    allowed_transitions = APPLICATION_STATUS_TRANSITIONS.get(current_code, [])
    available_statuses = g.db.query(ApplicationStatus).filter(
        ApplicationStatus.code.in_(allowed_transitions)
    ).all() if allowed_transitions else []

    return render_template(
        'admin/applications/detail.html',
        application=application,
        organisation=organisation,
        coverage=coverage,
        all_doc_types=all_doc_types,
        submitted_docs=submitted_docs,
        available_statuses=available_statuses
    )


@admin_bp.route('/documents/<int:document_id>/download')
@login_required
@admin_required
def document_download(document_id):
    """Securely download a document"""
    document = g.db.query(Document).get_or_404(document_id)

    if not os.path.exists(document.file_path):
        flash('Document file not found.', 'danger')
        return redirect(request.referrer or url_for('admin.applications_list'))

    log_audit_action('download', 'Document', document.id,
                     f'Document viewed by {current_user.email}')

    directory = os.path.dirname(document.file_path)
    filename = os.path.basename(document.file_path)

    return send_from_directory(directory, filename,
                               download_name=document.original_file_name,
                               as_attachment=True)
