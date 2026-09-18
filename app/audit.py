from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .models import AuditLog


def record_audit(
    session: Session,
    *,
    actor: str,
    action: str,
    object_type: str,
    object_id: str,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=object_id,
        details_json=json.dumps(details, sort_keys=True) if details else None,
    )
    session.add(entry)
    session.commit()
    return entry
