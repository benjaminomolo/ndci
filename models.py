# *******************************************************************
# NDCI Database Models - Complete & Corrected
# National Development Consortium Initiative
# *******************************************************************

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, Float,
    ForeignKey, UniqueConstraint, Numeric, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


# ============================================================
# 1. LOOKUP / REFERENCE TABLES
# ============================================================

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship('User', back_populates='role')
    permissions = relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')


class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False, unique=True)
    name = Column(String(150), nullable=False)
    module = Column(String(100))
    description = Column(Text)

    role_permissions = relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)

    role = relationship('Role', back_populates='permissions')
    permission = relationship('Permission', back_populates='role_permissions')

    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
    )


class Sector(Base):
    __tablename__ = 'sectors'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisations = relationship('OrganisationSector', back_populates='sector', cascade='all, delete-orphan')
    programmes = relationship('Programme', back_populates='sector')
    board_members = relationship('BoardMember', back_populates='sector')
    applications = relationship('ApplicationSector', back_populates='sector', cascade='all, delete-orphan')


class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    is_administrative_area = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    counties = relationship('County', back_populates='state', cascade='all, delete-orphan')
    organisations = relationship('Organisation', back_populates='head_office_state')
    regional_offices = relationship('RegionalOffice', back_populates='state')
    organisation_coverage = relationship('OrganisationCoverage', back_populates='state', cascade='all, delete-orphan')
    programme_locations = relationship('ProgrammeLocation', back_populates='state', cascade='all, delete-orphan')


