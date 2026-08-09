# seed_data.py
# Seed data for NDCI database

from datetime import datetime, timezone
from models import (
    Role, Sector, State, County, Ministry, OrganisationType,
    DocumentType, ApplicationStatus, MembershipStatus,
    RegistrationAuthority, User
)


def seed_database(db):
    """Seed the database with initial data"""

    now = datetime.now(timezone.utc)

    # ============================================================
    # ROLES
    # ============================================================
    roles = [
        Role(name='Super Admin', description='Full system access'),
        Role(name='NDCI Admin', description='NDCI administrator'),
        Role(name='Board Member', description='Board of Directors member'),
        Role(name='Technical Expert', description='Technical unit expert'),
        Role(name='Ministry User', description='Ministry representative'),
        Role(name='Regional Coordinator', description='Regional office coordinator'),
        Role(name='NGO Admin', description='NGO administrator'),
        Role(name='NGO User', description='NGO staff user'),
        Role(name='Donor Viewer', description='Donor read-only access'),
    ]
    db.add_all(roles)
    db.flush()

    # ============================================================
    # SECTORS
    # ============================================================
    # Replace the sectors section in your seed data with:

    sectors = [
        Sector(
            name='Culture and Tourism',
            code='CULT',
            description='Cultural heritage, arts, tourism, wildlife conservation, and environmental protection'
        ),
        Sector(
            name='Education and Skills Development',
            code='EDU',
            description='Schools, teacher training, vocational skills, and educational access'
        ),
        Sector(
            name='Health and Environment',
            code='HLTH',
            description='Healthcare, mental health, HIV/AIDS, environmental health, and wellbeing'
        ),
        Sector(
            name='Sports Development and Youth Empowerment',
            code='SPORT',
            description='Sports, youth development, recreation, and youth employment'
        ),
        Sector(
            name='Humanitarian and Social Development',
            code='HUM',
            description='Humanitarian response, women empowerment, children, peace building, and social development'
        ),
    ]

    db.add_all(sectors)
    db.flush()

    # ============================================================
    # STATES
    # ============================================================
    states = [
        State(name='Central Equatoria State', code='CE'),
        State(name='Eastern Equatoria State', code='EE'),
        State(name='Jonglei State', code='JG'),
        State(name='Lakes State', code='LK'),
        State(name='Northern Bahr el Ghazal State', code='NBG'),
        State(name='Unity State', code='UN'),
        State(name='Upper Nile State', code='UNL'),
        State(name='Warrap State', code='WR'),
        State(name='Western Bahr el Ghazal State', code='WBG'),
        State(name='Western Equatoria State', code='WE'),
        State(name='Abyei Administrative Area', code='ABY', is_administrative_area=True),
        State(name='Greater Pibor Administrative Area', code='GP', is_administrative_area=True),
        State(name='Ruweng Administrative Area', code='RW', is_administrative_area=True),
    ]
    db.add_all(states)
    db.flush()

    # ============================================================
    # MINISTRIES
    # ============================================================
    ministries = [
        Ministry(name='Ministry of General Education and Instruction', short_name='MoGEI',
                description='Responsible for general education and instruction'),
        Ministry(name='Ministry of Culture, Museum and National Heritage', short_name='MoCMNH',
                description='Responsible for culture, museums and national heritage'),
        Ministry(name='Ministry of Health', short_name='MoH',
                description='Responsible for health services and policy'),
        Ministry(name='Ministry of Youth and Sports', short_name='MoYS',
                description='Responsible for youth affairs and sports development'),
        Ministry(name='Ministry of Humanitarian Affairs and Disaster Management', short_name='MoHADM',
                description='Responsible for humanitarian affairs and disaster management'),
        Ministry(name='Ministry of Wildlife, Conservation and Tourism', short_name='MoWCT',
                description='Responsible for wildlife, conservation and tourism'),
    ]
    db.add_all(ministries)
    db.flush()

    # ============================================================
    # ORGANISATION TYPES
    # ============================================================
    org_types = [
        OrganisationType(name='National NGO', description='National non-governmental organisation'),
        OrganisationType(name='International NGO', description='International non-governmental organisation'),
        OrganisationType(name='Community-Based Organisation', description='Community-based organisation (CBO)'),
        OrganisationType(name='Faith-Based Organisation', description='Faith-based organisation (FBO)'),
        OrganisationType(name='Youth Association', description='Youth-led association or group'),
        OrganisationType(name='Academic Institution', description='University, college or academic institution'),
        OrganisationType(name='Vocational Institution', description='Vocational or technical training institution'),
        OrganisationType(name='Private Sector Partner', description='Private sector company or business partner'),
        OrganisationType(name='Professional Association', description='Professional body or association'),
        OrganisationType(name='Other', description='Other type of organisation'),
    ]
    db.add_all(org_types)
    db.flush()

    # ============================================================
    # REGISTRATION AUTHORITIES
    # ============================================================
    authorities = [
        RegistrationAuthority(name='Relief and Rehabilitation Commission', short_name='RRC',
                            description='RRC registration for NGOs'),
        RegistrationAuthority(name='Ministry of Justice and Constitutional Affairs', short_name='MoJCA',
                            description='Legal registration for companies and organisations'),
        RegistrationAuthority(name='Ministry of Trade and Industry', short_name='MTI',
                            description='Business registration'),
        RegistrationAuthority(name='Ministry of Higher Education', short_name='MoHE',
                            description='Academic institution accreditation'),
        RegistrationAuthority(name='Other', short_name='OTHER',
                            description='Other registration authority'),
    ]
    db.add_all(authorities)
    db.flush()

    # ============================================================
    # DOCUMENT TYPES
    # ============================================================
    doc_types = [
        DocumentType(name='Legal Registration Certificate', code='REG_CERT',
                    description='Official registration or accreditation certificate',
                    is_required_for_registration=True, allowed_extensions='pdf,jpg,jpeg,png'),
        DocumentType(name='Organisation Policies / Constitution', code='POLICIES',
                    description='Governance document, constitution or organisational policies',
                    is_required_for_registration=True, allowed_extensions='pdf,doc,docx'),
        DocumentType(name='Executive Director CV', code='ED_CV',
                    description='Curriculum vitae of the head of organisation',
                    is_required_for_registration=True, allowed_extensions='pdf,doc,docx'),
        DocumentType(name='Head of Programme CV', code='HOP_CV',
                    description='Curriculum vitae of the technical lead',
                    is_required_for_registration=True, allowed_extensions='pdf,doc,docx'),
        DocumentType(name='MoGEI Partner Coordination Acknowledgement', code='MOGEI_ACK',
                    description='Acknowledgement from MoGEI Partner Coordination Office',
                    is_required_for_registration=False, allowed_extensions='pdf,jpg,jpeg,png'),
        DocumentType(name='Annual Report', code='ANNUAL_RPT',
                    description='Most recent annual report',
                    is_required_for_registration=False, allowed_extensions='pdf'),
        DocumentType(name='Financial Report', code='FIN_RPT',
                    description='Most recent financial or audit report',
                    is_required_for_registration=False, allowed_extensions='pdf'),
        DocumentType(name='Additional Licence', code='ADD_LIC',
                    description='Additional professional licence or accreditation',
                    is_required_for_registration=False, allowed_extensions='pdf,jpg,jpeg,png'),
    ]
    db.add_all(doc_types)
    db.flush()

    # ============================================================
    # APPLICATION STATUSES
    # ============================================================
    app_statuses = [
        ApplicationStatus(name='Draft', code='draft',
                         description='Application is being prepared', sort_order=1),
        ApplicationStatus(name='Submitted', code='submitted',
                         description='Application has been submitted', sort_order=2),
        ApplicationStatus(name='Under Review', code='under_review',
                         description='Application is under review', sort_order=3),
        ApplicationStatus(name='Information Requested', code='info_requested',
                         description='Additional information requested from applicant', sort_order=4),
        ApplicationStatus(name='Approved', code='approved',
                         description='Application has been approved', sort_order=5, is_final=True),
        ApplicationStatus(name='Rejected', code='rejected',
                         description='Application has been rejected', sort_order=6, is_final=True),
    ]
    db.add_all(app_statuses)
    db.flush()

    # ============================================================
    # MEMBERSHIP STATUSES
    # ============================================================
    mem_statuses = [
        MembershipStatus(name='Active', code='active', description='Active consortium member'),
        MembershipStatus(name='Suspended', code='suspended', description='Membership suspended'),
        MembershipStatus(name='Expired', code='expired', description='Membership has expired'),
        MembershipStatus(name='Revoked', code='revoked', description='Membership has been revoked'),
    ]
    db.add_all(mem_statuses)
    db.flush()

    print("Seed data created successfully!")
