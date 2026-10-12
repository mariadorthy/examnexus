"""
Post-Phase 7 — Emergency reallocation on published examinations.

Covers the emergency workflow built on top of the existing
reallocation planner. The ordinary what-if paths remain
untouched and are regression-guarded here.
"""

import pytest

from datetime import date, timedelta

from app import db
from app.models.examination import Examination
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation
from app.models.hall_ticket import HallTicket
from app.models.admin import Admin
from app.models.hall_incident import HallIncident

from app.services.hall_ticket import (
    generate_hall_tickets,
    verify_hall_ticket,
    supersede_hall_tickets,
)
from app.services.reallocation import (
    simulate_reallocation,
    simulate_emergency_reallocation,
    apply_emergency_reallocation,
)


# ============================================================
# Helpers
# ============================================================

def _admin_id():
    return Admin.query.first().id


def _force_published(examination):
    examination.status = "PUBLISHED"
    db.session.commit()


def _make_incident(examination_id, scope="EXAM_SPECIFIC"):
    return HallIncident(
        hall_id=Hall.query.first().id,
        category="MAINTENANCE",
        description="Test incident for emergency reallocation.",
        scope=scope,
        examination_id=examination_id if scope == "EXAM_SPECIFIC" else None,
        status="OPEN",
        reported_by_admin_id=_admin_id(),
    )


def _cleanup_incidents():
    HallIncident.query.delete(synchronize_session=False)
    db.session.commit()


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
    }

def _first_allocation_or_skip(examination_id):
    row = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .first()
    )
    if row is None:
        pytest.skip(
            "no hall allocation for this examination — "
            "run allocation first"
        )
    return row


def _prepare_allocation_or_skip(examination_id):
    """
    Ensure examination <id> has a fresh hall + invigilator
    allocation. The Feature 21 test module wipes and rebuilds
    allocations during its own tests, so we cannot assume any
    pre-existing state. Regenerate if necessary.
    """
    from app.services.allocation import generate_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )

    hall_existing = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).count()

    if hall_existing == 0:
        result = generate_allocation(examination_id, force=True)
        if not result.get("success"):
            pytest.skip(
                f"cannot rebuild hall allocation: {result.get('message')}"
            )

    inv_existing = InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).count()

    if inv_existing == 0:
        result = generate_invigilator_allocation(
            examination_id, force=True
        )
        if not result.get("success"):
            pytest.skip(
                f"cannot rebuild invigilators: {result.get('message')}"
            )


def _pick_feasible_excluded_hall(examination_id):
    """
    Return a hall id from the current allocation whose exclusion
    the planner can still satisfy — or pytest.skip if no such
    hall exists.

    The seed data has limited accessible-hall capacity; excluding
    the wrong hall triggers the planner's accessibility guard.
    Trying each hall in turn and using the first one that yields
    a successful emergency simulation is deterministic and cheap.
    """
    from app.services.reallocation import (
        simulate_emergency_reallocation,
    )

    # Need an OPEN incident to run a simulation. Create a
    # throwaway one, try each hall, then clean up.
    from app.models.hall_incident import HallIncident
    from app.models.admin import Admin

    admin = Admin.query.first()
    if admin is None:
        pytest.skip("no admin user present")

    hall_ids = sorted({
        row.hall_id
        for row in HallAllocation.query.filter_by(
            examination_id=examination_id
        ).all()
    })

    if not hall_ids:
        pytest.skip("no allocated halls to choose from")

    # Use a GLOBAL-scope incident so it does not depend on
    # examination_id matching.
    probe = HallIncident(
        hall_id=hall_ids[0],
        category="MAINTENANCE",
        description="(probe) feasibility check",
        scope="GLOBAL",
        status="OPEN",
        reported_by_admin_id=admin.id,
    )
    db.session.add(probe)
    db.session.commit()

    try:
        for hall_id in hall_ids:
            result = simulate_emergency_reallocation(
                examination_id,
                excluded_hall_ids=[hall_id],
                incident_id=probe.id,
            )
            if result.get("success"):
                return hall_id
    finally:
        HallIncident.query.filter_by(id=probe.id).delete(
            synchronize_session=False
        )
        db.session.commit()

    pytest.skip(
        "no single-hall exclusion in the seed data yields a "
        "feasible emergency replan (likely accessible-capacity "
        "constraint)"
    )

# ============================================================
# 1. Normal what-if still refuses PUBLISHED (regression)
# ============================================================

