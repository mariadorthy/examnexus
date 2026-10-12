"""
Hall incident service.

All reads and writes for HallIncident go through this module
so the routes stay thin and the allocation layer has a single
integration point.
"""

from datetime import datetime

from app import db
from app.models.hall import Hall
from app.models.examination import Examination
from app.models.admin import Admin
from app.models.hall_incident import (
    HallIncident,
    CATEGORIES,
    SCOPES,
    STATUSES,
)


def _err(message, **extra):
    return {"success": False, "message": message, **extra}


def report_incident(
    hall_id,
    category,
    description,
    scope,
    reported_by_admin_id,
    examination_id=None,
):
    """
    Persist a new incident. Validates all inputs.

    - category must be in CATEGORIES
    - scope must be in SCOPES
    - description must be a non-empty string
    - examination_id is required when scope=EXAM_SPECIFIC
    - hall and admin must exist
    """
    hall = db.session.get(Hall, hall_id)
    if hall is None:
        return _err("Hall not found.")

    admin = db.session.get(Admin, reported_by_admin_id)
    if admin is None:
        return _err("Reporting admin not found.")

    if not isinstance(description, str) or not description.strip():
        return _err("Description is required.")

    category_norm = str(category or "").strip().upper()
    if category_norm not in CATEGORIES:
        return _err(
            f"Invalid category. Allowed: {sorted(CATEGORIES)}."
        )

    scope_norm = str(scope or "").strip().upper()
    if scope_norm not in SCOPES:
        return _err(f"Invalid scope. Allowed: {sorted(SCOPES)}.")

    if scope_norm == "EXAM_SPECIFIC":
        if examination_id is None:
            return _err(
                "examination_id is required when scope=EXAM_SPECIFIC."
            )
        exam = db.session.get(Examination, examination_id)
        if exam is None:
            return _err("Examination not found.")
    else:
        # GLOBAL scope must not carry an examination_id.
        examination_id = None

    try:
        incident = HallIncident(
            hall_id=hall.id,
            category=category_norm,
            description=description.strip(),
            scope=scope_norm,
            examination_id=examination_id,
            status="OPEN",
            reported_by_admin_id=admin.id,
        )
        db.session.add(incident)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return _err("Failed to record incident.", error=str(exc))

    return {
        "success": True,
        "message": "Incident recorded.",
        "incident": _serialize(incident),
    }


def resolve_incident(incident_id, resolved_by_admin_id, notes=None):
    """
    Mark an OPEN incident as RESOLVED.
    """
    incident = db.session.get(HallIncident, incident_id)
    if incident is None:
        return _err("Incident not found.")

    if incident.status == "RESOLVED":
        return _err(
            "Incident is already resolved.",
            incident=_serialize(incident),
        )

    admin = db.session.get(Admin, resolved_by_admin_id)
    if admin is None:
        return _err("Resolving admin not found.")

    try:
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by_admin_id = admin.id
        if notes is not None:
            incident.resolution_notes = str(notes).strip() or None
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return _err("Failed to resolve incident.", error=str(exc))

    return {
        "success": True,
        "message": "Incident resolved.",
        "incident": _serialize(incident),
    }


def active_incidents_for_hall(hall_id, examination_id=None):
    """
    Return OPEN incidents for a hall relevant to an
    examination:

      - GLOBAL incidents are always returned.
      - EXAM_SPECIFIC incidents are returned only when their
        examination_id matches the given examination_id.

    Pass examination_id=None to get only GLOBAL incidents.
    """
    query = HallIncident.query.filter(
        HallIncident.hall_id == hall_id,
        HallIncident.status == "OPEN",
    )

    if examination_id is None:
        query = query.filter(HallIncident.scope == "GLOBAL")
    else:
        query = query.filter(
            db.or_(
                HallIncident.scope == "GLOBAL",
                db.and_(
                    HallIncident.scope == "EXAM_SPECIFIC",
                    HallIncident.examination_id == examination_id,
                ),
            )
        )

    return query.all()


def is_hall_currently_blocked(hall_id, examination_id):
    """
    Convenience predicate used by the allocator's availability
    filter. True iff the hall has any active incident that
    applies to this examination.
    """
    return (
        HallIncident.query
        .filter(
            HallIncident.hall_id == hall_id,
            HallIncident.status == "OPEN",
            db.or_(
                HallIncident.scope == "GLOBAL",
                db.and_(
                    HallIncident.scope == "EXAM_SPECIFIC",
                    HallIncident.examination_id == examination_id,
                ),
            ),
        )
        .first()
        is not None
    )

def list_incidents(
    status=None,
    hall_id=None,
    examination_id=None,
):
    query = HallIncident.query

    if status:
        status_norm = str(status).strip().upper()
        if status_norm in STATUSES:
            query = query.filter(HallIncident.status == status_norm)

    if hall_id is not None:
        query = query.filter(HallIncident.hall_id == hall_id)

    # When examination_id is given, return only incidents that
    # apply to that examination: GLOBAL incidents always apply,
    # EXAM_SPECIFIC incidents only when their examination_id
    # matches. This mirrors active_incidents_for_hall().
    if examination_id is not None:
        query = query.filter(
            db.or_(
                HallIncident.scope == "GLOBAL",
                db.and_(
                    HallIncident.scope == "EXAM_SPECIFIC",
                    HallIncident.examination_id == examination_id,
                ),
            )
        )

    rows = query.order_by(HallIncident.reported_at.desc()).all()
    return [_serialize(r) for r in rows]

def _serialize(incident):
    return {
        "id": incident.id,
        "hall_id": incident.hall_id,
        "hall_name": incident.hall.name if incident.hall else None,
        "category": incident.category,
        "description": incident.description,
        "scope": incident.scope,
        "examination_id": incident.examination_id,
        "examination_name": (
            incident.examination.name
            if incident.examination
            else None
        ),
        "status": incident.status,
        "reported_by_admin_id": incident.reported_by_admin_id,
        "reported_at": (
            incident.reported_at.isoformat()
            if incident.reported_at
            else None
        ),
        "resolved_at": (
            incident.resolved_at.isoformat()
            if incident.resolved_at
            else None
        ),
        "resolved_by_admin_id": incident.resolved_by_admin_id,
        "resolution_notes": incident.resolution_notes,
    }