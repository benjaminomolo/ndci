# utils/audit.py
# Audit logging utility

import logging
from flask import request, g
from flask_login import current_user
from models import AuditLog
from config import AUDIT_LOG_ENABLED

logger = logging.getLogger(__name__)


def log_audit_action(action, entity_type=None, entity_id=None, description=None):
    """Log an audit action if enabled"""
    if not AUDIT_LOG_ENABLED:
        return

    try:
        user_id = current_user.id if current_user.is_authenticated else None

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '') if request else ''
        )
        g.db.add(audit_log)
        g.db.commit()

        logger.debug(f"Audit: {action} - {entity_type}#{entity_id} - {description}")

    except Exception as e:
        g.db.rollback()
        logger.error(f"Audit log failed: {e}", exc_info=True)
