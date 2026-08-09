# config.py
# NDCI - National Development Consortium Initiative
# Flask Application Configuration

import hashlib
import json
import os
import stat
from datetime import datetime, timedelta, timezone
from flask import request
from flask_login import current_user
from flask_caching import Cache
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE DIRECTORY (defined once at the top)
# ============================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
TESTING = os.getenv('TESTING', 'False').lower() == 'true'

# WTF CSRF Configuration
WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True').lower() == 'true'
WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', SECRET_KEY)
WTF_CSRF_TIME_LIMIT = int(os.getenv('WTF_CSRF_TIME_LIMIT', 3600))  # 1 hour
WTF_CSRF_SSL_STRICT = os.getenv('WTF_CSRF_SSL_STRICT', 'True').lower() == 'true'

# Session configuration
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'ndci_session')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_LIFETIME_HOURS', 8)))
REMEMBER_COOKIE_DURATION = timedelta(days=int(os.getenv('REMEMBER_COOKIE_DAYS', 30)))
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'

# Flask-Login Configuration
LOGIN_DISABLED = os.getenv('LOGIN_DISABLED', 'False').lower() == 'true'
USE_SESSION_FOR_NEXT = True

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # 'sqlite' | 'mysql' | 'postgresql'

if DATABASE_TYPE == 'sqlite':
    # SQLite for local development and testing
    DB_NAME = os.getenv('SQLITE_DB_NAME', 'ndci.db')
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite doesn't use connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False  # Required for Flask's threaded mode
        }
    }

elif DATABASE_TYPE == 'postgresql':
    # PostgreSQL for production
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'ndci')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME', 'ndci')

    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 28000)),
        'pool_pre_ping': True
    }

else:  # mysql (default for production)
    # MySQL for production
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'ndci')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME', 'ndci')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+mysqldb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 28000)),
        'pool_pre_ping': True
    }

# ============================================================
# FILE UPLOAD CONFIGURATION
# ============================================================
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Create upload subdirectories
UPLOAD_SUBFOLDERS = {
    'documents': os.path.join(UPLOAD_FOLDER, 'documents'),
    'logos': os.path.join(UPLOAD_FOLDER, 'logos'),
    'programmes': os.path.join(UPLOAD_FOLDER, 'programmes'),
    'mous': os.path.join(UPLOAD_FOLDER, 'mous'),
    'training': os.path.join(UPLOAD_FOLDER, 'training'),
    'reports': os.path.join(UPLOAD_FOLDER, 'reports'),
    'temp': os.path.join(UPLOAD_FOLDER, 'temp')
}

# Ensure all upload directories exist with proper permissions
for folder_name, folder_path in UPLOAD_SUBFOLDERS.items():
    os.makedirs(folder_path, exist_ok=True)
    # Set directory permissions to 750 (owner rwx, group rx, others none)
    try:
        os.chmod(folder_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
    except (OSError, PermissionError):
        pass  # Permissions may not be settable on all platforms

# File upload limits
MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE_MB', 10)) * 1024 * 1024  # 10MB default
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# MIME type validation mapping
ALLOWED_MIME_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png'
}

# Document-specific limits (matches due diligence requirements)
DOCUMENT_MAX_SIZE_MB = int(os.getenv('DOCUMENT_MAX_SIZE_MB', 10))
LOGO_MAX_SIZE_MB = int(os.getenv('LOGO_MAX_SIZE_MB', 2))

# ============================================================
# SECURITY CONFIGURATION
# ============================================================

# Password policy
PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'True').lower() == 'true'
PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'True').lower() == 'true'
PASSWORD_REQUIRE_DIGITS = os.getenv('PASSWORD_REQUIRE_DIGITS', 'True').lower() == 'true'
PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'True').lower() == 'true'

# Rate Limiting (Flask-Limiter)
RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
RATELIMIT_STRATEGY = os.getenv('RATELIMIT_STRATEGY', 'fixed-window')
RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day;50 per hour')