class County(Base):
    __tablename__ = 'counties'
    id = Column(Integer, primary_key=True)
    state_id = Column(Integer, ForeignKey('states.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50))
    is_active = Column(Boolean, default=True)

    state = relationship('State', back_populates='counties')
    organisation_coverage = relationship('OrganisationCoverage', back_populates='county')
    programme_locations = relationship('ProgrammeLocation', back_populates='county')

    __table_args__ = (
        UniqueConstraint('state_id', 'name', name='unique_county_per_state'),
    )


class Ministry(Base):
    __tablename__ = 'ministries'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    short_name = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    contacts = relationship('MinistryContact', back_populates='ministry', cascade='all, delete-orphan')
    board_members = relationship('BoardMember', back_populates='ministry')
    technical_members = relationship('TechnicalUnitMember', back_populates='ministry')
    programmes = relationship('Programme', back_populates='lead_ministry')
    meetings = relationship('MeetingMinistry', back_populates='ministry', cascade='all, delete-orphan')
    mous = relationship('MoU', back_populates='ministry')


class OrganisationType(Base):
    __tablename__ = 'organisation_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    organisations = relationship('Organisation', back_populates='organisation_type')
    document_requirements = relationship('OrganisationTypeDocumentRequirement', back_populates='organisation_type', cascade='all, delete-orphan')


class DocumentType(Base):
    __tablename__ = 'document_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    is_required_for_registration = Column(Boolean, default=False)
    allowed_extensions = Column(String(100), default='pdf,doc,docx,jpg,jpeg,png')
    max_file_size_mb = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)

    documents = relationship('Document', back_populates='document_type')
    org_type_requirements = relationship('OrganisationTypeDocumentRequirement', back_populates='document_type', cascade='all, delete-orphan')


class OrganisationTypeDocumentRequirement(Base):
    """
    Maps organisation types to required/optional document types.
    This allows different organisation types (NGO, CBO, company, academic institution, etc.)
    to have different document requirements during application.
    """
    __tablename__ = 'organisation_type_document_requirements'
    id = Column(Integer, primary_key=True)
    organisation_type_id = Column(Integer, ForeignKey('organisation_types.id', ondelete='CASCADE'), nullable=False)
    document_type_id = Column(Integer, ForeignKey('document_types.id', ondelete='CASCADE'), nullable=False)
    is_required = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisation_type = relationship('OrganisationType', back_populates='document_requirements')
    document_type = relationship('DocumentType', back_populates='org_type_requirements')

    __table_args__ = (
        UniqueConstraint('organisation_type_id', 'document_type_id', name='unique_org_type_document'),
    )


class ApplicationStatus(Base):
    __tablename__ = 'application_statuses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_final = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    applications = relationship('OrganisationApplication', back_populates='status')
    status_logs = relationship('ApplicationStatusLog', back_populates='status')


class MembershipStatus(Base):
    __tablename__ = 'membership_statuses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    memberships = relationship('ConsortiumMembership', back_populates='status')


# ============================================================
# 2. USERS & ACCESS CONTROL
# ============================================================

class User(Base, UserMixin):
    """
    User model with Flask-Login integration.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='SET NULL'), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(50))
    password = Column(String(255), nullable=False)
    position = Column(String(150))
    gender = Column(String(20))
    timezone = Column(String(50), default='Africa/Juba', nullable=False)

    profile_photo = Column(String(255))
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    organisation = relationship('Organisation', back_populates='users', foreign_keys=[organisation_id])

    user_preferences = relationship('UserPreference', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    module_access = relationship('UserModuleAccess', back_populates='user', cascade='all, delete-orphan')

    board_memberships = relationship('BoardMember', back_populates='user')
    technical_memberships = relationship('TechnicalUnitMember', back_populates='user')

    reviewed_applications = relationship(
        'OrganisationApplication',
        back_populates='reviewed_by_user',
        foreign_keys='OrganisationApplication.reviewed_by'
    )
    application_status_logs = relationship('ApplicationStatusLog', back_populates='user')
    application_notes = relationship(
        'ApplicationNote',
        back_populates='user',
        foreign_keys='ApplicationNote.created_by'
    )
    application_notes_recipient = relationship(
        'ApplicationNote',
        back_populates='recipient_user',
        foreign_keys='ApplicationNote.recipient_id'
    )

    uploaded_documents = relationship('Document', back_populates='uploaded_by_user')
    document_reviews = relationship('DocumentReview', back_populates='reviewed_by_user')

    created_programmes = relationship(
        'Programme',
        back_populates='created_by_user',
        foreign_keys='Programme.created_by'
    )
    updated_programmes = relationship(
        'Programme',
        back_populates='updated_by_user',
        foreign_keys='Programme.updated_by'
    )

    meeting_attendances = relationship('MeetingAttendance', back_populates='user')
    created_meetings = relationship('Meeting', back_populates='created_by_user')

    audit_logs = relationship('AuditLog', back_populates='user')
    created_mous = relationship('MoU', back_populates='created_by_user')

    # Self-referential relationships
    creator = relationship('User', remote_side=[id], foreign_keys=[created_by], post_update=True)
    updater = relationship('User', remote_side=[id], foreign_keys=[updated_by], post_update=True)

    # ============================================================
    # INIT METHOD (Fixes the "unexpected argument" error)
    # ============================================================
    def __init__(self, **kwargs):
        """
        Custom init to handle full_name auto-generation
        and ensure proper initialization.
        """
        # Auto-generate full_name if not provided
        if 'full_name' not in kwargs and 'first_name' in kwargs and 'last_name' in kwargs:
            kwargs['full_name'] = f"{kwargs['first_name']} {kwargs['last_name']}"

        super().__init__(**kwargs)

    # ============================================================
    # PASSWORD MANAGEMENT
    # ============================================================
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password against the stored hash."""
        return check_password_hash(self.password, password)

    def get_id(self):
        """Override get_id to return string ID (required by Flask-Login)."""
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email}>'

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    preference_type = Column(String(50), nullable=False)
    preference_value = Column(String(255))
    do_not_show_again = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='user_preferences')

    __table_args__ = (
        UniqueConstraint('user_id', 'preference_type', name='unique_user_preference'),
    )


class UserModuleAccess(Base):
    __tablename__ = 'user_module_access'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    module_name = Column(String(100), nullable=False)
    can_view = Column(Boolean, default=True)
    can_create = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_approve = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='module_access')

    __table_args__ = (
        UniqueConstraint('user_id', 'module_name', name='unique_user_module'),
    )


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default='info')
    reference_type = Column(String(100))
    reference_id = Column(Integer)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='notifications')


# ============================================================
# 3. ORGANISATIONS / NGOs
# ============================================================

