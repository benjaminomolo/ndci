# routes/public.py
# Public-facing routes
import logging
import traceback

from flask import Blueprint, render_template, jsonify, g, flash, redirect, url_for
from sqlalchemy.orm import joinedload

from models import (
    Organisation, Programme, Sector, State, County, Ministry,
    OrganisationType, RegistrationAuthority, DocumentType,
    OrganisationTypeDocumentRequirement
)

public_bp = Blueprint('public', __name__)

logger = logging.getLogger(__name__)


# routes/public.py

@public_bp.route('/')
def home():
    """Public home page"""
    # Get stats for the homepage
    total_members = g.db.query(Organisation).filter(
        Organisation.is_active == True,
        Organisation.is_verified == True
    ).count()

    active_programmes = g.db.query(Programme).filter(
        Programme.status == 'active'
    ).options(
        joinedload(Programme.sector),
        joinedload(Programme.lead_ministry)
    ).order_by(Programme.created_at.desc()).limit(3).all()

    sectors = g.db.query(Sector).filter(
        Sector.is_active == True
    ).order_by(Sector.name).all()

    states = g.db.query(State).filter(
        State.is_active == True
    ).order_by(State.name).all()

    ministries = g.db.query(Ministry).filter(
        Ministry.is_active == True
    ).order_by(Ministry.name).all()

    return render_template(
        'public/index.html',
        total_members=total_members,
        active_programmes=active_programmes,
        programmes=active_programmes,
        sectors=sectors,
        states=states,
        ministries=ministries
    )


@public_bp.route('/about')
def about():
    """About page"""
    ministries = g.db.query(Ministry).filter(
        Ministry.is_active == True
    ).order_by(Ministry.name).all()
    return render_template('public/about.html', ministries=ministries)


@public_bp.route('/programmes')
def programmes():
    """Public programmes"""
    programmes = g.db.query(Programme).filter(
        Programme.status.in_(['active', 'approved'])
    ).options(
        joinedload(Programme.sector),
        joinedload(Programme.lead_ministry)
    ).order_by(Programme.created_at.desc()).all()
    return render_template('public/programmes.html', programmes=programmes)


# routes/public.py - Add this route

@public_bp.route('/register')
def register_page():
    """Organisation registration page"""
    try:
        organisation_types = g.db.query(OrganisationType).filter(
            OrganisationType.is_active == True
        ).order_by(OrganisationType.name).all()

        registration_authorities = g.db.query(RegistrationAuthority).filter(
            RegistrationAuthority.is_active == True
        ).order_by(RegistrationAuthority.name).all()

        states = g.db.query(State).filter(
            State.is_active == True
        ).order_by(State.name).all()

        sectors = g.db.query(Sector).filter(
            Sector.is_active == True
        ).order_by(Sector.name).all()

        counties = g.db.query(County).filter(
            County.is_active == True
        ).order_by(County.name).all()

        document_types = g.db.query(DocumentType).filter(
            DocumentType.is_active == True,
            DocumentType.is_required_for_registration == True
        ).order_by(DocumentType.name).all()

        return render_template(
            'public/register.html',
            organisation_types=organisation_types,
            registration_authorities=registration_authorities,
            states=states,
            sectors=sectors,
            counties=counties,
            document_types=document_types
        )

    except Exception as e:
        logger.error(f"Error loading registration page: {e}\n{traceback.format_exc()}", exc_info=True)
        flash('An error occurred while loading the registration page. Please try again.', 'danger')
        return redirect(url_for('public.home'))


@public_bp.route('/api/counties/<int:state_id>')
def get_counties(state_id):
    """API: Get counties for a state"""
    counties = g.db.query(County).filter(
        County.state_id == state_id,
        County.is_active == True
    ).order_by(County.name).all()

    return jsonify([{
        'id': c.id,
        'name': c.name,
        'code': c.code
    } for c in counties])


@public_bp.route('/api/document-requirements/<int:org_type_id>')
def get_document_requirements(org_type_id):
    """API: Get document requirements by org type"""
    requirements = g.db.query(OrganisationTypeDocumentRequirement).filter(
        OrganisationTypeDocumentRequirement.organisation_type_id == org_type_id
    ).options(
        joinedload(OrganisationTypeDocumentRequirement.document_type)
    ).order_by(OrganisationTypeDocumentRequirement.sort_order).all()

    if not requirements:
        doc_types = g.db.query(DocumentType).filter(
            DocumentType.is_active == True,
            DocumentType.is_required_for_registration == True
        ).all()
        return jsonify([{
            'id': dt.id, 'name': dt.name, 'code': dt.code,
            'description': dt.description, 'is_required': True,
            'allowed_extensions': dt.allowed_extensions,
            'max_file_size_mb': dt.max_file_size_mb
        } for dt in doc_types])

    return jsonify([{
        'id': r.document_type.id, 'name': r.document_type.name,
        'code': r.document_type.code,
        'description': r.document_type.description,
        'is_required': r.is_required,
        'allowed_extensions': r.document_type.allowed_extensions,
        'max_file_size_mb': r.document_type.max_file_size_mb
    } for r in requirements])