# Specific rate limits
RATELIMIT_LOGIN = os.getenv('RATELIMIT_LOGIN', '5 per minute')
RATELIMIT_REGISTRATION = os.getenv('RATELIMIT_REGISTRATION', '3 per hour')
RATELIMIT_DOCUMENT_UPLOAD = os.getenv('RATELIMIT_DOCUMENT_UPLOAD', '20 per hour')
RATELIMIT_API = os.getenv('RATELIMIT_API', '100 per minute')

# ============================================================
# ROLE PERMISSIONS
# ============================================================
ROLE_PERMISSIONS = {
    'Super Admin': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': True,
        'can_approve': True,
        'can_administer': True
    },
    'NDCI Admin': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': True,
        'can_approve': True,
        'can_administer': True
    },
    'Board Member': {
        'can_view': True,
        'can_create': False,
        'can_edit': False,
        'can_delete': False,
        'can_approve': True,
        'can_administer': False
    },
    'Technical Expert': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    },
    'Ministry User': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    },
    'Regional Coordinator': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    },
    'NGO Admin': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    },
    'NGO User': {
        'can_view': True,
        'can_create': True,
        'can_edit': True,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    },
    'Donor Viewer': {
        'can_view': True,
        'can_create': False,
        'can_edit': False,
        'can_delete': False,
        'can_approve': False,
        'can_administer': False
    }
}

# ============================================================
# EMAIL CONFIGURATION
# ============================================================
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ndci.org')
MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'
MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', 100))
MAIL_ASCII_ATTACHMENTS = False

# ============================================================
# FLASK CACHING
# ============================================================
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # 'simple' | 'redis' | 'memcached'
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
CACHE_THRESHOLD = int(os.getenv('CACHE_THRESHOLD', 100))

if CACHE_TYPE == 'redis':
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    cache = Cache(config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': CACHE_REDIS_URL,
        'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
        'CACHE_KEY_PREFIX': 'ndci_cache_'
    })
else:
    cache = Cache(config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
        'CACHE_THRESHOLD': CACHE_THRESHOLD
    })


def make_cache_key():
    """
    Generate a cache key based on request args, path and current user.
    Used for view-level caching to differentiate between users.
    """
    args = {}
    if request:
        args = request.args.to_dict(flat=True)
        args['path'] = request.path
    args['user_id'] = getattr(current_user, "id", "anon")
    key = f"ndci_view:{hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()}"
    return key


# ============================================================
# APPLICATION CONSTANTS
# ============================================================
NDCI_NAME = 'National Development Consortium Initiative'
NDCI_SHORT_NAME = 'NDCI'
NDCI_COUNTRY = 'South Sudan'
NDCI_TIMEZONE = 'Africa/Juba'

# Application reference number format
REFERENCE_PREFIX = 'NDCI'
REFERENCE_YEAR = os.getenv('REFERENCE_YEAR', str(datetime.now(timezone.utc).year))

# Application statuses
APPLICATION_STATUS_DRAFT = 'draft'
APPLICATION_STATUS_SUBMITTED = 'submitted'
APPLICATION_STATUS_UNDER_REVIEW = 'under_review'
APPLICATION_STATUS_INFO_REQUESTED = 'info_requested'
APPLICATION_STATUS_APPROVED = 'approved'
APPLICATION_STATUS_REJECTED = 'rejected'

# Application status transitions (valid status changes)
APPLICATION_STATUS_TRANSITIONS = {
    APPLICATION_STATUS_DRAFT: [APPLICATION_STATUS_SUBMITTED],
    APPLICATION_STATUS_SUBMITTED: [APPLICATION_STATUS_UNDER_REVIEW],
    APPLICATION_STATUS_UNDER_REVIEW: [
        APPLICATION_STATUS_INFO_REQUESTED,
        APPLICATION_STATUS_APPROVED,
        APPLICATION_STATUS_REJECTED
    ],
    APPLICATION_STATUS_INFO_REQUESTED: [APPLICATION_STATUS_UNDER_REVIEW],
    APPLICATION_STATUS_APPROVED: [],  # Final state
    APPLICATION_STATUS_REJECTED: []    # Final state
}

