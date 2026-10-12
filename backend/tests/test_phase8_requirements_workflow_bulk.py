"""
Issue 5 (extended) — Bulk natural-language allocation workflow.

Covers:
  - /api/requirements/apply-bulk preview and apply
  - per-exam readiness / lifecycle handling
  - invigilator generation driven by the NL prompt
  - hard-refuse for lifecycle instructions
  - backward compatibility of the existing single-exam route
"""

import pytest

from app import db
from app.models.examination import Examination
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation


def _reset_examination_state(examination_id):
    from app.models.hall_ticket import HallTicket
    from app.services.allocation import generate_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )

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

    r = generate_allocation(examination_id, force=True)
    assert r.get("success"), r

    r = generate_invigilator_allocation(examination_id, force=True)
    assert r.get("success"), r


@pytest.fixture
def prepared_examination(examination_id):
    _reset_examination_state(examination_id)
    yield examination_id
    _reset_examination_state(examination_id)


@pytest.fixture(autouse=True)
def _restore_after(examination_id):
    yield
    _reset_examination_state(examination_id)


def test_bulk_preview_does_not_mutate(
    admin_client, prepared_examination
):
    before = InvigilatorAllocation.query.filter_by(
        examination_id=prepared_examination
    ).count()

    r = admin_client.post(
        "/api/requirements/apply-bulk",
        json={
            "examination_ids": [prepared_examination],
            "requirement": "Use minimum halls.",
        },
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["mode"] == "preview"
    assert body["results"][0]["status"] == "PREVIEW"

    after = InvigilatorAllocation.query.filter_by(
        examination_id=prepared_examination
    ).count()
    assert before == after


def test_bulk_apply_generates_invigilators_when_requested(
    admin_client, prepared_examination
):
    exam = Examination.query.get(prepared_examination)
    expected = exam.updated_at.isoformat()

    r = admin_client.post(
        "/api/requirements/apply-bulk",
        json={
            "examination_ids": [prepared_examination],
            "requirement": (
                "Use minimum halls and generate invigilators."
            ),
            "confirm": True,
            "expected_updated_at_map": {
                str(prepared_examination): expected,
            },
        },
    )
    assert r.status_code == 200, r.get_json()
    row = r.get_json()["results"][0]
    assert row["status"] == "APPLIED"
    assert row["invigilator_allocation"] is not None
    assert row["invigilator_allocation"]["success"] is True
    assert row["invigilator_validation"]["status"] == "VALID"


def test_bulk_apply_refuses_lifecycle_instructions(
    admin_client, prepared_examination
):
    r = admin_client.post(
        "/api/requirements/apply-bulk",
        json={
            "examination_ids": [prepared_examination],
            "requirement": "Use minimum halls and approve the exam.",
            "confirm": True,
        },
    )
    assert r.status_code == 400, r.get_json()
    body = r.get_json()
    assert body["blocking_requirements"]


def test_single_apply_refuses_lifecycle_instructions(
    admin_client, prepared_examination
):
    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": "Use minimum halls and publish the exam.",
        },
    )
    assert r.status_code == 400, r.get_json()
    body = r.get_json()
    assert body["blocking_requirements"]


def test_single_apply_generates_invigilators_when_requested(
    admin_client, prepared_examination
):
    exam = Examination.query.get(prepared_examination)
    expected = exam.updated_at.isoformat()

    r = admin_client.post(
        f"/api/requirements/apply/{prepared_examination}",
        json={
            "requirement": (
                "Use minimum halls and generate invigilators."
            ),
            "confirm": True,
            "expected_updated_at": expected,
        },
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["mode"] == "applied"
    assert body["invigilator_allocation"]["success"] is True
    assert body["invigilator_validation"]["status"] == "VALID"