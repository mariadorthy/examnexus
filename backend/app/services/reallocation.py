"""
Feature 21 — Dynamic Reallocation / What-If Replanning.

Pure, read-only simulation layer around the existing
deterministic allocator (services/allocation.py).

Hard rules:
  - simulate_reallocation() MUST NOT write to the database.
  - It reuses _plan_hall_allocations(); it does not implement a
    second allocator.
  - It never mutates Hall rows.
  - It is not allowed when the examination is PUBLISHED.
"""
from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.allocation import _plan_hall_allocations


def _normalize_excluded(raw):
    if not raw:
        return None
    try:
        normalized = {int(v) for v in raw}
    except (TypeError, ValueError):
        return "INVALID"
    return normalized or None


def _current_snapshot(examination_id):
    """Read persisted hall + seat + invigilator state (read-only)."""

    hall_allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    hall_ids = sorted({row.hall_id for row in hall_allocations})

    halls = {
        hall.id: hall
        for hall in Hall.query.filter(Hall.id.in_(hall_ids)).all()
    } if hall_ids else {}

    per_hall = {}
    for row in hall_allocations:
        hall = halls.get(row.hall_id)
        per_hall[row.hall_id] = {
            "hall_id": row.hall_id,
            "hall_name": hall.name if hall else None,
            "timetable_id": row.timetable_id,
            "allocated_capacity": row.allocated_capacity,
            "purpose": row.purpose,
        }

    seat_rows = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    invigilator_rows = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    return {
        "hall_allocations": hall_allocations,
        "halls_by_id": halls,
        "per_hall": per_hall,
        "seat_rows": seat_rows,
        "invigilator_rows": invigilator_rows,
        "hall_ids": hall_ids,
    }