class Organisation(Base):
    __tablename__ = 'organisations'
    id = Column(Integer, primary_key=True)
    organisation_type_id = Column(Integer, ForeignKey('organisation_types.id'), nullable=False)
    registration_authority_id = Column(Integer, ForeignKey('registration_authorities.id'), nullable=True)
    head_office_state_id = Column(Integer, ForeignKey('states.id'), nullable=True)

    # Basic identity
    name = Column(String(255), nullable=False)
    acronym = Column(String(50))
    year_established = Column(Integer)

    # Generic legal registration (works for all organisation types)
    registration_number = Column(String(100), unique=True)
    registration_authority_other = Column(String(150))   # for "Other" free-text option
    registration_date = Column(Date, nullable=True)
    registration_expiry = Column(Date, nullable=True)

    # Contact details
    physical_address = Column(Text)
    postal_address = Column(String(255))
    email = Column(String(150))
    phone = Column(String(50))
    website = Column(String(255))
    logo = Column(String(255))

    # Profile
    mission = Column(Text)
    vision = Column(Text)
    description = Column(Text)

    # MoGEI partner coordination
    is_moge_partner = Column(Boolean, default=False)
    moge_partner_number = Column(String(100))

    # System flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    organisation_type = relationship('OrganisationType', back_populates='organisations')
    registration_authority = relationship('RegistrationAuthority', back_populates='organisations')
    head_office_state = relationship('State', back_populates='organisations')

    users = relationship('User', back_populates='organisation', foreign_keys='User.organisation_id')
    contacts = relationship('OrganisationContact', back_populates='organisation', cascade='all, delete-orphan')
    sectors = relationship('OrganisationSector', back_populates='organisation', cascade='all, delete-orphan')
    coverage_areas = relationship('OrganisationCoverage', back_populates='organisation', cascade='all, delete-orphan')
    applications = relationship('OrganisationApplication', back_populates='organisation', cascade='all, delete-orphan')
    memberships = relationship('ConsortiumMembership', back_populates='organisation', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='organisation')
    programme_partners = relationship('ProgrammePartner', back_populates='organisation')
    board_members = relationship('BoardMember', back_populates='organisation')
    technical_members = relationship('TechnicalUnitMember', back_populates='organisation')
    mous = relationship('MoU', back_populates='organisation')

    def __repr__(self):
        return f'<Organisation {self.name}>'


class RegistrationAuthority(Base):
    __tablename__ = 'registration_authorities'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    short_name = Column(String(50))
    description = Column(Text)
    applies_to_org_types = Column(String(255))   # optional metadata, e.g. "NGO,CBO"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisations = relationship('Organisation', back_populates='registration_authority')


class OrganisationContact(Base):
    __tablename__ = 'organisation_contacts'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)

    full_name = Column(String(150), nullable=False)
    position = Column(String(150))
    email = Column(String(150))
    phone = Column(String(50))
    is_primary = Column(Boolean, default=False)
    is_executive_director = Column(Boolean, default=False)
    is_head_of_programme = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisation = relationship('Organisation', back_populates='contacts')


class OrganisationSector(Base):
    __tablename__ = 'organisation_sectors'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)
    sector_id = Column(Integer, ForeignKey('sectors.id', ondelete='CASCADE'), nullable=False)
    is_primary = Column(Boolean, default=False)
    years_of_experience = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisation = relationship('Organisation', back_populates='sectors')
    sector = relationship('Sector', back_populates='organisations')

    __table_args__ = (
        UniqueConstraint('organisation_id', 'sector_id', name='unique_org_sector'),
    )


class OrganisationCoverage(Base):
    __tablename__ = 'organisation_coverage'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)
    state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
    county_id = Column(Integer, ForeignKey('counties.id'), nullable=True)
    communities = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organisation = relationship('Organisation', back_populates='coverage_areas')
    state = relationship('State', back_populates='organisation_coverage')
    county = relationship('County', back_populates='organisation_coverage')

    __table_args__ = (
        UniqueConstraint('organisation_id', 'state_id', 'county_id', name='unique_org_coverage'),
    )


# ============================================================
# 4. NGO REGISTRATION / APPLICATIONS / DUE DILIGENCE
# ============================================================

