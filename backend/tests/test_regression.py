"""
Golden-path end-to-end regression.

This is not a re-run of every assertion in the phase files.
It is a single walking-through of the whole system, top to
bottom, in the same order an administrator would use it.

If this file passes AND every phase file passes, the
platform is healthy.
"""

from app import db
from app.models.examination import Examination
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation
from app.models.hall_ticket import HallTicket

from app.services.allocation import generate_allocation
from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
)
from app.services.validation import (
    validate_allocation,
    validate_invigilator_allocation,
)
from app.services.hall_ticket import generate_hall_tickets
from app.services.lifecycle import transition_status


def test_full_pipeline_is_healthy(app_context, examination_id):
    # ------------------------------------------------------
    # 1. Examination exists
    # ------------------------------------------------------
    examination = db.session.get(Examination, examination_id)
    assert examination is not None

    # ------------------------------------------------------
    # 2. Hall + seat allocation
    # ------------------------------------------------------
    result = generate_allocation(examination_id, force=True)
    assert result.get("success") is True, result

    # ------------------------------------------------------
    # 3. Invigilator allocation
    # ------------------------------------------------------
    invig = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert invig.get("success") is True, invig

    # ------------------------------------------------------
    # 4. Independent validation
    # ------------------------------------------------------
    assert (
        validate_allocation(examination_id).get("status")
        == "VALID"
    )
    assert (
        validate_invigilator_allocation(examination_id).get("status")
        == "VALID"
    )

    # ------------------------------------------------------
    # 5. Persisted state is consistent
    # ------------------------------------------------------
    assert HallAllocation.query.filter_by(
        examination_id=examination_id
    ).count() > 0
    assert SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).count() > 0
    assert InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).count() > 0

    # ------------------------------------------------------
    # 6. Publish and issue hall tickets
    # ------------------------------------------------------

    examination = db.session.get(
        Examination,
        examination_id,
    )

    current_status = examination.status

    lifecycle_order = [
        "DRAFT",
        "GENERATED",
        "VALIDATED",
        "REVIEW",
        "APPROVED",
        "PUBLISHED",
    ]

    current_index = lifecycle_order.index(current_status)

    for next_index in range(
        current_index + 1,
        len(lifecycle_order),
    ):
        transition_result = transition_status(
            examination_id,
            lifecycle_order[next_index],
        )

        assert transition_result.get("success") is True, (
            transition_result
        )

    db.session.refresh(examination)

    assert examination.status == "PUBLISHED"

    tickets = generate_hall_tickets(
        examination_id, force=True
    )
    assert tickets.get("success") is True, tickets
    assert tickets.get("issued", 0) > 0

    assert HallTicket.query.filter_by(
        examination_id=examination_id
    ).count() > 0