def simulate_reallocation(examination_id, excluded_hall_ids):
    """
    Compute a proposed reallocation in memory.

    Returns a structured proposal dict. Does not touch the DB.
    """

    excluded = _normalize_excluded(excluded_hall_ids)

    if excluded == "INVALID":
        return {
            "success": False,
            "message": (
                "excluded_hall_ids must be a list of "
                "integer hall ids."
            ),
        }

    if not excluded:
        return {
            "success": False,
            "message": (
                "At least one hall must be marked unavailable."
            ),
        }

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found",
        }

    status = (examination.status or "DRAFT").upper()

    if status == "PUBLISHED":
        return {
            "success": False,
            "message": (
                "Reallocation is not permitted after the "
                "examination has been PUBLISHED."
            ),
            "examination_status": status,
        }

    # Refuse to exclude a hall that is not part of the current
    # allocation — that would be a user error, not an incident.
    current = _current_snapshot(examination_id)

    if not current["hall_allocations"]:
        return {
            "success": False,
            "message": (
                "No hall allocation exists for this "
                "examination yet."
            ),
            "examination_status": status,
        }

    unknown_excluded = sorted(
        h for h in excluded if h not in current["hall_ids"]
    )

    if unknown_excluded:
        return {
            "success": False,
            "message": (
                "Excluded hall(s) are not part of the current "
                "allocation."
            ),
            "unknown_excluded_hall_ids": unknown_excluded,
        }

    timetables = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
            Timetable.id
        )
        .all()
    )

    if not timetables:
        return {
            "success": False,
            "message": "No timetable entries found.",
        }

    plan = _plan_hall_allocations(
        examination=examination,
        timetables=timetables,
        excluded_hall_ids=excluded
    )

    if not plan["success"]:
        # Infeasible replan. Return the specific reason.
        return {
            "success": False,
            "message": plan.get(
                "message",
                "Unable to replan with excluded halls."
            ),
            "examination_id": examination_id,
            "examination_status": status,
            "excluded_hall_ids": sorted(excluded),
            "detail": plan,
        }

    proposed_allocations = plan["allocations"]

    # ---------------------------------------------------------
    # DIFF
    # ---------------------------------------------------------
    current_by_key = {}

    for allocation in current["hall_allocations"]:
        key = (
            allocation.timetable_id,
            allocation.hall_id
        )

        current_by_key[key] = {
            "timetable_id": allocation.timetable_id,
            "hall_id": allocation.hall_id,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
        }

    proposed_by_key = {}

    for allocation in proposed_allocations:
        key = (
            allocation.timetable_id,
            allocation.hall_id
        )

        proposed_by_key[key] = {
            "timetable_id": allocation.timetable_id,
            "hall_id": allocation.hall_id,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
        }

    removed_keys = sorted(
        set(current_by_key) - set(proposed_by_key)
    )

    added_keys = sorted(
        set(proposed_by_key) - set(current_by_key)
    )

    retained_keys = sorted(
        set(current_by_key) & set(proposed_by_key)
    )

    removed_halls = sorted({
        hall_id
        for _, hall_id in removed_keys
    })

    added_halls = sorted({
        hall_id
        for _, hall_id in added_keys
    })

    retained_halls = sorted({
        hall_id
        for _, hall_id in retained_keys
    })
    # Affected students = students currently seated in a
    # hall that is being removed.
    affected_student_ids = {
        row.student_id
        for row in current["seat_rows"]
        if row.hall_id in removed_halls
    }

    affected_students = len(affected_student_ids)

    # ---------------------------------------------------------
    # EXPLANATIONS (deterministic, from real constraint data)
    # ---------------------------------------------------------

    explanations = []

    excluded_hall_names = [
        current["halls_by_id"][hid].name
        for hid in sorted(excluded)
        if hid in current["halls_by_id"]
    ]

    for name in excluded_hall_names:
        explanations.append({
            "hall": name,
            "reason": (
                "Excluded by administrator: hall became "
                "unavailable for this operation."
            ),
        })

    for hall_id in added_halls:
        hall = Hall.query.get(hall_id)
        if not hall:
            continue

        reasons = []
        if hall.is_available:
            reasons.append("available")
        if not hall.is_under_maintenance:
            reasons.append("not under maintenance")
        if hall.examination_capacity > 0:
            reasons.append(
                f"examination capacity {hall.examination_capacity}"
            )

        explanations.append({
            "hall": hall.name,
            "reason": (
                "Selected as replacement: "
                + ", ".join(reasons) + "."
            ),
        })

    # ---------------------------------------------------------
    # PROPOSAL VALIDATION (pure)
    # ---------------------------------------------------------

    from app.services.validation import validate_proposed_plan

    proposal_validation = validate_proposed_plan(
        examination_id=examination_id,
        proposed_allocations=[
            {
                "timetable_id": row.timetable_id,
                "hall_id": row.hall_id,
                "allocated_capacity": row.allocated_capacity,
                "purpose": row.purpose,
            }
            for row in proposed_allocations
        ],
        eligible_students=plan["total_students"],
        accessibility_students=len(
            plan["accessibility_students"]
        ),
    )

    current_total_capacity = sum(
        row.allocated_capacity
        for row in current["hall_allocations"]
    )
    proposed_total_capacity = sum(
        row.allocated_capacity
        for row in proposed_allocations
    )

    requires_reapproval = status in {"REVIEW", "APPROVED"}

    return {
        "success": True,
        "examination_id": examination_id,
        "examination_status": status,
        "excluded_hall_ids": sorted(excluded),
        "current": {
            "halls_used": len(current_by_key),
            "total_capacity": current_total_capacity,
            "hall_ids": current["hall_ids"],
        },
        "proposed": {
    "halls_used": len({
        hall_id
        for _, hall_id in proposed_by_key
    }),
    "total_capacity": proposed_total_capacity,
    "hall_ids": sorted({
        hall_id
        for _, hall_id in proposed_by_key
    }),        
            "per_hall": [
                {
                    "hall_id": row.hall_id,
                    "timetable_id": row.timetable_id,
                    "allocated_capacity": row.allocated_capacity,
                    "purpose": row.purpose,
                }
                for row in proposed_allocations
            ],
        },
        "diff": {
            "removed_halls": removed_halls,
            "added_halls": added_halls,
            "retained_halls": retained_halls,
            "affected_students": affected_students,
            "affected_student_ids": sorted(affected_student_ids),
            "unallocated_students": 0,
        },
        "validation": proposal_validation,
        "explanations": explanations,
        "requires_reapproval": requires_reapproval,
        "invigilators_will_be_invalidated": bool(
            current["invigilator_rows"]
        ),
    }