class OrganisationApplication(Base):
    __tablename__ = 'organisation_applications'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(Integer, ForeignKey('application_statuses.id'), nullable=False)

    reference_number = Column(String(50), nullable=False, unique=True)
    application_year = Column(Integer, nullable=False)

    contact_name = Column(String(150), nullable=False)
    contact_position = Column(String(150))
    contact_email = Column(String(150), nullable=False)
    contact_phone = Column(String(50), nullable=False)

    coverage_summary = Column(Text)
    declaration_accuracy = Column(Boolean, default=False)
    declaration_consent = Column(Boolean, default=False)

    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    decision_notes = Column(Text)
    rejection_reason = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    organisation = relationship('Organisation', back_populates='applications')
    status = relationship('ApplicationStatus', back_populates='applications')
    reviewed_by_user = relationship('User', back_populates='reviewed_applications', foreign_keys=[reviewed_by])

    sectors = relationship('ApplicationSector', back_populates='application', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='application')
    status_logs = relationship('ApplicationStatusLog', back_populates='application', cascade='all, delete-orphan')
    notes = relationship('ApplicationNote', back_populates='application', cascade='all, delete-orphan')
    due_diligence_reviews = relationship('DueDiligenceReview', back_populates='application', cascade='all, delete-orphan')
    membership = relationship('ConsortiumMembership', back_populates='application', uselist=False)


class ApplicationSector(Base):
    __tablename__ = 'application_sectors'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='CASCADE'), nullable=False)
    sector_id = Column(Integer, ForeignKey('sectors.id', ondelete='CASCADE'), nullable=False)
    is_primary = Column(Boolean, default=False)

    application = relationship('OrganisationApplication', back_populates='sectors')
    sector = relationship('Sector', back_populates='applications')

    __table_args__ = (
        UniqueConstraint('application_id', 'sector_id', name='unique_application_sector'),
    )


class ApplicationStatusLog(Base):
    __tablename__ = 'application_status_logs'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(Integer, ForeignKey('application_statuses.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    remarks = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship('OrganisationApplication', back_populates='status_logs')
    status = relationship('ApplicationStatus', back_populates='status_logs')
    user = relationship('User', back_populates='application_status_logs')


class ApplicationNote(Base):
    __tablename__ = 'application_notes'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    note = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship('OrganisationApplication', back_populates='notes')
    user = relationship('User', back_populates='application_notes', foreign_keys=[created_by])
    recipient_user = relationship('User', back_populates='application_notes_recipient', foreign_keys=[recipient_id])


class DueDiligenceReview(Base):
    __tablename__ = 'due_diligence_reviews'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='CASCADE'), nullable=False)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=False)

    legal_status_ok = Column(Boolean)
    governance_ok = Column(Boolean)
    financial_capacity_ok = Column(Boolean)
    technical_capacity_ok = Column(Boolean)
    safeguarding_ok = Column(Boolean)
    document_completeness_ok = Column(Boolean)

    overall_score = Column(Float)
    overall_recommendation = Column(String(100))  # approve / reject / request_more_info
    findings = Column(Text)
    recommendations = Column(Text)

    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship('OrganisationApplication', back_populates='due_diligence_reviews')
    reviewer = relationship('User')


