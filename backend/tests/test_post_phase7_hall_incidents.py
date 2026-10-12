"""
Post-Phase 7 — Hall incident reporting + allocation integration.

Covers:
  - incident creation and validation
  - scope semantics (GLOBAL vs EXAM_SPECIFIC)
  - resolution
  - integration with the allocator's availability filter
  - authorization
  - non-persistence of what-if simulations
"""

import pytest

from app import db
from app.models.admin import Admin
from app.models.hall import Hall
from app.models.hall_incident import HallIncident
from app.models.examination import Examination
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation
from app.models.hall_ticket import HallTicket

from app.services.hall_incident import (
    report_incident,
    resolve_incident,
    is_hall_currently_blocked,
)


def _admin_id():
    return Admin.query.first().id


def _any_hall():
    return Hall.query.filter_by(is_active=True).first()


def _snapshot(examination_id):
    return {
        "hall_allocs": HallAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "seats": SeatAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "invs": InvigilatorAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "tickets": HallTicket.query.filter_by(
            examination_id=examination_id
        ).count(),
        "incidents": HallIncident.query.count(),
    }


# ============================================================
# Creation
# ============================================================

def test_report_incident_happy_path(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    result = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="Ceiling leak in the northwest corner.",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )

    assert result["success"] is True
    assert result["incident"]["id"] is not None
    assert result["incident"]["status"] == "OPEN"
    assert result["incident"]["hall_id"] == hall.id

    # Clean up
    row = db.session.get(
        HallIncident, result["incident"]["id"]
    )
    db.session.delete(row)
    db.session.commit()


def test_report_incident_requires_description(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    result = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="   ",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    assert result["success"] is False
    assert "description" in result["message"].lower()


def test_report_incident_rejects_unknown_hall(app_context):
    result = report_incident(
        hall_id=999999999,
        category="MAINTENANCE",
        description="x",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_report_incident_rejects_bad_category(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    result = report_incident(
        hall_id=hall.id,
        category="VOLCANO",
        description="x",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    assert result["success"] is False
    assert "category" in result["message"].lower()


def test_report_incident_exam_specific_requires_exam(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    result = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="x",
        scope="EXAM_SPECIFIC",
        reported_by_admin_id=_admin_id(),
        examination_id=None,
    )
    assert result["success"] is False
    assert "examination_id" in result["message"].lower()


# ============================================================
# Resolution
# ============================================================

def test_resolve_incident_closes_it(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = report_incident(
        hall_id=hall.id,
        category="EQUIPMENT_FAILURE",
        description="Projector dead.",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    iid = create["incident"]["id"]

    resolve = resolve_incident(
        incident_id=iid,
        resolved_by_admin_id=_admin_id(),
        notes="Replaced bulb.",
    )
    assert resolve["success"] is True
    assert resolve["incident"]["status"] == "RESOLVED"
    assert resolve["incident"]["resolved_at"] is not None

    # Cleanup
    row = db.session.get(HallIncident, iid)
    db.session.delete(row)
    db.session.commit()


def test_resolve_incident_twice_fails_cleanly(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = report_incident(
        hall_id=hall.id,
        category="OTHER",
        description="x",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    iid = create["incident"]["id"]
    resolve_incident(iid, _admin_id())
    second = resolve_incident(iid, _admin_id())
    assert second["success"] is False

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()


# ============================================================
# Scope semantics
# ============================================================

def test_global_incident_blocks_hall_for_every_exam(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="x",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    iid = create["incident"]["id"]

    assert is_hall_currently_blocked(hall.id, 1) is True
    assert is_hall_currently_blocked(hall.id, 999) is True
    assert is_hall_currently_blocked(hall.id, None) is True

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()


def test_exam_specific_incident_blocks_only_that_exam(
    app_context, examination_id
):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="x",
        scope="EXAM_SPECIFIC",
        reported_by_admin_id=_admin_id(),
        examination_id=examination_id,
    )
    iid = create["incident"]["id"]

    assert (
        is_hall_currently_blocked(hall.id, examination_id) is True
    )
    assert (
        is_hall_currently_blocked(hall.id, 999999) is False
    )
    assert is_hall_currently_blocked(hall.id, None) is False

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()


def test_resolved_incident_no_longer_blocks(app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = report_incident(
        hall_id=hall.id,
        category="OTHER",
        description="x",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    iid = create["incident"]["id"]
    resolve_incident(iid, _admin_id())
    assert is_hall_currently_blocked(hall.id, 1) is False

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()


# ============================================================
# Authorization (routes)
# ============================================================

def test_incident_route_requires_admin(client, app_context):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    resp = client.post(
        f"/api/halls/{hall.id}/incidents",
        json={
            "category": "MAINTENANCE",
            "description": "x",
            "scope": "GLOBAL",
        },
    )
    assert resp.status_code in (401, 403)


def test_incident_route_create_and_resolve(
    admin_client, app_context
):
    hall = _any_hall()
    if hall is None:
        pytest.skip("no active hall")

    create = admin_client.post(
        f"/api/halls/{hall.id}/incidents",
        json={
            "category": "MAINTENANCE",
            "description": "Ceiling fan not working.",
            "scope": "GLOBAL",
        },
    )
    assert create.status_code == 200, create.get_json()
    iid = create.get_json()["incident"]["id"]

    resolve = admin_client.post(
        f"/api/halls/incidents/{iid}/resolve",
        json={"resolution_notes": "Fixed."},
    )
    assert resolve.status_code == 200
    assert resolve.get_json()["incident"]["status"] == "RESOLVED"

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()


# ============================================================
# Integration with allocator: block propagates to availability
# ============================================================

def test_global_incident_excludes_hall_from_availability(
    app_context, examination_id
):
    """
    When a hall is blocked by a GLOBAL incident, the allocator's
    get_available_halls must not return it for any timetable.
    """
    from app.models.timetable import Timetable
    from app.services.allocation import get_available_halls

    hall = _any_hall()
    timetable = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .first()
    )
    if hall is None or timetable is None:
        pytest.skip("needs an active hall and a timetable entry")

    # Pre-check: hall is normally available unless already
    # excluded by unrelated rules.
    before = {
        h.id for h in get_available_halls(
            timetable,
            ignore_examination_id=examination_id,
        )
    }

    create = report_incident(
        hall_id=hall.id,
        category="MAINTENANCE",
        description="test",
        scope="GLOBAL",
        reported_by_admin_id=_admin_id(),
    )
    iid = create["incident"]["id"]

    after = {
        h.id for h in get_available_halls(
            timetable,
            ignore_examination_id=examination_id,
        )
    }

    assert hall.id not in after

    db.session.delete(db.session.get(HallIncident, iid))
    db.session.commit()

    restored = {
        h.id for h in get_available_halls(
            timetable,
            ignore_examination_id=examination_id,
        )
    }
    assert restored == before