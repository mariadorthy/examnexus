"""
Feature 20 — Explainable Allocation.

Self-contained module. Mirrors the fixture pattern used by
test_phase10_dynamic_reallocation.py (local helper + local
fixture + local autouse teardown). Does NOT rely on any
module-local fixture from another test file.

Verifies that explanations come from the real allocation
engine, are deterministic, and never invent reasons.
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
from app.services.explanation import (
    REASON_CODES,
    explain_allocation,
    explain_hall_decision,
)


# =============================================================
# LOCAL HELPERS (mirrors test_phase10)
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


def _reset_examination_state(examination_id):
    """
    Force examination <id> into a fully-allocated, DRAFT state.

    Identical contract to the Feature 21 module. Rebuilt here
    rather than imported so this module stays self-contained.
    """
    from app.models.hall_ticket import HallTicket

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

    exam = Examination.query.get(examination_id)
    if exam is not None and exam.status != "DRAFT":
        exam.status = "DRAFT"
        db.session.commit()

    hall_result = generate_allocation(examination_id, force=True)
    if not hall_result.get("success"):
        raise AssertionError(
            "Feature 20 fixture could not rebuild hall "
            f"allocation: {hall_result}"
        )

    invig_result = generate_invigilator_allocation(
        examination_id, force=True
    )
    if not invig_result.get("success"):
        raise AssertionError(
            "Feature 20 fixture could not rebuild "
            f"invigilators: {invig_result}"
        )


# =============================================================
# LOCAL FIXTURES
# =============================================================

@pytest.fixture
def prepared_examination(examination_id):
    _reset_examination_state(examination_id)
    yield examination_id
    _reset_examination_state(examination_id)


@pytest.fixture(autouse=True)
def _enforce_full_state_after_each_test(examination_id):
    yield
    try:
        _reset_examination_state(examination_id)
    except Exception:
        raise


# =============================================================
# SELECTED explanations
# =============================================================

def test_selected_hall_explained(admin_client, prepared_examination):
    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()
    assert row is not None, (
        "Fixture did not produce a HallAllocation row"
    )

    r = admin_client.get(
        f"/api/allocations/explain/{prepared_examination}/hall/"
        f"{row.hall_id}?timetable_id={row.timetable_id}"
    )
    assert r.status_code == 200, r.get_json()

    body = r.get_json()
    assert body["decision"] == "SELECTED"

    codes = {reason["code"] for reason in body["reasons"]}
    assert "HALL_ACTIVE" in codes
    assert "HALL_AVAILABLE" in codes
    assert "NOT_UNDER_MAINTENANCE" in codes
    assert "HAS_EXAM_CAPACITY" in codes
    assert "NO_TIMETABLE_CONFLICT" in codes


def test_capacity_reason_present(admin_client, prepared_examination):
    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()
    r = admin_client.get(
        f"/api/allocations/explain/{prepared_examination}/hall/"
        f"{row.hall_id}?timetable_id={row.timetable_id}"
    )
    assert r.status_code == 200
    codes = {x["code"] for x in r.get_json()["reasons"]}
    assert "HAS_EXAM_CAPACITY" in codes

def test_allocator_strategy_reason_present(admin_client, prepared_examination):
    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()
    r = admin_client.get(
        f"/api/allocations/explain/{prepared_examination}/hall/"
        f"{row.hall_id}?timetable_id={row.timetable_id}"
    )
    assert r.status_code == 200
    codes = {x["code"] for x in r.get_json()["reasons"]}
    assert "SELECTED_BY_ALLOCATOR_STRATEGY" in codes
    assert "SELECTED_BY_MINIMIZATION" not in codes

def test_purpose_reason_present(admin_client, prepared_examination):
    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()
    r = admin_client.get(
        f"/api/allocations/explain/{prepared_examination}/hall/"
        f"{row.hall_id}?timetable_id={row.timetable_id}"
    )
    assert r.status_code == 200
    codes = {x["code"] for x in r.get_json()["reasons"]}
    assert any(c.startswith("PURPOSE_") for c in codes)


# =============================================================
# REJECTED explanations
# =============================================================

def test_rejected_hall_explained(admin_client, prepared_examination):
    allocated_ids = {
        a.hall_id
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    }
    rejected = Hall.query.filter(
        ~Hall.id.in_(allocated_ids)
    ).first()

    if rejected is None:
        pytest.skip(
            "Every hall is currently allocated; "
            "no rejected hall to assert against."
        )

    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()

    r = admin_client.get(
        f"/api/allocations/explain/{prepared_examination}/hall/"
        f"{rejected.id}?timetable_id={row.timetable_id}"
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["decision"] == "REJECTED"
    assert body["reasons"]


def test_maintenance_reason_is_not_reported_for_healthy_hall(
    prepared_examination,
):
    """
    Flip a currently-selected hall to under_maintenance and
    verify the SELECTED explanation no longer claims
    NOT_UNDER_MAINTENANCE. Restore afterwards.
    """
    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()
    hall = Hall.query.get(row.hall_id)
    assert hall is not None

    original = hall.is_under_maintenance
    hall.is_under_maintenance = True
    db.session.commit()

    try:
        result = explain_hall_decision(
            prepared_examination,
            hall.id,
            row.timetable_id,
        )
        codes = {r["code"] for r in result["reasons"]}
        assert "NOT_UNDER_MAINTENANCE" not in codes
    finally:
        hall.is_under_maintenance = original
        db.session.commit()


def test_unavailable_reason_is_reported(prepared_examination):
    allocated_ids = {
        a.hall_id
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    }
    candidate = Hall.query.filter(~Hall.id.in_(allocated_ids)).first()

    if candidate is None:
        pytest.skip(
            "Every hall is currently allocated; "
            "no rejected candidate to flip unavailable."
        )

    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()

    original = candidate.is_available
    candidate.is_available = False
    db.session.commit()

    try:
        result = explain_hall_decision(
            prepared_examination,
            candidate.id,
            row.timetable_id,
        )
        codes = {r["code"] for r in result["reasons"]}
        assert "REJECTED_UNAVAILABLE" in codes
    finally:
        candidate.is_available = original
        db.session.commit()


# =============================================================
# Determinism & closed enum
# =============================================================

def test_explanation_is_deterministic(prepared_examination):
    a = explain_allocation(prepared_examination)
    b = explain_allocation(prepared_examination)
    assert a["selected"] == b["selected"]
    assert a["rejected"] == b["rejected"]
    assert a["aggregate"] == b["aggregate"]


def test_all_reason_codes_are_declared(prepared_examination):
    result = explain_allocation(prepared_examination)
    assert result["success"] is True
    seen = set()
    for group in ("selected", "rejected", "aggregate"):
        for row in result[group]:
            for reason in row["reasons"]:
                seen.add(reason["code"])
    assert seen.issubset(REASON_CODES), (
        f"Undeclared reason code(s): {seen - REASON_CODES}"
    )


def test_explanation_matches_actual_allocation(prepared_examination):
    result = explain_allocation(prepared_examination)
    assert result["success"] is True

    persisted = {
        (a.timetable_id, a.hall_id)
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    }
    explained = {
        (row["timetable_id"], row["hall_id"])
        for row in result["selected"]
    }
    assert persisted == explained


def test_explanation_does_not_invent_reasons(prepared_examination):
    result = explain_allocation(prepared_examination)
    for group in ("selected", "rejected", "aggregate"):
        for row in result[group]:
            for reason in row["reasons"]:
                assert reason["code"] in REASON_CODES
                assert isinstance(reason["message"], str)
                assert reason["message"].strip()


# =============================================================
# Feature 21 integration
# =============================================================

def test_feature21_explanations_still_present(prepared_examination):
    hall_id = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first().hall_id

    result = simulate_reallocation(prepared_examination, [hall_id])
    assert result["success"] is True
    assert "explanations" in result
    assert isinstance(result["explanations"], list)

def test_no_mutation_from_explanation(prepared_examination):
    before = _snapshot(prepared_examination)
    explain_allocation(prepared_examination)
    after = _snapshot(prepared_examination)
    assert after == before

# =============================================================
# Transient exclusion (Feature 21 alignment)
# =============================================================

def test_transient_exclusion_code_is_declared(prepared_examination):
    """
    REJECTED_TRANSIENTLY_EXCLUDED must belong to the closed
    REASON_CODES enum. Guards against the enum drifting out
    of sync with the emitter.
    """
    assert "REJECTED_TRANSIENTLY_EXCLUDED" in REASON_CODES


def test_transient_exclusion_is_reported(prepared_examination):
    """
    When a hall is passed via excluded_hall_ids and is not
    currently selected for a given timetable, the explanation
    must report REJECTED_TRANSIENTLY_EXCLUDED.
    """
    allocated_ids = {
        a.hall_id
        for a in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    }
    candidate = Hall.query.filter(~Hall.id.in_(allocated_ids)).first()

    if candidate is None:
        pytest.skip(
            "Every hall is currently allocated; "
            "no rejected candidate to exclude."
        )

    row = HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).first()

    result = explain_hall_decision(
        prepared_examination,
        candidate.id,
        row.timetable_id,
        excluded_hall_ids=[candidate.id],
    )
    codes = {r["code"] for r in result["reasons"]}
    assert "REJECTED_TRANSIENTLY_EXCLUDED" in codes
    assert codes.issubset(REASON_CODES)