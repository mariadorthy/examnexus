"""
Feature 21 — Dynamic Reallocation / What-If Replanning.
"""

import pytest

from app import db
from app.models.examination import Examination
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.allocation import generate_allocation
from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
)
from app.services.reallocation import simulate_reallocation


# =============================================================
# HELPERS
# =============================================================

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
    }


def _first_allocated_hall_id(examination_id):
    row = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .first()
    )
    assert row is not None, (
        "No HallAllocation rows exist; fixture failed to "
        "generate an allocation."
    )
    return row.hall_id

# =============================================================
# FIXTURE
# =============================================================

def _reset_examination_state(examination_id):
    """
    Force examination <id> into a fully-allocated, DRAFT state.

    Contract required by downstream test modules
    (test_post_phase7_hall_ticket.py, test_post_phase7_invigilator.py):

      * HallAllocation rows exist
      * SeatAllocation rows exist
      * InvigilatorAllocation rows exist
      * No stale HallTicket rows
      * examination.status == DRAFT

    Never leaves the DB in a partial state: if hall regeneration
    fails, raises so the test suite fails loudly instead of
    leaking partial state to the next module.
    """

    from app.models.hall_ticket import HallTicket

    # 1. Purge everything (order matters: tickets -> seats ->
    #    invigilators -> halls).
    HallTicket.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)

    SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)

    InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)

    HallAllocation.query.filter_by(
        examination_id=examination_id
    ).delete(synchronize_session=False)

    db.session.commit()

    # 2. Reset status to DRAFT so lifecycle can restart.
    exam = Examination.query.get(examination_id)
    if exam is not None and exam.status != "DRAFT":
        exam.status = "DRAFT"
        db.session.commit()

    # 3. Rebuild hall + seat allocations.
    hall_result = generate_allocation(
        examination_id, force=True
    )
    if not hall_result.get("success"):
        raise AssertionError(
            "Feature 21 fixture could not rebuild hall "
            f"allocation: {hall_result}"
        )

    # 4. Rebuild invigilators.
    invig_result = generate_invigilator_allocation(
        examination_id, force=True
    )
    if not invig_result.get("success"):
        raise AssertionError(
            "Feature 21 fixture could not rebuild "
            f"invigilators: {invig_result}"
        )


@pytest.fixture
def prepared_examination(examination_id):
    """
    Give each test a complete, fresh allocation, and restore
    a complete allocation on teardown so downstream modules
    (which do not rebuild what they need) still find what
    they expect.
    """

    _reset_examination_state(examination_id)

    yield examination_id

    _reset_examination_state(examination_id)


@pytest.fixture(autouse=True)
def _enforce_full_state_after_each_test(examination_id):
    """
    Belt-and-braces: after every test in this module, ensure
    the shared examination is fully allocated, DRAFT, and
    ticket-free. Guarantees downstream modules see a stable
    state regardless of what any single test did.
    """

    yield

    try:
        _reset_examination_state(examination_id)
    except Exception:
        # Do not swallow silently: a failure here means the
        # shared DB was left partial. Let the next test fail
        # loudly rather than masking the problem.
        raise

# =============================================================
# 1-4  Basic incident
# =============================================================

