from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def record_event(
    db: Session,
    event_type: str,
    user_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(AuditLog(user_id=user_id, event_type=event_type, detail=detail, ip_address=ip_address))
    db.commit()
