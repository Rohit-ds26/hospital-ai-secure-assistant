import logging

from models import AuditLog


def log_audit(db, actor, action, resource, details="", success=True):
    """Log every sensitive action for audit trail."""

    try:
        log = AuditLog(
            username=actor.username,
            role=actor.role,
            action=action,
            resource=resource,
            success=success,
            details=details,
        )

        db.add(log)
        db.commit()
    except Exception as exc:
        db.rollback()
        logging.warning("Audit log write failed: %s", exc)