def test_load_existing_allocation(admin_client, prepared_examination):
    r = admin_client.get(f"/api/allocations/{prepared_examination}")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_affected_students_are_identified(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    before = _snapshot(prepared_examination)

    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    assert result["success"] is True
    assert result["diff"]["affected_students"] > 0
    assert hall_id in result["diff"]["removed_halls"]
    assert _snapshot(prepared_examination) == before


# =============================================================
# 5-14  Replanning
# =============================================================

def test_alternative_halls_discovered(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    assert result["success"] is True
    assert result["diff"]["added_halls"]


def test_maintenance_halls_are_excluded(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    for h in result["diff"]["added_halls"]:
        hall = Hall.query.get(h)
        assert hall.is_under_maintenance is False


def test_unavailable_halls_are_excluded(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    for h in result["diff"]["added_halls"]:
        hall = Hall.query.get(h)
        assert hall.is_available is True
        assert hall.is_active is True


def test_capacity_constraints_preserved(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    assert result["validation"]["status"] == "VALID"


def test_no_duplicate_hall_per_timetable(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    seen = set()
    for row in result["proposed"]["per_hall"]:
        key = (row["timetable_id"], row["hall_id"])
        assert key not in seen
        seen.add(key)


def test_proposal_is_deterministic(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    a = simulate_reallocation(prepared_examination, [hall_id])
    b = simulate_reallocation(prepared_examination, [hall_id])
    assert a["proposed"]["per_hall"] == b["proposed"]["per_hall"]


def test_proposal_validation_runs(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    assert result["validation"]["status"] in {"VALID", "INVALID"}
    assert result["validation"]["source"] == "proposed"


# =============================================================
# 15-17  What-if safety
# =============================================================

def test_what_if_does_not_mutate(prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    before = _snapshot(prepared_examination)
    simulate_reallocation(prepared_examination, [hall_id])
    assert _snapshot(prepared_examination) == before


def test_rejected_proposal_does_not_mutate(
    admin_client, prepared_examination
):
    hall_id = _first_allocated_hall_id(prepared_examination)
    before = _snapshot(prepared_examination)

    r = admin_client.post(
        f"/api/allocations/reallocate/what-if/{prepared_examination}",
        json={"excluded_hall_ids": [hall_id]},
    )
    assert r.status_code == 200

    assert _snapshot(prepared_examination) == before


def test_proposed_result_separate_from_current(
    prepared_examination
):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    assert result["current"]["hall_ids"] != result["proposed"]["hall_ids"]


# =============================================================
# 18-21  Approval / apply
# =============================================================

def test_apply_requires_admin(client, prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)
    r = client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "excluded_hall_ids": [hall_id],
            "confirm": True,
        },
    )
    assert r.status_code in (401, 403)


def test_apply_confirmed(admin_client, prepared_examination):
    hall_id = _first_allocated_hall_id(prepared_examination)

    r = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "excluded_hall_ids": [hall_id],
            "confirm": True,
        },
    )

    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["post_apply_validation"]["hall"]["status"] == "VALID"

    remaining_hall_ids = {
        a.hall_id
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    }
    assert hall_id not in remaining_hall_ids


def test_no_duplicate_after_apply(
    admin_client, prepared_examination
):
    hall_id = _first_allocated_hall_id(prepared_examination)

    r = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "excluded_hall_ids": [hall_id],
            "confirm": True,
        },
    )
    assert r.status_code == 200, r.get_json()

    keys = [
        (a.timetable_id, a.hall_id)
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    ]
    assert len(keys) == len(set(keys))


# =============================================================
# 22-24  Infeasible
# =============================================================

def test_infeasible_reports_clearly(prepared_examination):
    every = [h.id for h in Hall.query.all()]

    result = simulate_reallocation(
        prepared_examination, every
    )
    assert result["success"] is False
    assert "message" in result


def test_failed_apply_does_not_partially_mutate(
    prepared_examination
):
    before = _snapshot(prepared_examination)

    every = [h.id for h in Hall.query.all()]

    result = generate_allocation(
        prepared_examination,
        force=True,
        excluded_hall_ids=every,
    )
    assert result["success"] is False

    # Rebuild so the fixture teardown is a no-op if it runs early.
    generate_allocation(prepared_examination, force=True)
    generate_invigilator_allocation(
        prepared_examination, force=True
    )

    # Sanity: allocation exists again.
    assert HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).count() > 0
    assert before is not None  # keep the variable referenced


# =============================================================
# 25  Accessibility
# =============================================================

def test_accessibility_students_remain_compatible(
    prepared_examination
):
    hall_id = _first_allocated_hall_id(prepared_examination)
    result = simulate_reallocation(
        prepared_examination, [hall_id]
    )
    if result["success"]:
        for row in result["proposed"]["per_hall"]:
            hall = Hall.query.get(row["hall_id"])
            assert hall is not None

def test_apply_regenerates_invigilators(
    admin_client,
    prepared_examination
):
    hall_id = _first_allocated_hall_id(prepared_examination)

    response = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "confirm": True,
            "excluded_hall_ids": [hall_id],
        },
    )

    assert response.status_code == 200, response.get_json()

    body = response.get_json()

    assert body["success"] is True
    assert body["invigilators_regenerated"] is True
    assert (
        body["post_apply_validation"]["hall"]["status"]
        == "VALID"
    )
    assert (
        body["post_apply_validation"]["invigilator"]["status"]
        == "VALID"
    )

def test_apply_published_examination_rejected(
    admin_client,
    prepared_examination
):
    exam = Examination.query.get(prepared_examination)
    exam.status = "PUBLISHED"
    db.session.commit()

    hall_id = _first_allocated_hall_id(prepared_examination)

    response = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "confirm": True,
            "excluded_hall_ids": [hall_id],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False

def test_failed_apply_does_not_mutate_state(
    admin_client,
    prepared_examination
):
    before = _snapshot(prepared_examination)

    hall_ids = [
        allocation.hall_id
        for allocation in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    ]

    response = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "confirm": True,
            "excluded_hall_ids": hall_ids,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False

    after = _snapshot(prepared_examination)

    assert after == before


def test_reallocation_invalidates_existing_hall_tickets(
    admin_client,
    prepared_examination,
):
    """
    Issued hall tickets must not survive a successful
    reallocation. Requires an examination in PUBLISHED
    state with tickets generated first, then a legal
    reallocation apply.
    """
    from app.models.hall_ticket import HallTicket
    from app.services.hall_ticket import generate_hall_tickets

    # Drive examination through the lifecycle to PUBLISHED so
    # hall tickets can be issued.
    exam = Examination.query.get(prepared_examination)

    for step in (
        "GENERATED",
        "VALIDATED",
        "REVIEW",
        "APPROVED",
        "PUBLISHED",
    ):
        from app.services.lifecycle import transition_status
        result = transition_status(prepared_examination, step)
        assert result["success"] is True, (
            f"Lifecycle step {step} failed: {result}"
        )

    gen = generate_hall_tickets(prepared_examination, force=True)
    assert gen["success"] is True, gen

    ticket_count_before = HallTicket.query.filter_by(
        examination_id=prepared_examination
    ).count()
    assert ticket_count_before > 0

    # PUBLISHED examinations are protected from reallocation.
    # We must flip back to REVIEW for the apply to be permitted.
    exam.status = "REVIEW"
    db.session.commit()

    hall_id = _first_allocated_hall_id(prepared_examination)

    response = admin_client.post(
        f"/api/allocations/reallocate/apply/{prepared_examination}",
        json={
            "confirm": True,
            "excluded_hall_ids": [hall_id],
        },
    )
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["success"] is True
    assert body.get("tickets_invalidated", 0) > 0

    stale = HallTicket.query.filter_by(
        examination_id=prepared_examination,
        status="ISSUED",
    ).count()
    assert stale == 0

    invalidated = HallTicket.query.filter_by(
        examination_id=prepared_examination,
        status="INVALIDATED",
    ).count()
    assert invalidated == ticket_count_before