def apply_reallocation(examination_id, excluded_hall_ids):
    """
    Apply a validated Feature 21 reallocation.

    The operation is transactional:
      Hall allocations + seats + invigilators must all succeed.
      Otherwise the previous allocation is restored.
    """

    from app.services.seat_allocation import generate_seat_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation
    )
    from app.services.validation import (
        validate_allocation,
        validate_invigilator_allocation,
    )

    simulation = simulate_reallocation(
        examination_id,
        excluded_hall_ids
    )

    if not simulation.get("success"):
        return simulation

    if simulation.get("validation", {}).get("status") != "VALID":
        return {
            "success": False,
            "message": (
                "Proposed reallocation is invalid; "
                "no changes were applied."
            ),
            "validation": simulation.get("validation")
        }

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
        }

    if (examination.status or "DRAFT").upper() == "PUBLISHED":
        return {
            "success": False,
            "message": "Published examinations cannot be reallocated."
        }

    try:
        # Remove dependent state first.
        SeatAllocation.query.filter_by(
            examination_id=examination_id
        ).delete(synchronize_session=False)

        InvigilatorAllocation.query.filter_by(
            examination_id=examination_id
        ).delete(synchronize_session=False)

        HallAllocation.query.filter_by(
            examination_id=examination_id
        ).delete(synchronize_session=False)

        db.session.flush()

        # Reuse the existing deterministic planner.
        timetables = (
            Timetable.query
            .filter_by(examination_id=examination_id)
            .order_by(
                Timetable.exam_date.asc(),
                Timetable.start_time.asc(),
                Timetable.id.asc()
            )
            .all()
        )

        plan = _plan_hall_allocations(
            examination=examination,
            timetables=timetables,
            excluded_hall_ids=set(
                int(value)
                for value in excluded_hall_ids
            )
        )

        if not plan.get("success"):
            db.session.rollback()

            return {
                "success": False,
                "message": "Reallocation failed.",
                "detail": plan.get("message")
            }

        for allocation in plan["allocations"]:
            db.session.add(allocation)

        db.session.flush()

        seat_result = generate_seat_allocation(
            examination_id,
            force=True,
            commit=False
        )

        if not seat_result.get("success"):
            db.session.rollback()

            return {
                "success": False,
                "message": "Seat allocation failed; previous state restored.",
                "detail": seat_result.get("message")
            }

        invigilator_result = generate_invigilator_allocation(
            examination_id,
            force=True,
            commit=False
        )

        if not invigilator_result.get("success"):
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    "Invigilator allocation failed; "
                    "previous state restored."
                ),
                "detail": invigilator_result.get("message")
            }

        hall_validation = validate_allocation(examination_id)
        invig_validation = validate_invigilator_allocation(
            examination_id
        )

        if hall_validation.get("status") != "VALID":
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    "Post-apply hall/seat validation failed; "
                    "previous state restored."
                ),
                "validation": hall_validation
            }

        if invig_validation.get("status") != "VALID":
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    "Post-apply invigilator validation failed; "
                    "previous state restored."
                ),
                "validation": invig_validation
            }

        previous_status = examination.status

        # An APPROVED plan is no longer approved after modification.
        if previous_status == "APPROVED":
            examination.status = "REVIEW"

        db.session.commit()

        return {
            "success": True,
            "message": "Reallocation applied successfully.",
            "examination_id": examination_id,
            "previous_status": previous_status,
            "status": examination.status,
            "requires_reapproval": previous_status == "APPROVED",
            "post_apply_validation": {
                "hall": hall_validation,
                "invigilator": invig_validation
            },
            "invigilators_regenerated": True,
            "seats_regenerated": True
        }

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": (
                "Reallocation failed; previous state restored."
            ),
            "error": str(error)
        }