# ============================================================
# 5. DOCUMENTS
# ============================================================

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    document_type_id = Column(Integer, ForeignKey('document_types.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=True)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='CASCADE'), nullable=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='SET NULL'), nullable=True)
    mou_id = Column(Integer, ForeignKey('mous.id', ondelete='SET NULL'), nullable=True)
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_extension = Column(String(20))
    file_size_kb = Column(Integer)
    mime_type = Column(String(100))

    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    status = Column(String(50), default='submitted')  # submitted / under_review / accepted / rejected
    expiry_date = Column(Date, nullable=True)
    notes = Column(Text)

    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    document_type = relationship('DocumentType', back_populates='documents')
    organisation = relationship('Organisation', back_populates='documents')
    application = relationship('OrganisationApplication', back_populates='documents')
    programme = relationship('Programme', back_populates='documents')
    mou = relationship('MoU', back_populates='documents')
    uploaded_by_user = relationship('User', back_populates='uploaded_documents')
    reviews = relationship('DocumentReview', back_populates='document', cascade='all, delete-orphan')


class DocumentReview(Base):
    __tablename__ = 'document_reviews'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    review_status = Column(String(50), nullable=False)  # accepted / rejected / needs_revision
    comments = Column(Text)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship('Document', back_populates='reviews')
    reviewed_by_user = relationship('User', back_populates='document_reviews')


# ============================================================
# 6. CONSORTIUM MEMBERSHIP
# ============================================================

class ConsortiumMembership(Base):
    __tablename__ = 'consortium_memberships'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)
    status_id = Column(Integer, ForeignKey('membership_statuses.id'), nullable=False)
    application_id = Column(Integer, ForeignKey('organisation_applications.id', ondelete='SET NULL'), nullable=True)

    membership_number = Column(String(50), unique=True)
    joined_date = Column(Date)
    renewed_date = Column(Date)
    expiry_date = Column(Date)
    membership_category = Column(String(100))  # full / associate / observer
    is_lead_organisation = Column(Boolean, default=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    organisation = relationship('Organisation', back_populates='memberships')
    status = relationship('MembershipStatus', back_populates='memberships')
    application = relationship('OrganisationApplication', back_populates='membership')


# ============================================================
# 7. GOVERNANCE - BOARD & TECHNICAL UNIT
# ============================================================

class Board(Base):
    __tablename__ = 'boards'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    established_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    members = relationship('BoardMember', back_populates='board', cascade='all, delete-orphan')
    meetings = relationship('Meeting', back_populates='board')


class BoardMember(Base):
    __tablename__ = 'board_members'
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey('boards.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id'), nullable=True)
    ministry_id = Column(Integer, ForeignKey('ministries.id'), nullable=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=True)

    full_name = Column(String(150), nullable=False)
    position_title = Column(String(150))  # Chair, Member, Secretary, Undersecretary representative
    member_category = Column(String(100))  # ministry / cwc / private_ngo / expert
    email = Column(String(150))
    phone = Column(String(50))
    appointment_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    board = relationship('Board', back_populates='members')
    user = relationship('User', back_populates='board_memberships')
    organisation = relationship('Organisation', back_populates='board_members')
    ministry = relationship('Ministry', back_populates='board_members')
    sector = relationship('Sector', back_populates='board_members')


class TechnicalUnit(Base):
    __tablename__ = 'technical_units'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    established_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    members = relationship('TechnicalUnitMember', back_populates='technical_unit', cascade='all, delete-orphan')
    meetings = relationship('Meeting', back_populates='technical_unit')


class TechnicalUnitMember(Base):
    __tablename__ = 'technical_unit_members'
    id = Column(Integer, primary_key=True)
    technical_unit_id = Column(Integer, ForeignKey('technical_units.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id'), nullable=True)
    ministry_id = Column(Integer, ForeignKey('ministries.id'), nullable=True)

    full_name = Column(String(150), nullable=False)
    expertise_area = Column(String(150))
    member_category = Column(String(100))  # ngo_expert / ministry_expert / international_expert
    email = Column(String(150))
    phone = Column(String(50))
    cv_document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    appointment_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    technical_unit = relationship('TechnicalUnit', back_populates='members')
    user = relationship('User', back_populates='technical_memberships')
    organisation = relationship('Organisation', back_populates='technical_members')
    ministry = relationship('Ministry', back_populates='technical_members')
    cv_document = relationship('Document', foreign_keys=[cv_document_id])


class MinistryContact(Base):
    __tablename__ = 'ministry_contacts'
    id = Column(Integer, primary_key=True)
    ministry_id = Column(Integer, ForeignKey('ministries.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(String(150), nullable=False)
    position = Column(String(150))
    directorate = Column(String(150))
    email = Column(String(150))
    phone = Column(String(50))
    is_undersecretary = Column(Boolean, default=False)
    is_technical_nominee = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ministry = relationship('Ministry', back_populates='contacts')


# ============================================================
# 8. REGIONAL STRUCTURE
# ============================================================

class RegionalOffice(Base):
    __tablename__ = 'regional_offices'
    id = Column(Integer, primary_key=True)
    state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
    name = Column(String(255), nullable=False)
    office_address = Column(Text)
    email = Column(String(150))
    phone = Column(String(50))
    coordinator_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    state = relationship('State', back_populates='regional_offices')
    coordinator = relationship('User')
    community_councils = relationship('CommunityAdvisoryCouncil', back_populates='regional_office', cascade='all, delete-orphan')


class CommunityAdvisoryCouncil(Base):
    __tablename__ = 'community_advisory_councils'
    id = Column(Integer, primary_key=True)
    regional_office_id = Column(Integer, ForeignKey('regional_offices.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    community_name = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    regional_office = relationship('RegionalOffice', back_populates='community_councils')
    members = relationship('CommunityCouncilMember', back_populates='council', cascade='all, delete-orphan')


class CommunityCouncilMember(Base):
    __tablename__ = 'community_council_members'
    id = Column(Integer, primary_key=True)
    council_id = Column(Integer, ForeignKey('community_advisory_councils.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(String(150), nullable=False)
    position = Column(String(150))
    phone = Column(String(50))
    gender = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    council = relationship('CommunityAdvisoryCouncil', back_populates='members')


# ============================================================
# 9. PROGRAMMES / PROJECTS / ACTIVITIES
# ============================================================

class Programme(Base):
    __tablename__ = 'programmes'
    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=False)
    lead_ministry_id = Column(Integer, ForeignKey('ministries.id'), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    title = Column(String(255), nullable=False)
    code = Column(String(50), unique=True)
    short_name = Column(String(100))
    description = Column(Text)
    background = Column(Text)
    overall_goal = Column(Text)

    estimated_budget = Column(Numeric(18, 2))
    currency = Column(String(10), default='USD')
    start_date = Column(Date)
    end_date = Column(Date)
    duration_years = Column(Integer)

    status = Column(String(50), default='draft')  # draft / submitted / approved / active / completed / suspended
    implementation_phase = Column(String(50))  # phase_1 / phase_2 / phase_3

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    sector = relationship('Sector', back_populates='programmes')
    lead_ministry = relationship('Ministry', back_populates='programmes')
    created_by_user = relationship('User', back_populates='created_programmes', foreign_keys=[created_by])
    updated_by_user = relationship('User', back_populates='updated_programmes', foreign_keys=[updated_by])

    objectives = relationship('ProgrammeObjective', back_populates='programme', cascade='all, delete-orphan')
    activities = relationship('ProgrammeActivity', back_populates='programme', cascade='all, delete-orphan')
    outcomes = relationship('ProgrammeOutcome', back_populates='programme', cascade='all, delete-orphan')
    budgets = relationship('ProgrammeBudget', back_populates='programme', cascade='all, delete-orphan')
    locations = relationship('ProgrammeLocation', back_populates='programme', cascade='all, delete-orphan')
    partners = relationship('ProgrammePartner', back_populates='programme', cascade='all, delete-orphan')
    documents = relationship('Document', back_populates='programme')
    indicators = relationship('MEIndicator', back_populates='programme', cascade='all, delete-orphan')
    reports = relationship('ProgrammeReport', back_populates='programme', cascade='all, delete-orphan')
    funding_commitments = relationship('FundingCommitment', back_populates='programme')


class ProgrammeObjective(Base):
    __tablename__ = 'programme_objectives'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    objective_number = Column(Integer)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='objectives')


class ProgrammeActivity(Base):
    __tablename__ = 'programme_activities'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    status = Column(String(50), default='planned')
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='activities')


class ProgrammeOutcome(Base):
    __tablename__ = 'programme_outcomes'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    description = Column(Text, nullable=False)
    target_value = Column(String(100))
    actual_value = Column(String(100))
    unit_of_measure = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='outcomes')


class ProgrammeBudget(Base):
    __tablename__ = 'programme_budgets'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    budget_line = Column(String(255), nullable=False)
    category = Column(String(100))  # personnel / infrastructure / training / operations / M&E
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default='USD')
    fiscal_year = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='budgets')


class ProgrammeLocation(Base):
    __tablename__ = 'programme_locations'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    state_id = Column(Integer, ForeignKey('states.id'), nullable=False)
    county_id = Column(Integer, ForeignKey('counties.id'), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='locations')
    state = relationship('State', back_populates='programme_locations')
    county = relationship('County', back_populates='programme_locations')


class ProgrammePartner(Base):
    __tablename__ = 'programme_partners'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False)
    role_in_programme = Column(String(150))  # lead / implementing / technical / consortium_member
    is_active = Column(Boolean, default=True)
    assigned_date = Column(Date)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='partners')
    organisation = relationship('Organisation', back_populates='programme_partners')

    __table_args__ = (
        UniqueConstraint('programme_id', 'organisation_id', name='unique_programme_partner'),
    )


