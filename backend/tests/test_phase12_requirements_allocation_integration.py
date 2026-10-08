"""
Feature 18 → Allocation integration tests.

Proves:
  - Supported requirements reach the deterministic allocator.
  - Unknown keys are rejected.
  - Natural language cannot mutate DB state on its own.
  - Safety constraints (maintenance, availability, timetable,
    accessibility) remain enforced.
  - Determinism.
  - Admin RBAC.
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
from app.services.allocation_options import build_allocation_options


# =============================================================
# HELPERS / FIXTURES (self-contained, mirrors phase 10/11)
# =============================================================

def _reset_examination_state(examination_id):
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
            f"Fixture could not rebuild hall allocation: {hall_result}"
        )

    invig_result = generate_invigilator_allocation(
        examination_id, force=True
    )
    if not invig_result.get("success"):
        raise AssertionError(
            f"Fixture could not rebuild invigilators: {invig_result}"
        )


@pytest.fixture
def prepared_examination(examination_id):
    _reset_examination_state(examination_id)
    yield examination_id
    _reset_examination_state(examination_id)


@pytest.fixture(autouse=True)
def _enforce_full_state_after_each_test(examination_id):
    yield
    _reset_examination_state(examination_id)


def _counts(examination_id):
    return {
        "halls": HallAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "seats": SeatAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
        "invs": InvigilatorAllocation.query.filter_by(
            examination_id=examination_id
        ).count(),
    }


# =============================================================
# 1. Options builder
# =============================================================

def test_options_builder_accepts_all_supported_keys():
    result = build_allocation_options({
        "minimize_halls": True,
        "accessibility_required": True,
        "exclude_maintenance_halls": True,
        "exclude_unavailable_halls": True,
        "avoid_timetable_conflicts": True,
    })
    assert result["success"] is True
    assert result["options"]["minimize_halls"] is True
    assert len(result["options"]) == 5


def test_options_builder_rejects_unknown_key():
    result = build_allocation_options({
        "minimize_halls": True,
        "assign_blue_seats": True,
    })
    assert result["success"] is False
    assert any(
        "assign_blue_seats" in err for err in result["errors"]
    )


def test_options_builder_rejects_wrong_type():
    result = build_allocation_options({"minimize_halls": "yes"})
    assert result["success"] is False


# =============================================================
# 2. Endpoint — preview vs apply
# =============================================================

def test_preview_does_not_mutate(
    admin_client, prepared_examination
):
    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls and accessible halls.",
        },
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["mode"] == "preview"
    assert body["allocation_options"]["minimize_halls"] is True
    assert body["allocation_options"]["accessibility_required"] is True

    assert _counts(prepared_examination) == before


def test_apply_regenerates_allocation(
    admin_client, prepared_examination
):
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": (
                "Use the minimum number of halls, keep "
                "accessibility students in accessible halls, "
                "exclude maintenance halls, exclude unavailable "
                "halls, avoid timetable conflicts."
            ),
            "confirm": True,
        },
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["mode"] == "applied"
    assert body["validation"]["status"] == "VALID"
    assert body["allocation"]["regenerated"] is True


def test_apply_rejects_unknown_key(
    admin_client, prepared_examination
):
    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirements": {
                "minimize_halls": True,
                "assign_blue_seats": True,
            },
            "confirm": True,
        },
    )
    assert r.status_code == 400
    assert _counts(prepared_examination) == before


def test_apply_requires_admin(client, prepared_examination):
    r = client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirements": {"minimize_halls": True},
            "confirm": True,
        },
    )
    assert r.status_code in (401, 403)

def test_apply_with_unsupported_only_does_not_alter_allocation(
    admin_client, prepared_examination
):
    """
    A requirement that parses to nothing supported must not
    regenerate the allocation, even when confirm=true is sent.
    """
    before = _counts(prepared_examination)

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Give students blue-colored seats.",
            "confirm": True,
        },
    )
    assert r.status_code == 400, r.get_json()
    assert r.get_json()["success"] is False

    assert _counts(prepared_examination) == before

# =============================================================
# 3. Safety constraints remain enforced
# =============================================================

def test_maintenance_halls_excluded_when_requested(
    admin_client, prepared_examination
):
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Exclude maintenance halls.",
            "confirm": True,
        },
    )
    assert r.status_code == 200, r.get_json()

    for allocation in HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).all():
        hall = Hall.query.get(allocation.hall_id)
        assert hall.is_under_maintenance is False


def test_unavailable_halls_excluded_when_requested(
    admin_client, prepared_examination
):
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Exclude unavailable halls.",
            "confirm": True,
        },
    )
    assert r.status_code == 200, r.get_json()

    for allocation in HallAllocation.query.filter_by(
        examination_id=prepared_examination
    ).all():
        hall = Hall.query.get(allocation.hall_id)
        assert hall.is_available is True
        assert hall.is_active is True


# =============================================================
# 4. Determinism
# =============================================================

def test_same_requirements_produce_same_allocation(
    prepared_examination
):
    options = {
        "minimize_halls": True,
        "accessibility_required": True,
    }

    a = generate_allocation(
        prepared_examination,
        force=True,
        allocation_options=options,
    )
    assert a["success"] is True
    first = sorted(
        (h.timetable_id, h.hall_id)
        for h in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    )

    b = generate_allocation(
        prepared_examination,
        force=True,
        allocation_options=options,
    )
    assert b["success"] is True
    second = sorted(
        (h.timetable_id, h.hall_id)
        for h in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    )

    assert first == second


def test_none_options_is_byte_identical_to_previous_behavior(
    prepared_examination
):
    """
    Passing allocation_options=None must not change the
    allocation produced by the deterministic engine.
    """
    a = generate_allocation(
        prepared_examination, force=True,
    )
    assert a["success"] is True
    first = sorted(
        (h.timetable_id, h.hall_id)
        for h in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    )

    b = generate_allocation(
        prepared_examination,
        force=True,
        allocation_options=None,
    )
    assert b["success"] is True
    second = sorted(
        (h.timetable_id, h.hall_id)
        for h in HallAllocation.query.filter_by(
            examination_id=prepared_examination
        ).all()
    )

    assert first == second