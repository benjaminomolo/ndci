# routes/partner/dashboard.py
# Partner/NGO Portal Dashboard

from datetime import datetime, timezone
from flask import render_template, g, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models import (
    Organisation, OrganisationApplication, ApplicationStatus,
    ConsortiumMembership, Document, Programme, ProgrammePartner,
    Meeting, Notification
)
from routes.partner import partner_bp


@partner_bp.route('/dashboard')
@login_required
def dashboard():
    """Partner portal dashboard"""
    # Get user's organisation
    if not current_user.organisation_id:
        return render_template('partner/no_organisation.html')

    organisation = g.db.get(Organisation, current_user.organisation_id)

    if not organisation:
        return render_template('partner/no_organisation.html')

    # Latest application status
    latest_application = g.db.query(OrganisationApplication).filter(
        OrganisationApplication.organisation_id == organisation.id
    ).options(
        joinedload(OrganisationApplication.status)
    ).order_by(
        OrganisationApplication.created_at.desc()
    ).first()

    # Membership status
    membership = g.db.query(ConsortiumMembership).filter(
        ConsortiumMembership.organisation_id == organisation.id,
        ConsortiumMembership.is_active == True
    ).options(
        joinedload(ConsortiumMembership.status)
    ).first()

    # Active programmes count
    active_programmes = g.db.query(Programme).join(
        ProgrammePartner
    ).filter(
        ProgrammePartner.organisation_id == organisation.id,
        Programme.status == 'active'
    ).count()

    # Document statistics
    total_documents = g.db.query(Document).filter(
        Document.organisation_id == organisation.id
    ).count()

    pending_documents = g.db.query(Document).filter(
        Document.organisation_id == organisation.id,
        Document.status == 'submitted'
    ).count()

    approved_documents = g.db.query(Document).filter(
        Document.organisation_id == organisation.id,
        Document.status == 'accepted'
    ).count()

    rejected_documents = g.db.query(Document).filter(
        Document.organisation_id == organisation.id,
        Document.status == 'rejected'
    ).count()

    # Upcoming meetings
    upcoming_meetings = g.db.query(Meeting).filter(
        Meeting.meeting_date >= datetime.now(timezone.utc),
        Meeting.status == 'scheduled'
    ).order_by(Meeting.meeting_date.asc()).limit(5).all()

    # Recent notifications (unread first, then by date)
    notifications = g.db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.is_read.asc(),  # Unread first
        Notification.created_at.desc()
    ).limit(10).all()

    unread_count = g.db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return render_template(
        'partner/dashboard.html',
        organisation=organisation,
        latest_application=latest_application,
        membership=membership,
        active_programmes=active_programmes,
        total_documents=total_documents,
        pending_documents=pending_documents,
        approved_documents=approved_documents,
        rejected_documents=rejected_documents,
        upcoming_meetings=upcoming_meetings,
        notifications=notifications,
        unread_count=unread_count
    )


@partner_bp.route('/applications')
@login_required
def applications():
    """View all applications for this organisation"""
    if not current_user.organisation_id:
        return redirect(url_for('partner.dashboard'))

    applications = g.db.query(OrganisationApplication).filter(
        OrganisationApplication.organisation_id == current_user.organisation_id
    ).options(
        joinedload(OrganisationApplication.status)
    ).order_by(
        OrganisationApplication.created_at.desc()
    ).all()

    return render_template(
        'partner/applications.html',
        applications=applications
    )


@partner_bp.route('/applications/<int:application_id>')
@login_required
def application_detail(application_id):
    """View application details"""
    application = g.db.query(OrganisationApplication).options(
        joinedload(OrganisationApplication.status),
        joinedload(OrganisationApplication.sectors),
        joinedload(OrganisationApplication.documents),
        joinedload(OrganisationApplication.status_logs)
    ).get_or_404(application_id)

    # Ensure user belongs to this organisation
    if application.organisation_id != current_user.organisation_id:
        return redirect(url_for('partner.dashboard'))

    return render_template(
        'partner/application_detail.html',
        application=application
    )


@partner_bp.route('/documents')
@login_required
def documents():
    """View all organisation documents"""
    if not current_user.organisation_id:
        return redirect(url_for('partner.dashboard'))

    documents = g.db.query(Document).filter(
        Document.organisation_id == current_user.organisation_id
    ).options(
        joinedload(Document.document_type)
    ).order_by(
        Document.uploaded_at.desc()
    ).all()

    return render_template(
        'partner/documents.html',
        documents=documents
    )


@partner_bp.route('/membership')
@login_required
def membership():
    """View membership details"""
    if not current_user.organisation_id:
        return redirect(url_for('partner.dashboard'))

    membership = g.db.query(ConsortiumMembership).filter(
        ConsortiumMembership.organisation_id == current_user.organisation_id
    ).options(
        joinedload(ConsortiumMembership.status)
    ).first()

    if not membership:
        return render_template('partner/no_membership.html')

    return render_template(
        'partner/membership.html',
        membership=membership
    )


@partner_bp.route('/programmes')
@login_required
def programmes():
    """View programmes the organisation participates in"""
    if not current_user.organisation_id:
        return redirect(url_for('partner.dashboard'))

    programme_partners = g.db.query(ProgrammePartner).filter(
        ProgrammePartner.organisation_id == current_user.organisation_id,
        ProgrammePartner.is_active == True
    ).options(
        joinedload(ProgrammePartner.programme).joinedload(Programme.sector)
    ).all()

    return render_template(
        'partner/programmes.html',
        programme_partners=programme_partners
    )


@partner_bp.route('/notifications')
@login_required
def notifications():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = g.db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.created_at.desc()
    )

    total = query.count()
    notifications = query.offset((page - 1) * per_page).limit(per_page).all()

    return render_template(
        'partner/notifications.html',
        notifications=notifications,
        page=page,
        total=total,
        per_page=per_page
    )


@partner_bp.route('/notifications/<int:notification_id>/read')
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = g.db.get(Notification, notification_id)

    if not notification:
        return redirect(url_for('partner.notifications'))

    if notification.user_id != current_user.id:
        return redirect(url_for('partner.notifications'))

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    g.db.commit()

    return redirect(url_for('partner.notifications'))


@partner_bp.route('/notifications/mark-all-read')
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    g.db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({
        'is_read': True,
        'read_at': datetime.now(timezone.utc)
    })
    g.db.commit()

    return redirect(url_for('partner.notifications'))
