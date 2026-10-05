"""
Post-Phase 7 — Bulk operations.
"""
from app import db
from app.models.seat_allocation import SeatAllocation
from app.models.timetable import Timetable

from app.services.seat_allocation import (
    generate_bulk_seat_allocation,
)
from app.services.invigilator_allocation import (
    generate_bulk_invigilator_allocation,
)
from app.services.validation import bulk_validate_examinations
from app.services import bulk_allocation as bulk_hall_module


MISSING_ID = 999999


def test_bulk_seat_allocation_single(
    app_context, examination_id
):
    result = generate_bulk_seat_allocation(
        [examination_id], force=True
    )
    assert result.get("success") is True
    assert result["results"][0]["status"] == "GENERATED"


def test_bulk_seat_allocation_mixed(
    app_context, examination_id
):
    result = generate_bulk_seat_allocation(
        [examination_id, MISSING_ID], force=True
    )
    assert result["results"][0]["status"] == "GENERATED"
    assert result["results"][1]["status"] == "FAILED"


def test_bulk_seat_allocation_preserves_mixed_course_strategy(
    app_context, examination_id
):
    result = generate_bulk_seat_allocation(
        [examination_id],
        force=True
    )

    assert result.get("success") is True
    assert result["results"][0]["status"] == "GENERATED"

    seats = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).all()

    assert seats

    # Course data must remain available through the normalized
    # Student -> Course relationship.
    course_aware_seats = [
        seat
        for seat in seats
        if seat.student is not None
        and seat.student.course is not None
    ]

    assert len(course_aware_seats) == len(seats)

def test_bulk_invigilator_allocation_single(
    app_context, examination_id
):
    result = generate_bulk_invigilator_allocation(
        [examination_id], force=True
    )
    assert result.get("success") is True
    assert result["results"][0]["status"] == "GENERATED"


def test_bulk_invigilator_allocation_mixed(
    app_context, examination_id
):
    result = generate_bulk_invigilator_allocation(
        [examination_id, MISSING_ID], force=True
    )
    assert result["results"][0]["status"] == "GENERATED"
    assert result["results"][1]["status"] == "FAILED"


def test_bulk_validation_mixed(app_context, examination_id):
    result = bulk_validate_examinations(
        [examination_id, MISSING_ID]
    )
    assert result["processed"] == 2
    assert result["results"][0]["status"] == "VALID"
    assert result["results"][1]["status"] == "INVALID"

def test_bulk_hall_allocation_mixed(app_context, examination_id):
    assert hasattr(
        bulk_hall_module,
        "generate_bulk_allocation",
    ), "Bulk hall allocation service is required"

    result = bulk_hall_module.generate_bulk_allocation(
        [examination_id, MISSING_ID],
        force=True,
    )

    assert len(result.get("results", [])) == 2
    assert result["results"][0]["status"] == "GENERATED"
    assert result["results"][1]["status"] == "FAILED"


# ============================================================
# 9G — RBAC on bulk endpoints
# ============================================================

def test_bulk_seat_endpoint_rejects_unauthenticated(
    client, examination_id
):
    response = client.post(
        "/api/allocations/seats/bulk-generate",
        json={"examination_ids": [examination_id]},
    )
    assert response.status_code in (401, 403)


def test_bulk_invigilator_endpoint_rejects_unauthenticated(
    client, examination_id
):
    response = client.post(
        "/api/allocations/invigilators/bulk-generate",
        json={"examination_ids": [examination_id]},
    )
    assert response.status_code in (401, 403)


def test_bulk_validate_endpoint_rejects_unauthenticated(
    client, examination_id
):
    response = client.post(
        "/api/allocations/validate/bulk",
        json={"examination_ids": [examination_id]},
    )
    assert response.status_code in (401, 403)