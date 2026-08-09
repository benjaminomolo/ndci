# setup.py
# Run this file to set up the database

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS
from models import Base


def init_db():
    """Create all database tables"""
    print("Creating database...")
    engine = create_engine(SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def seed_db():
    """Seed the database with initial data"""
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        from seed_data import seed_database
        seed_database(db)
        db.commit()
        print("✅ Database seeded successfully!")
    except ImportError:
        print("⚠️  seed_data.py not found. Creating basic seed data...")
        _create_basic_seed_data(db)
        db.commit()
        print("✅ Basic seed data created!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


def create_admin():
    """Create a super admin user"""
    from sqlalchemy.orm import sessionmaker
    from models import User, Role
    import getpass

    engine = create_engine(SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        print("\n" + "=" * 40)
        print("  Create Super Admin User")
        print("=" * 40)

        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip().lower()
        phone = input("Phone: ").strip()
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("❌ Passwords don't match!")
            return

        if not all([first_name, last_name, email, password]):
            print("❌ All fields are required!")
            return

        role = db.query(Role).filter_by(name='Super Admin').first()
        if not role:
            role = Role(name='Super Admin', description='Full system access')
            db.add(role)
            db.flush()

        existing = db.query(User).filter_by(email=email).first()
        if existing:
            print(f"❌ User with email '{email}' already exists!")
            return

        user = User(
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            email=email,
            phone=phone,
            role_id=role.id,
            is_active=True,
            is_verified=True,
            must_change_password=False
        )
        user.set_password(password)
        db.add(user)
        db.commit()
        print(f"✅ Admin '{email}' created successfully!")
    finally:
        db.close()


def _create_basic_seed_data(db):
    """Create basic seed data if seed_data.py doesn't exist"""
    from models import (
        Role, Sector, State, Ministry, OrganisationType,
        DocumentType, ApplicationStatus, MembershipStatus,
        RegistrationAuthority
    )
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Roles
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

    # Sectors
    sectors = [
        Sector(name='Education and Skills Development', code='EDU',
               description='Schools, teacher training, vocational skills'),
        Sector(name='Health and Wellbeing', code='HLTH',
               description='Health systems, community health, psychosocial support'),
        Sector(name='Culture, Arts and Heritage', code='CULT', description='Arts, heritage, national unity'),
        Sector(name='Tourism and Hospitality', code='TOUR', description='Tourism development, hospitality training'),
        Sector(name='Youth and Sports', code='YTH', description='Youth empowerment, sports development'),
        Sector(name='Humanitarian Affairs', code='HUM', description='Humanitarian response, disaster management'),
        Sector(name='Environment and Conservation', code='ENV', description='Environmental protection, conservation'),
        Sector(name='Women, Peace and Protection', code='WPP',
               description='Women empowerment, peace building, protection'),
    ]
    db.add_all(sectors)

    # States
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

    # Ministries
    ministries = [
        Ministry(name='Ministry of General Education and Instruction', short_name='MoGEI'),
        Ministry(name='Ministry of Culture, Museum and National Heritage', short_name='MoCMNH'),
        Ministry(name='Ministry of Health', short_name='MoH'),
        Ministry(name='Ministry of Youth and Sports', short_name='MoYS'),
        Ministry(name='Ministry of Humanitarian Affairs and Disaster Management', short_name='MoHADM'),
        Ministry(name='Ministry of Wildlife, Conservation and Tourism', short_name='MoWCT'),
    ]
    db.add_all(ministries)

    # Organisation Types
    org_types = [
        OrganisationType(name='National NGO', description='National non-governmental organisation'),
        OrganisationType(name='Community-Based Organisation', description='Community-based organisation (CBO)'),
        OrganisationType(name='Faith-Based Organisation', description='Faith-based organisation (FBO)'),
        OrganisationType(name='Youth Association', description='Youth-led association'),
        OrganisationType(name='Academic Institution', description='University or academic institution'),
        OrganisationType(name='Vocational Institution', description='Vocational training institution'),
        OrganisationType(name='Private Sector Partner', description='Private sector company or partner'),
        OrganisationType(name='Professional Association', description='Professional body or association'),
        OrganisationType(name='Other', description='Other type of organisation'),
    ]
    db.add_all(org_types)

    # Registration Authorities
    authorities = [
        RegistrationAuthority(name='Relief and Rehabilitation Commission', short_name='RRC'),
        RegistrationAuthority(name='Ministry of Justice and Constitutional Affairs', short_name='MoJCA'),
        RegistrationAuthority(name='Ministry of Trade and Industry', short_name='MTI'),
        RegistrationAuthority(name='Ministry of Higher Education', short_name='MoHE'),
        RegistrationAuthority(name='Other', short_name='OTHER'),
    ]
    db.add_all(authorities)

    # Document Types
    doc_types = [
        DocumentType(name='Legal Registration Certificate', code='REG_CERT', is_required_for_registration=True,
                     allowed_extensions='pdf,jpg,jpeg,png'),
        DocumentType(name='Organisation Policies / Constitution', code='POLICIES', is_required_for_registration=True,
                     allowed_extensions='pdf,doc,docx'),
        DocumentType(name='Executive Director CV', code='ED_CV', is_required_for_registration=True,
                     allowed_extensions='pdf,doc,docx'),
        DocumentType(name='Head of Programme CV', code='HOP_CV', is_required_for_registration=True,
                     allowed_extensions='pdf,doc,docx'),
        DocumentType(name='MoGEI Partner Coordination Acknowledgement', code='MOGEI_ACK',
                     is_required_for_registration=False, allowed_extensions='pdf,jpg,jpeg,png'),
        DocumentType(name='Annual Report', code='ANNUAL_RPT', is_required_for_registration=False,
                     allowed_extensions='pdf'),
        DocumentType(name='Financial Report', code='FIN_RPT', is_required_for_registration=False,
                     allowed_extensions='pdf'),
        DocumentType(name='Additional Licence', code='ADD_LIC', is_required_for_registration=False,
                     allowed_extensions='pdf,jpg,jpeg,png'),
    ]
    db.add_all(doc_types)

    # Application Statuses
    app_statuses = [
        ApplicationStatus(name='Draft', code='draft', sort_order=1),
        ApplicationStatus(name='Submitted', code='submitted', sort_order=2),
        ApplicationStatus(name='Under Review', code='under_review', sort_order=3),
        ApplicationStatus(name='Information Requested', code='info_requested', sort_order=4),
        ApplicationStatus(name='Approved', code='approved', sort_order=5, is_final=True),
        ApplicationStatus(name='Rejected', code='rejected', sort_order=6, is_final=True),
    ]
    db.add_all(app_statuses)

    # Membership Statuses
    mem_statuses = [
        MembershipStatus(name='Active', code='active'),
        MembershipStatus(name='Suspended', code='suspended'),
        MembershipStatus(name='Expired', code='expired'),
        MembershipStatus(name='Revoked', code='revoked'),
    ]
    db.add_all(mem_statuses)

    print("  - Roles, Sectors, States, Ministries created")
    print("  - Organisation Types, Registration Authorities created")
    print("  - Document Types, Application Statuses, Membership Statuses created")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='NDCI Database Setup')
    parser.add_argument('command', choices=['init', 'seed', 'admin', 'all'],
                        help='Command to run')

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
    elif args.command == 'seed':
        seed_db()
    elif args.command == 'admin':
        create_admin()
    elif args.command == 'all':
        init_db()
        seed_db()
        create_admin()
    else:
        parser.print_help()



