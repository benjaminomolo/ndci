# routes/registrations.py
# Public organisation registration submission

import os
import secrets
import logging
from datetime import datetime, timezone
from flask import (
    Blueprint, request, jsonify, render_template, g
)
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models import (
    Organisation, OrganisationApplication, OrganisationContact,
    OrganisationCoverage, OrganisationSector,
    ApplicationSector, ApplicationStatus, ApplicationStatusLog,
    Document, DocumentType, User, Role
)
from config import (
    UPLOAD_SUBFOLDERS, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES,
    DOCUMENT_MAX_SIZE_MB, APPLICATION_STATUS_SUBMITTED,
    REFERENCE_PREFIX
)
from utils.audit import log_audit_action

logger = logging.getLogger(__name__)

registrations_bp = Blueprint('registrations', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_mime_type(file_storage):
    """Validate file MIME type"""
    if not file_storage or '.' not in file_storage.filename:
        return False
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    expected = ALLOWED_MIME_TYPES.get(ext)
    return expected and file_storage.content_type == expected


def save_uploaded_file(file_storage, subfolder='documents'):
    """
    Save file with secure random name.
    Returns (secure_name, original_name, size_kb, path)
    """
    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    secure_name = f"{secrets.token_hex(16)}.{ext}"

    upload_path = UPLOAD_SUBFOLDERS.get(subfolder, UPLOAD_SUBFOLDERS['documents'])
    os.makedirs(upload_path, exist_ok=True)

    file_path = os.path.join(upload_path, secure_name)
    file_storage.save(file_path)

    file_size_kb = os.path.getsize(file_path) // 1024
    return secure_name, original_name, file_size_kb, file_path


def generate_reference_number():
    """Generate unique registration reference number"""
    year = datetime.now(timezone.utc).year

    count = g.db.query(OrganisationApplication).filter(
        OrganisationApplication.application_year == year
    ).count()

    return f"{REFERENCE_PREFIX}-{year}-{count + 1:04d}"


@registrations_bp.route('/submit-registration', methods=['POST'])
def submit_registration():
    """Handle organisation registration form submission"""
    errors = []
    saved_files = []

    try:
        # ============================================================
        # STEP 1: Organisation Identity
        # ============================================================
        org_name = request.form.get('organisation_name', '').strip()
        org_acronym = request.form.get('organisation_acronym', '').strip()
        org_type_id = request.form.get('organisation_type_id', type=int)
        year_established = request.form.get('year_established', type=int)
        reg_number = request.form.get('registration_number', '').strip()
        reg_authority_id = request.form.get('registration_authority_id', type=int)
        reg_authority_other = request.form.get('registration_authority_other', '').strip()
        reg_date = request.form.get('registration_date')
        reg_expiry = request.form.get('registration_expiry')
        head_office_state_id = request.form.get('head_office_state_id', type=int)
        physical_address = request.form.get('physical_address', '').strip()
        org_email = request.form.get('organisation_email', '').strip()
        org_phone = request.form.get('organisation_phone', '').strip()
        org_website = request.form.get('organisation_website', '').strip()

        # Portal account credentials
        portal_email = request.form.get('portal_email', '').strip()
        portal_password = request.form.get('portal_password', '')
        portal_password_confirm = request.form.get('portal_password_confirm', '')

        # Validate Step 1
        if not org_name:
            errors.append('Organisation name is required.')
        if not org_type_id:
            errors.append('Organisation type is required.')
        if not reg_number:
            errors.append('Registration/accreditation number is required.')
        if not org_email:
            errors.append('Organisation email is required.')
        if not head_office_state_id:
            errors.append('Head office state is required.')

        # Validate portal account
        user_email = portal_email if portal_email else request.form.get('contact_email', '').strip()
        if not portal_password:
            errors.append('Password is required for portal access.')
        elif len(portal_password) < 8:
            errors.append('Password must be at least 8 characters.')
        elif portal_password != portal_password_confirm:
            errors.append('Passwords do not match.')

        # ============================================================
        # STEP 2: Contact & Coverage
        # ============================================================
        contact_name = request.form.get('contact_name', '').strip()
        contact_position = request.form.get('contact_position', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        coverage_states = request.form.getlist('coverage_states[]') or \
                          request.form.getlist('coverage_states')

        selected_sectors = request.form.getlist('sectors[]') or \
                           request.form.getlist('sectors')
        primary_sector = request.form.get('primary_sector', type=int)

        if not contact_name:
            errors.append('Contact person name is required.')
        if not contact_email:
            errors.append('Contact email is required.')
        if not contact_phone:
            errors.append('Contact phone is required.')
        if not coverage_states:
            errors.append('At least one state of operation is required.')
        if not selected_sectors:
            errors.append('At least one sector must be selected.')
        if not primary_sector:
            errors.append('Primary sector must be selected.')

        # Use contact email as portal email if not specified
        if not portal_email:
            user_email = contact_email

        # ============================================================
        # STEP 3: Documents
        # ============================================================
        uploaded_docs = []
        doc_type_ids = request.form.getlist('document_type_ids[]') or \
                       request.form.getlist('document_type_ids')

        for doc_type_id in doc_type_ids:
            file = request.files.get(f'document_{doc_type_id}')

            if file and file.filename and allowed_file(file.filename):
                if not validate_mime_type(file):
                    errors.append(f'Invalid file type for document ID {doc_type_id}.')
                    continue

                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)

                max_bytes = DOCUMENT_MAX_SIZE_MB * 1024 * 1024
                if file_size > max_bytes:
                    errors.append(f'File exceeds {DOCUMENT_MAX_SIZE_MB}MB limit.')
                    continue

                uploaded_docs.append({
                    'document_type_id': int(doc_type_id),
                    'file': file
                })
            else:
                doc_type = g.db.get(DocumentType, int(doc_type_id))
                if doc_type and doc_type.is_required_for_registration:
                    errors.append(f'Required document "{doc_type.name}" is missing.')

        # ============================================================
        # STEP 4: Declarations
        # ============================================================
        decl_accuracy = request.form.get('declaration_accuracy') in ('on', 'true', '1')
        decl_consent = request.form.get('declaration_consent') in ('on', 'true', '1')

        if not decl_accuracy:
            errors.append('You must confirm the accuracy of the information provided.')
        if not decl_consent:
            errors.append('You must consent to data processing.')

        # ============================================================
        # CHECK FOR DUPLICATES
        # ============================================================

        # Check if organisation name already exists
        existing_org = g.db.query(Organisation).filter(
            func.lower(Organisation.name) == func.lower(org_name)
        ).first()

        if existing_org:
            errors.append(
                f'An organisation named "{existing_org.name}" is already registered. '
                f'If this is your organisation, please contact NDCI administration.'
            )

        # Check if user email already has an account
        existing_user = g.db.query(User).filter(
            func.lower(User.email) == user_email.lower()
        ).first()

        if existing_user:
            errors.append(
                f'A portal account with email "{user_email}" already exists. '
                f'Please use a different email or login to your existing account.'
            )

        # ============================================================
        # RETURN VALIDATION ERRORS IF ANY
        # ============================================================
        if errors:
            logger.warning(f"Registration validation failed: {len(errors)} errors")
            return jsonify({
                'success': False,
                'message': 'Please correct the following errors:',
                'errors': errors
            }), 400

        # ============================================================
        # DATABASE TRANSACTION
        # ============================================================

        # Parse dates
        parsed_reg_date = None
        if reg_date:
            try:
                parsed_reg_date = datetime.strptime(reg_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'errors': ['Invalid registration date format.']
                }), 400

        parsed_reg_expiry = None
        if reg_expiry:
            try:
                parsed_reg_expiry = datetime.strptime(reg_expiry, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'errors': ['Invalid expiry date format.']
                }), 400

        # Find or create organisation
        organisation = g.db.query(Organisation).filter(
            Organisation.registration_number == reg_number
        ).first()

        if organisation:
            organisation.organisation_type_id = org_type_id
            organisation.registration_authority_id = reg_authority_id
            organisation.head_office_state_id = head_office_state_id
            organisation.name = org_name
            organisation.acronym = org_acronym if org_acronym else None
            organisation.year_established = year_established
            organisation.registration_authority_other = reg_authority_other if not reg_authority_id else None
            organisation.registration_date = parsed_reg_date
            organisation.registration_expiry = parsed_reg_expiry
            organisation.physical_address = physical_address
            organisation.email = org_email
            organisation.phone = org_phone
            organisation.website = org_website if org_website else None
        else:
            organisation = Organisation(
                organisation_type_id=org_type_id,
                registration_authority_id=reg_authority_id,
                head_office_state_id=head_office_state_id,
                name=org_name,
                acronym=org_acronym if org_acronym else None,
                year_established=year_established,
                registration_number=reg_number,
                registration_authority_other=reg_authority_other if not reg_authority_id else None,
                registration_date=parsed_reg_date,
                registration_expiry=parsed_reg_expiry,
                physical_address=physical_address,
                email=org_email,
                phone=org_phone,
                website=org_website if org_website else None,
                is_active=True,
                is_verified=False
            )
            g.db.add(organisation)
            g.db.flush()

        # Save contact
        existing_contact = g.db.query(OrganisationContact).filter(
            OrganisationContact.organisation_id == organisation.id,
            OrganisationContact.email == contact_email
        ).first()

        if not existing_contact:
            contact = OrganisationContact(
                organisation_id=organisation.id,
                full_name=contact_name,
                position=contact_position if contact_position else None,
                email=contact_email,
                phone=contact_phone,
                is_primary=True
            )
            g.db.add(contact)

        # Get or create 'submitted' status
        submitted_status = g.db.query(ApplicationStatus).filter(
            ApplicationStatus.code == APPLICATION_STATUS_SUBMITTED
        ).first()

        if not submitted_status:
            submitted_status = ApplicationStatus(
                name='Submitted',
                code=APPLICATION_STATUS_SUBMITTED,
                description='Registration has been submitted for review',
                sort_order=2
            )
            g.db.add(submitted_status)
            g.db.flush()

        # Create registration record
        registration = OrganisationApplication(
            organisation_id=organisation.id,
            status_id=submitted_status.id,
            reference_number=generate_reference_number(),
            application_year=datetime.now(timezone.utc).year,
            contact_name=contact_name,
            contact_position=contact_position if contact_position else None,
            contact_email=contact_email,
            contact_phone=contact_phone,
            coverage_summary=f"Operating in {len(coverage_states)} state(s)",
            declaration_accuracy=decl_accuracy,
            declaration_consent=decl_consent,
            submitted_at=datetime.now(timezone.utc)
        )
        g.db.add(registration)
        g.db.flush()

        # Save sectors
        for sector_id in selected_sectors:
            sid = int(sector_id)
            app_sector = ApplicationSector(
                application_id=registration.id,
                sector_id=sid,
                is_primary=(sid == primary_sector)
            )
            g.db.add(app_sector)

        # Save coverage
        g.db.query(OrganisationCoverage).filter(
            OrganisationCoverage.organisation_id == organisation.id
        ).delete()

        for state_id in coverage_states:
            coverage = OrganisationCoverage(
                organisation_id=organisation.id,
                state_id=int(state_id)
            )
            g.db.add(coverage)

        # Save documents
        for doc_info in uploaded_docs:
            file = doc_info['file']
            doc_type_id = doc_info['document_type_id']

            secure_name, original_name, file_size_kb, file_path = save_uploaded_file(file)
            saved_files.append(file_path)

            doc_type = g.db.get(DocumentType, doc_type_id)

            document = Document(
                document_type_id=doc_type_id,
                organisation_id=organisation.id,
                application_id=registration.id,
                title=f"{doc_type.name if doc_type else 'Document'} - {org_name}",
                file_name=secure_name,
                original_file_name=original_name,
                file_path=file_path,
                file_extension=secure_name.rsplit('.', 1)[1].lower(),
                file_size_kb=file_size_kb,
                mime_type=file.content_type,
                version=1,
                is_latest=True,
                status='submitted',
                uploaded_at=datetime.now(timezone.utc)
            )
            g.db.add(document)

        # Create status log
        status_log = ApplicationStatusLog(
            application_id=registration.id,
            status_id=submitted_status.id,
            remarks='Registration submitted via public portal'
        )
        g.db.add(status_log)

        # ============================================================
        # CREATE USER ACCOUNT FOR PORTAL ACCESS
        # ============================================================

        # Get or create NGO Admin role
        ngo_admin_role = g.db.query(Role).filter_by(name='NGO Admin').first()
        if not ngo_admin_role:
            ngo_admin_role = Role(
                name='NGO Admin',
                description='NGO administrator with portal access'
            )
            g.db.add(ngo_admin_role)
            g.db.flush()

        # Check if user already exists
        existing_user = g.db.query(User).filter(
            func.lower(User.email) == user_email.lower()
        ).first()

        if not existing_user:
            name_parts = contact_name.strip().split()
            first_name = name_parts[0] if name_parts else 'User'
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            user = User(
                organisation_id=organisation.id,
                role_id=ngo_admin_role.id,
                first_name=first_name,
                last_name=last_name,
                full_name=contact_name,
                email=user_email,
                phone=contact_phone,
                position=contact_position,
                is_active=True,
                is_verified=True,
                must_change_password=False
            )
            user.set_password(portal_password)
            g.db.add(user)
            logger.info(f"Portal account created: {user_email}")
        else:
            if not existing_user.organisation_id:
                existing_user.organisation_id = organisation.id

        # ============================================================
        # COMMIT TRANSACTION
        # ============================================================
        g.db.commit()

        logger.info(f"Registration submitted: {registration.reference_number} - {org_name}")

        log_audit_action(
            'submit',
            'OrganisationApplication',
            registration.id,
            f'Organisation "{org_name}" registered with reference {registration.reference_number}'
        )

        return jsonify({
            'success': True,
            'message': 'Registration complete! You can now login to the partner portal.',
            'reference_number': registration.reference_number,
            'redirect_url': f"/registration-confirmation?ref={registration.reference_number}"
        }), 201

    except Exception as e:
        g.db.rollback()

        for file_path in saved_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass

        logger.error(f"Registration submission error: {e}", exc_info=True)

        return jsonify({
            'success': False,
            'message': 'An error occurred while submitting your registration. Please try again.',
            'error': str(e)
        }), 500


@registrations_bp.route('/registration-confirmation')
def confirmation():
    """Registration confirmation page"""
    reference = request.args.get('ref', '')
    return render_template('public/confirmation.html', reference_number=reference)
