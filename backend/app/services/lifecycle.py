"""
Examination lifecycle service.

Forward-only status transitions, server-enforced:

    DRAFT -> GENERATED -> VALIDATED -> REVIEW -> APPROVED -> PUBLISHED

Rules:
  - DRAFT     -> GENERATED : allocation must exist for the examination
  - GENERATED -> VALIDATED : independent validation must pass
  - VALIDATED -> REVIEW    : no gate (admin declares they are reviewing)
  - REVIEW    -> APPROVED  : validation re-run must pass, and status must
                             currently be REVIEW
  - APPROVED  -> PUBLISHED : status must currently be APPROVED

No status may move backward. No status may skip. Invalid transitions
are rejected with a structured error.
"""

from app import db
from app.models.examination import Examination
from app.models.hall_allocation import HallAllocation

from app.services.validation import (
    validate_allocation,
    validate_invigilator_allocation
)


ALLOWED_TRANSITIONS = {
    "DRAFT":     {"GENERATED"},
    "GENERATED": {"VALIDATED"},
    "VALIDATED": {"REVIEW"},
    "REVIEW":    {"APPROVED"},
    "APPROVED":  {"PUBLISHED"},
    "PUBLISHED": set(),
}


def _can_transition(current, target):
    return target in ALLOWED_TRANSITIONS.get(current, set())


def _require_hall_allocation(examination_id):
    return (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .count()
    ) > 0


def transition_status(examination_id, target_status):
    """
    Server-enforced forward-only status transition.

    Returns a dict with:
      success  bool
      status   final status on success
      message  human-readable
      errors   list of strings (on failure)
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found",
            "errors": ["Examination not found"]
        }

    target_status = str(target_status).upper()

    current_status = examination.status or "DRAFT"

    if target_status not in ALLOWED_TRANSITIONS:
        return {
            "success": False,
            "status": current_status,
            "message": f"Unknown target status: {target_status}",
            "errors": [f"Unknown target status: {target_status}"]
        }

    if not _can_transition(current_status, target_status):
        return {
            "success": False,
            "status": current_status,
            "message": (
                f"Cannot transition from {current_status} "
                f"to {target_status}"
            ),
            "errors": [
                f"Illegal transition: {current_status} -> "
                f"{target_status}"
            ]
        }

    # ---------------------------------------------------------
    # GATE: DRAFT -> GENERATED
    # ---------------------------------------------------------

    if target_status == "GENERATED":
        if not _require_hall_allocation(examination_id):
            return {
                "success": False,
                "status": current_status,
                "message": (
                    "Hall allocation must exist before the "
                    "examination can be marked GENERATED"
                ),
                "errors": ["Hall allocation not generated"]
            }

    # ---------------------------------------------------------
    # GATE: GENERATED -> VALIDATED
    # ---------------------------------------------------------

    if target_status == "VALIDATED":
        hall_result = validate_allocation(examination_id)
        invig_result = validate_invigilator_allocation(examination_id)

        errors = []

        if hall_result.get("status") != "VALID":
            errors.append(
                "Hall/seat validation failed: "
                + "; ".join(hall_result.get("errors", []) or [])
            )

        if invig_result.get("status") != "VALID":
            errors.append(
                "Invigilator validation failed: "
                + "; ".join(invig_result.get("errors", []) or [])
            )

        if errors:
            return {
                "success": False,
                "status": current_status,
                "message": (
                    "Allocation is not valid; cannot mark VALIDATED"
                ),
                "errors": errors
            }

    # ---------------------------------------------------------
    # GATE: REVIEW -> APPROVED
    # ---------------------------------------------------------

    if target_status == "APPROVED":
        hall_result = validate_allocation(examination_id)
        invig_result = validate_invigilator_allocation(examination_id)

        errors = []

        if hall_result.get("status") != "VALID":
            errors.append(
                "Hall/seat validation failed at approval time"
            )

        if invig_result.get("status") != "VALID":
            errors.append(
                "Invigilator validation failed at approval time"
            )

        if errors:
            return {
                "success": False,
                "status": current_status,
                "message": (
                    "Allocation is no longer valid; "
                    "cannot APPROVE"
                ),
                "errors": errors
            }

    # ---------------------------------------------------------
    # GATE: APPROVED -> PUBLISHED
    #
    # Publishing is the point of no return: hall tickets become
    # issuable from this moment. We re-run both validators here
    # rather than trusting the APPROVED snapshot, because the
    # persisted allocation may have drifted after approval.
    # ---------------------------------------------------------

    if target_status == "PUBLISHED":
        hall_result = validate_allocation(examination_id)
        invig_result = validate_invigilator_allocation(examination_id)

        errors = []

        if hall_result.get("status") != "VALID":
            errors.append(
                "Final hall/seat validation failed at publish time: "
                + "; ".join(hall_result.get("errors", []) or [])
            )

        if invig_result.get("status") != "VALID":
            errors.append(
                "Final invigilator validation failed at publish time: "
                + "; ".join(invig_result.get("errors", []) or [])
            )

        if errors:
            return {
                "success": False,
                "status": current_status,
                "message": (
                    "Final validation failed; cannot PUBLISH"
                ),
                "errors": errors
            }

    # ---------------------------------------------------------
    # APPLY
    # ---------------------------------------------------------

    try:
        examination.status = target_status
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return {
            "success": False,
            "status": current_status,
            "message": "Failed to update examination status",
            "errors": [str(error)]
        }

    return {
        "success": True,
        "status": target_status,
        "previous_status": current_status,
        "message": f"Examination moved to {target_status}"
    }