class ProgrammeReport(Base):
    __tablename__ = 'programme_reports'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)
    submitted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    report_type = Column(String(100))  # monthly / quarterly / annual / final
    title = Column(String(255), nullable=False)
    reporting_period_start = Column(Date)
    reporting_period_end = Column(Date)
    summary = Column(Text)
    challenges = Column(Text)
    recommendations = Column(Text)
    status = Column(String(50), default='draft')
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='reports')
    submitter = relationship('User')


# ============================================================
# 10. MONITORING, EVALUATION & LEARNING
# ============================================================

class MEIndicator(Base):
    __tablename__ = 'me_indicators'
    id = Column(Integer, primary_key=True)
    programme_id = Column(Integer, ForeignKey('programmes.id', ondelete='CASCADE'), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    indicator_type = Column(String(50))  # output / outcome / impact
    unit_of_measure = Column(String(100))
    baseline_value = Column(String(100))
    target_value = Column(String(100))
    data_source = Column(String(255))
    collection_frequency = Column(String(50))  # monthly / quarterly / annual
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    programme = relationship('Programme', back_populates='indicators')
    results = relationship('MEResult', back_populates='indicator', cascade='all, delete-orphan')


class MEResult(Base):
    __tablename__ = 'me_results'
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey('me_indicators.id', ondelete='CASCADE'), nullable=False)
    reported_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    reporting_period = Column(String(50))
    period_start = Column(Date)
    period_end = Column(Date)
    actual_value = Column(String(100), nullable=False)
    remarks = Column(Text)
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    indicator = relationship('MEIndicator', back_populates='results')
    reporter = relationship('User')