def test_normal_what_if_still_refuses_published(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status

    _prepare_allocation_or_skip(examination_id)

    try:
        _force_published(exam)
        hall_id = _first_allocation_or_skip(examination_id).hall_id

        result = simulate_reallocation(examination_id, [hall_id])

        assert result["success"] is False
        assert "PUBLISHED" in result["message"]
    finally:
        exam.status = original_status
        db.session.commit()


# ============================================================
# 2. Emergency simulate does not mutate persistent state
# ============================================================
def test_emergency_simulate_does_not_mutate(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status

    _prepare_allocation_or_skip(examination_id)
    _cleanup_incidents()

    try:
        _force_published(exam)

        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        # Try each allocated hall until the planner accepts the
        # exclusion. The mutation check runs against the same
        # call, so feasibility and non-mutation are proven on
        # exactly the state the planner saw.
        hall_ids = sorted({
            row.hall_id
            for row in HallAllocation.query.filter_by(
                examination_id=examination_id
            ).all()
        })
        if not hall_ids:
            pytest.skip("no allocated halls")

        before = _snapshot(examination_id)

        result = None
        for candidate in hall_ids:
            result = simulate_emergency_reallocation(
                examination_id,
                excluded_hall_ids=[candidate],
                incident_id=incident.id,
            )
            if result.get("success"):
                break

        if result is None or not result.get("success"):
            pytest.skip(
                "no single-hall exclusion in the seed data yields "
                "a feasible emergency replan"
            )

        assert result["emergency"] is True
        assert _snapshot(examination_id) == before

    finally:
        exam.status = original_status
        db.session.commit()
        _cleanup_incidents()

# ============================================================
# 3. Emergency simulate requires an OPEN matching incident
# ============================================================

def test_emergency_simulate_requires_incident_id(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status

    try:
        _force_published(exam)

        hall_id = _pick_feasible_excluded_hall(examination_id)
        result = simulate_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=None,
        )

        assert result["success"] is False
        assert "incident_id" in result["message"]
    finally:
        exam.status = original_status
        db.session.commit()


# ============================================================
# 4. Emergency apply on NOT_STARTED published exam
# ============================================================

def test_emergency_apply_on_not_started_published(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status
    original_start = exam.start_date
    original_end = exam.end_date

    _prepare_allocation_or_skip(examination_id)
    _cleanup_incidents()

    try:
        # Force the examination window to be in the future so
        # the in-progress rule classifies it NOT_STARTED.
        exam.start_date = date.today() + timedelta(days=30)
        exam.end_date = date.today() + timedelta(days=45)
        _force_published(exam)

        # Give the examination a set of tickets at version 1.
        gen = generate_hall_tickets(examination_id, force=True)
        assert gen["success"] is True, gen
        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        hall_id = _pick_feasible_excluded_hall(examination_id)

        result = apply_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=incident.id,
        )

        assert result["success"] is True, result
        assert result["emergency"] is True
        assert result["in_progress_state"] == "NOT_STARTED"
        assert result["tickets_superseded"] > 0
        assert result["tickets_issued"] > 0

        # Every student should have exactly one ISSUED ticket at
        # version 2, plus any SUPERSEDED version-1 rows.
        issued = HallTicket.query.filter_by(
            examination_id=examination_id,
            status="ISSUED",
        ).all()
        assert all(t.version == 2 for t in issued)
        assert len(issued) == result["tickets_issued"]

        superseded = HallTicket.query.filter_by(
            examination_id=examination_id,
            status="SUPERSEDED",
        ).count()
        assert superseded == result["tickets_superseded"]

        # Examination status must be unchanged.
        db.session.refresh(exam)
        assert exam.status == "PUBLISHED"

    finally:
        exam.status = original_status
        exam.start_date = original_start
        exam.end_date = original_end
        db.session.commit()
        _cleanup_incidents()


# ============================================================
# 5. QR verification distinguishes current and superseded
# ============================================================

def test_verify_superseded_ticket_returns_superseded_status(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status
    original_start = exam.start_date
    original_end = exam.end_date

    _prepare_allocation_or_skip(examination_id)
    _cleanup_incidents()

    try:
        exam.start_date = date.today() + timedelta(days=30)
        exam.end_date = date.today() + timedelta(days=45)
        _force_published(exam)

        gen = generate_hall_tickets(examination_id, force=True)
        assert gen["success"] is True, gen

        # Capture one v1 token before reallocation.
        v1_ticket = (
            HallTicket.query
            .filter_by(examination_id=examination_id, version=1)
            .first()
        )
        v1_token = v1_ticket.verification_token
        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        hall_id = _pick_feasible_excluded_hall(examination_id)
        apply_result = apply_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=incident.id,
        )
        assert apply_result["success"] is True, apply_result

        # Old token now reports SUPERSEDED, not valid, not "not found".
        old_result = verify_hall_ticket(v1_token)
        assert old_result["valid"] is False
        assert old_result["status"] == "SUPERSEDED"
        assert "superseded" in old_result["message"].lower()

        # New token verifies as valid.
        v2_ticket = (
            HallTicket.query
            .filter_by(
                examination_id=examination_id,
                student_id=v1_ticket.student_id,
                version=2,
            )
            .first()
        )
        assert v2_ticket is not None
        new_result = verify_hall_ticket(v2_ticket.verification_token)
        assert new_result["valid"] is True
        assert new_result["status"] == "ISSUED"

    finally:
        exam.status = original_status
        exam.start_date = original_start
        exam.end_date = original_end
        db.session.commit()
        _cleanup_incidents()


# ============================================================
# 6. In-progress published exam requires acknowledgement
# ============================================================

def test_emergency_apply_in_progress_requires_acknowledgement(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status
    original_start = exam.start_date
    original_end = exam.end_date

    _prepare_allocation_or_skip(examination_id)
    _cleanup_incidents()

    try:
        # Force today to fall inside the examination window.
        exam.start_date = date.today() - timedelta(days=1)
        exam.end_date = date.today() + timedelta(days=1)
        _force_published(exam)

        gen = generate_hall_tickets(examination_id, force=True)
        assert gen["success"] is True, gen

        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        hall_id = _pick_feasible_excluded_hall(examination_id)

        # Without acknowledgement: refused.
        refused = apply_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=incident.id,
            acknowledge_in_progress=False,
        )
        assert refused["success"] is False
        assert "acknowledge_in_progress" in refused["message"]
        assert refused["in_progress_state"] == "IN_PROGRESS"

        # With acknowledgement: proceeds.
        accepted = apply_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=incident.id,
            acknowledge_in_progress=True,
        )
        assert accepted["success"] is True, accepted

    finally:
        exam.status = original_status
        exam.start_date = original_start
        exam.end_date = original_end
        db.session.commit()
        _cleanup_incidents()


# ============================================================
# 7. Emergency simulate refuses ENDED examinations
# ============================================================

def test_emergency_simulate_refuses_ended_examination(
    app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status
    original_start = exam.start_date
    original_end = exam.end_date

    _cleanup_incidents()

    try:
        exam.start_date = date.today() - timedelta(days=45)
        exam.end_date = date.today() - timedelta(days=30)
        _force_published(exam)

        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        hall_id = _first_allocation_or_skip(examination_id).hall_id

        result = simulate_emergency_reallocation(
            examination_id,
            excluded_hall_ids=[hall_id],
            incident_id=incident.id,
        )
        assert result["success"] is False
        assert "ended" in result["message"].lower()

    finally:
        exam.status = original_status
        exam.start_date = original_start
        exam.end_date = original_end
        db.session.commit()
        _cleanup_incidents()


# ============================================================
# 8. Authorization
# ============================================================

def test_emergency_routes_require_admin(client, examination_id):
    allocation = _first_allocation_or_skip(examination_id)

    body = {
        "incident_id": 1,
        "excluded_hall_ids": [allocation.hall_id],
    }
    r1 = client.post(
        f"/api/allocations/reallocate/emergency/what-if/"
        f"{examination_id}",
        json=body,
    )
    assert r1.status_code in (401, 403)

    r2 = client.post(
        f"/api/allocations/reallocate/emergency/apply/"
        f"{examination_id}",
        json={**body, "confirm": True},
    )
    assert r2.status_code in (401, 403)


# ============================================================
# 9. Route-level apply happy path
# ============================================================

def test_emergency_apply_route_happy_path(
    admin_client, app_context, examination_id
):
    exam = db.session.get(Examination, examination_id)
    original_status = exam.status
    original_start = exam.start_date
    original_end = exam.end_date
    _prepare_allocation_or_skip(examination_id)
    _cleanup_incidents()

    try:
        exam.start_date = date.today() + timedelta(days=30)
        exam.end_date = date.today() + timedelta(days=45)
        _force_published(exam)

        gen = generate_hall_tickets(examination_id, force=True)
        assert gen["success"] is True, gen

        incident = _make_incident(examination_id)
        db.session.add(incident)
        db.session.commit()

        hall_id = _pick_feasible_excluded_hall(examination_id)

        resp = admin_client.post(
            f"/api/allocations/reallocate/emergency/apply/"
            f"{examination_id}",
            json={
                "incident_id": incident.id,
                "excluded_hall_ids": [hall_id],
                "confirm": True,
            },
        )
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()
        assert body["success"] is True
        assert body["emergency"] is True

    finally:
        exam.status = original_status
        exam.start_date = original_start
        exam.end_date = original_end
        db.session.commit()
        _cleanup_incidents()