# Membership statuses
MEMBERSHIP_STATUS_ACTIVE = 'active'
MEMBERSHIP_STATUS_SUSPENDED = 'suspended'
MEMBERSHIP_STATUS_EXPIRED = 'expired'
MEMBERSHIP_STATUS_REVOKED = 'revoked'

# Due diligence settings
DUE_DILIGENCE_REQUIRED_DOCS = [
    'Legal Registration Certificate',
    'Organisation Policies / Constitution',
    'Executive Director CV',
    'Head of Programme CV'
]

DUE_DILIGENCE_SCORE_THRESHOLD = float(os.getenv('DUE_DILIGENCE_SCORE_THRESHOLD', '0.7'))
DUE_DILIGENCE_PASSING_SCORE = float(os.getenv('DUE_DILIGENCE_PASSING_SCORE', '70.0'))

# Consortium coverage
NDCI_STATES_COUNT = 10
NDCI_ADMIN_AREAS_COUNT = 3
NDCI_LINE_MINISTRIES_COUNT = 6

# ============================================================
# PAGINATION
# ============================================================
ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
MAX_ITEMS_PER_PAGE = int(os.getenv('MAX_ITEMS_PER_PAGE', 100))

# ============================================================
# AUDIT LOGGING
# ============================================================
AUDIT_LOG_ENABLED = os.getenv('AUDIT_LOG_ENABLED', 'True').lower() == 'true'
AUDIT_LOG_ACTIONS = [
    'create',
    'update',
    'delete',
    'login',
    'logout',
    'login_failed',
    'approve',
    'reject',
    'submit',
    'upload',
    'download',
    'status_change'
]

# ============================================================
# FEATURE FLAGS
# ============================================================
ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'True').lower() == 'true'
ENABLE_SMS_NOTIFICATIONS = os.getenv('ENABLE_SMS_NOTIFICATIONS', 'False').lower() == 'true'
ENABLE_DOCUMENT_VERSIONING = os.getenv('ENABLE_DOCUMENT_VERSIONING', 'True').lower() == 'true'
ENABLE_DUE_DILIGENCE_WORKFLOW = os.getenv('ENABLE_DUE_DILIGENCE_WORKFLOW', 'True').lower() == 'true'
ENABLE_REGISTRATION = os.getenv('ENABLE_REGISTRATION', 'True').lower() == 'true'
ENABLE_PUBLIC_APPLICATION = os.getenv('ENABLE_PUBLIC_APPLICATION', 'True').lower() == 'true'

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
LOGGING_FORMAT = os.getenv(
    'LOGGING_FORMAT',
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGING_FILE = os.getenv('LOGGING_FILE', os.path.join(BASE_DIR, 'logs', 'ndci.log'))

# Ensure log directory exists
log_dir = os.path.dirname(LOGGING_FILE)
os.makedirs(log_dir, exist_ok=True)

# ============================================================
# EXTERNAL SERVICES (Optional)
# ============================================================

# Twilio (SMS notifications)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# WhatsApp Business API
WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

# S3 / DigitalOcean Spaces (Optional cloud storage)
CLOUD_STORAGE_ENABLED = os.getenv('CLOUD_STORAGE_ENABLED', 'False').lower() == 'true'
CLOUD_STORAGE_PROVIDER = os.getenv('CLOUD_STORAGE_PROVIDER', 's3')  # 's3' | 'digitalocean'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'ndci-documents')
AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # For DigitalOcean Spaces

# ============================================================
# FLASK-MIGRATE CONFIGURATION
# ============================================================
# These are set when Flask-Migrate is initialized, but defaults help
MIGRATIONS_DIR = os.path.join(BASE_DIR, 'migrations')

# ============================================================
# TIMEZONE HANDLING
# ============================================================
import pytz

# System timezone (UTC for storage)
SYSTEM_TIMEZONE = pytz.UTC

# Display timezone (for user-facing times)
DISPLAY_TIMEZONE = pytz.timezone(NDCI_TIMEZONE)


def utcnow():
    """Return current UTC datetime - use this for all database timestamps."""
    return datetime.now(pytz.UTC)


def to_display_timezone(dt):
    """Convert a UTC datetime to Africa/Juba for display."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(DISPLAY_TIMEZONE)