# ============================================================
# 11. DONORS / FUNDING / MoUs
# ============================================================

class Donor(Base):
    __tablename__ = 'donors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    donor_type = Column(String(100))  # bilateral / multilateral / foundation / private
    contact_name = Column(String(150))
    contact_email = Column(String(150))
    contact_phone = Column(String(50))
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    commitments = relationship('FundingCommitment', back_populates='donor')
    mous = relationship('MoU', back_populates='donor')


class FundingCommitment(Base):
    __tablename__ = 'funding_commitments'
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=False)
    programme_id = Column(Integer, ForeignKey('programmes.id'), nullable=True)

    title = Column(String(255), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default='USD')
    commitment_date = Column(Date)
    disbursement_status = Column(String(50), default='pending')  # pending / partial / disbursed
    conditions = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    donor = relationship('Donor', back_populates='commitments')
    programme = relationship('Programme', back_populates='funding_commitments')
    disbursements = relationship('FundDisbursement', back_populates='commitment', cascade='all, delete-orphan')


class FundDisbursement(Base):
    __tablename__ = 'fund_disbursements'
    id = Column(Integer, primary_key=True)
    commitment_id = Column(Integer, ForeignKey('funding_commitments.id', ondelete='CASCADE'), nullable=False)

    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default='USD')
    disbursement_date = Column(Date)
    reference_number = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    commitment = relationship('FundingCommitment', back_populates='disbursements')


class MoU(Base):
    __tablename__ = 'mous'
    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id'), nullable=True)
    ministry_id = Column(Integer, ForeignKey('ministries.id'), nullable=True)

    title = Column(String(255), nullable=False)
    reference_number = Column(String(100), unique=True)
    mou_type = Column(String(100))  # donor / ministry / consortium / implementing_partner
    description = Column(Text)

    signatory_party_a = Column(String(255))
    signatory_party_b = Column(String(255))
    signed_date = Column(Date)
    effective_date = Column(Date)
    expiry_date = Column(Date)

    status = Column(String(50), default='draft')  # draft / pending_signature / active / expired / terminated
    approval_authority = Column(String(255))
    notes = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    created_by_user = relationship('User', back_populates='created_mous')
    donor = relationship('Donor', back_populates='mous')
    organisation = relationship('Organisation', back_populates='mous')
    ministry = relationship('Ministry', back_populates='mous')
    documents = relationship('Document', back_populates='mou')


# ============================================================
# 12. MEETINGS / ACTION POINTS
# ============================================================

class Meeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    board_id = Column(Integer, ForeignKey('boards.id'), nullable=True)
    technical_unit_id = Column(Integer, ForeignKey('technical_units.id'), nullable=True)

    title = Column(String(255), nullable=False)
    meeting_type = Column(String(100))  # consortium / board / technical / ministry_coordination
    venue = Column(String(255))
    meeting_date = Column(DateTime, nullable=False)
    agenda = Column(Text)
    minutes = Column(Text)
    status = Column(String(50), default='scheduled')  # scheduled / completed / cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    created_by_user = relationship('User', back_populates='created_meetings')
    board = relationship('Board', back_populates='meetings')
    technical_unit = relationship('TechnicalUnit', back_populates='meetings')

    attendances = relationship('MeetingAttendance', back_populates='meeting', cascade='all, delete-orphan')
    action_points = relationship('MeetingActionPoint', back_populates='meeting', cascade='all, delete-orphan')
    ministries = relationship('MeetingMinistry', back_populates='meeting', cascade='all, delete-orphan')


class MeetingAttendance(Base):
    __tablename__ = 'meeting_attendances'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    attendee_name = Column(String(150), nullable=False)
    organisation_name = Column(String(255))
    position = Column(String(150))
    attendance_status = Column(String(50), default='present')  # present / absent / excused
    is_chair = Column(Boolean, default=False)
    is_secretary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    meeting = relationship('Meeting', back_populates='attendances')
    user = relationship('User', back_populates='meeting_attendances')


class MeetingActionPoint(Base):
    __tablename__ = 'meeting_action_points'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    action_point = Column(Text, nullable=False)
    responsible_party = Column(String(255))
    due_date = Column(Date)
    status = Column(String(50), default='pending')  # pending / in_progress / completed / overdue
    completion_notes = Column(Text)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    meeting = relationship('Meeting', back_populates='action_points')
    assigned_to = relationship('User')


class MeetingMinistry(Base):
    __tablename__ = 'meeting_ministries'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    ministry_id = Column(Integer, ForeignKey('ministries.id', ondelete='CASCADE'), nullable=False)

    meeting = relationship('Meeting', back_populates='ministries')
    ministry = relationship('Ministry', back_populates='meetings')

    __table_args__ = (
        UniqueConstraint('meeting_id', 'ministry_id', name='unique_meeting_ministry'),
    )


# ============================================================
# 13. CAPACITY BUILDING
# ============================================================

class TrainingProgramme(Base):
    __tablename__ = 'training_programmes'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    training_type = Column(String(100))  # proposal_writing / donor_compliance / financial_management / M&E
    target_audience = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)
    venue = Column(String(255))
    facilitator = Column(String(255))
    status = Column(String(50), default='planned')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    participants = relationship('TrainingParticipant', back_populates='training', cascade='all, delete-orphan')


class TrainingParticipant(Base):
    __tablename__ = 'training_participants'
    id = Column(Integer, primary_key=True)
    training_id = Column(Integer, ForeignKey('training_programmes.id', ondelete='CASCADE'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisations.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    participant_name = Column(String(150), nullable=False)
    email = Column(String(150))
    phone = Column(String(50))
    attendance_status = Column(String(50), default='registered')
    certificate_issued = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    training = relationship('TrainingProgramme', back_populates='participants')
    organisation = relationship('Organisation')
    user = relationship('User')


# ============================================================
# 14. SYSTEM / AUDIT / SETTINGS
# ============================================================

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    action = Column(String(100), nullable=False)  # create / update / delete / login / approve / reject
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    description = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='audit_logs')


class SystemSetting(Base):
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), nullable=False, unique=True)
    setting_value = Column(Text)
    setting_type = Column(String(50), default='string')
    description = Column(Text)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    updater = relationship('User')


class EmailLog(Base):
    __tablename__ = 'email_logs'
    id = Column(Integer, primary_key=True)
    recipient_email = Column(String(150), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text)
    related_entity_type = Column(String(100))
    related_entity_id = Column(Integer)
    status = Column(String(50), default='pending')  # pending / sent / failed
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ActivityReport(Base):
    __tablename__ = 'activity_reports'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    report_period = Column(String(100))
    summary = Column(Text)
    achievements = Column(Text)
    challenges = Column(Text)
    next_steps = Column(Text)
    prepared_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    report_date = Column(Date)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    preparer = relationship('User')


def init_db(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_session(engine):
    """Create a new database session"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    return Session()
