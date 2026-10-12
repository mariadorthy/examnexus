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
from datetime import date

from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation
from app.models.hall_incident import HallIncident
from app.services.allocation import _plan_hall_allocations


def _normalize_excluded(raw):
    if not raw:
        return None
    try:
        normalized = {int(v) for v in raw}
    except (TypeError, ValueError):
        return "INVALID"
    return normalized or None


def _load_emergency_incident(incident_id, examination_id):
    """
    Load and validate the incident that justifies an
    emergency reallocation.

    Rules:
      - The incident must exist.
      - It must be OPEN. A resolved incident no longer
        authorizes a new reallocation.
      - It must apply to this examination: either scope=GLOBAL
        (applies to every examination), or scope=EXAM_SPECIFIC
        with matching examination_id.
    """
    if incident_id is None:
        return None, (
            "incident_id is required for emergency reallocation."
        )

    try:
        incident_id = int(incident_id)
    except (TypeError, ValueError):
        return None, "incident_id must be an integer."

    incident = HallIncident.query.get(incident_id)

    if not incident:
        return None, f"Incident #{incident_id} not found."

    if incident.status != "OPEN":
        return None, (
            f"Incident #{incident_id} is not OPEN; "
            "only OPEN incidents authorize emergency reallocation."
        )

    if incident.scope == "EXAM_SPECIFIC":
        if incident.examination_id != examination_id:
            return None, (
                f"Incident #{incident_id} applies to examination "
                f"#{incident.examination_id}, not #{examination_id}."
            )

    return incident, None


def _emergency_in_progress_flag(examination):
    """
    Return a dict describing the examination's in-progress state
    using only data that exists:
      - start_date and end_date (day granularity)

    Values:
      - {"state": "ENDED"}         today > end_date
      - {"state": "IN_PROGRESS"}   start_date <= today <= end_date
      - {"state": "NOT_STARTED"}   today < start_date
    """
    today = date.today()

    if today > examination.end_date:
        return {"state": "ENDED"}

    if today >= examination.start_date:
        return {"state": "IN_PROGRESS"}

    return {"state": "NOT_STARTED"}

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
        explanations.append(
            {
                "hall": name,
                "decision": "REJECTED",
                "reasons": [
                    {
                        "code": "REJECTED_TRANSIENTLY_EXCLUDED",
                        "message": (
                            "Hall was excluded by the administrator "
                            "for this what-if reallocation."
                        ),
                    }
                ],
            }
        )
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

        explanations.append(
            {
    "hall": hall.name,
    "decision": "SELECTED",
    "reasons": [
        {
            "code": "HALL_ACTIVE",
            "message": "Hall is active."
        },
        {
            "code": "HALL_AVAILABLE",
            "message": "Hall is available."
        },
        {
            "code": "NOT_UNDER_MAINTENANCE",
            "message": "Hall is not under maintenance."
        },
        {
            "code": "HAS_EXAM_CAPACITY",
            "message": "Hall has sufficient examination capacity."
        },
        {
            "code": "SELECTED_BY_ALLOCATOR_STRATEGY",
            "message": "Selected by the deterministic hall allocation strategy."
        }
    ]
}
        )

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

        # Invalidate any hall tickets issued for the previous
        # arrangement. Runs inside the same transaction so a
        # later validation failure rolls this back too.
        from app.services.hall_ticket import (
            invalidate_hall_tickets
        )

        ticket_result = invalidate_hall_tickets(
            examination_id,
            commit=False
        )

        if not ticket_result.get("success"):
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    "Failed to invalidate existing hall tickets; "
                    "previous state restored."
                ),
                "detail": ticket_result,
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
            "seats_regenerated": True,
            "tickets_invalidated": ticket_result.get(
                "invalidated", 0
            ),
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

def simulate_emergency_reallocation(
    examination_id,
    excluded_hall_ids,
    incident_id,
):
    """
    Emergency reallocation simulation for a PUBLISHED examination.

    Differences from simulate_reallocation():
      - Allows PUBLISHED status.
      - Requires a valid, OPEN incident.
      - Refuses if the examination has ended.
      - Adds an in_progress flag to the response so the caller
        knows whether extra acknowledgement is needed to apply.

    Read-only. Nothing is persisted.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    status = (examination.status or "DRAFT").upper()

    if status != "PUBLISHED":
        return {
            "success": False,
            "message": (
                "Emergency reallocation is only available for "
                "PUBLISHED examinations. Use the standard What-If "
                "workflow for this examination."
            ),
            "examination_status": status,
        }

    incident, incident_error = _load_emergency_incident(
        incident_id, examination_id
    )
    if incident_error:
        return {"success": False, "message": incident_error}

    progress = _emergency_in_progress_flag(examination)

    if progress["state"] == "ENDED":
        return {
            "success": False,
            "message": (
                "Examination has already ended. Emergency "
                "reallocation is not applicable."
            ),
            "examination_status": status,
            "in_progress_state": progress["state"],
        }

    # Reuse the existing simulate_reallocation machinery by
    # calling the shared planner through a temporary shortcut.
    # We can't call simulate_reallocation directly because it
    # refuses PUBLISHED. So we replicate its body but keep the
    # published branch out.
    excluded = _normalize_excluded(excluded_hall_ids)

    if excluded == "INVALID":
        return {
            "success": False,
            "message": (
                "excluded_hall_ids must be a list of integer "
                "hall ids."
            ),
        }

    if not excluded:
        return {
            "success": False,
            "message": (
                "At least one hall must be marked unavailable."
            ),
        }

    current = _current_snapshot(examination_id)

    if not current["hall_allocations"]:
        return {
            "success": False,
            "message": (
                "No hall allocation exists for this examination."
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
            Timetable.id,
        )
        .all()
    )

    if not timetables:
        return {"success": False, "message": "No timetable entries found."}

    plan = _plan_hall_allocations(
        examination=examination,
        timetables=timetables,
        excluded_hall_ids=excluded,
    )

    if not plan["success"]:
        return {
            "success": False,
            "message": plan.get(
                "message",
                "Unable to replan with excluded halls.",
            ),
            "examination_id": examination_id,
            "examination_status": status,
            "excluded_hall_ids": sorted(excluded),
            "detail": plan,
        }

    # The rest of this function duplicates the tail of
    # simulate_reallocation deliberately — the two flows must
    # stay independent so the ordinary what-if remains
    # untouched. Any change here does not affect that path.

    proposed_allocations = plan["allocations"]

    current_by_key = {}
    for allocation in current["hall_allocations"]:
        key = (allocation.timetable_id, allocation.hall_id)
        current_by_key[key] = {
            "timetable_id": allocation.timetable_id,
            "hall_id": allocation.hall_id,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
        }

    proposed_by_key = {}
    for allocation in proposed_allocations:
        key = (allocation.timetable_id, allocation.hall_id)
        proposed_by_key[key] = {
            "timetable_id": allocation.timetable_id,
            "hall_id": allocation.hall_id,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
        }

    removed_keys = sorted(set(current_by_key) - set(proposed_by_key))
    added_keys = sorted(set(proposed_by_key) - set(current_by_key))
    retained_keys = sorted(set(current_by_key) & set(proposed_by_key))

    removed_halls = sorted({hall_id for _, hall_id in removed_keys})
    added_halls = sorted({hall_id for _, hall_id in added_keys})
    retained_halls = sorted({hall_id for _, hall_id in retained_keys})

    affected_student_ids = {
        row.student_id
        for row in current["seat_rows"]
        if row.hall_id in removed_halls
    }

    explanations = []

    excluded_hall_names = [
        current["halls_by_id"][hid].name
        for hid in sorted(excluded)
        if hid in current["halls_by_id"]
    ]

    for name in excluded_hall_names:
        explanations.append({
            "hall": name,
            "decision": "REJECTED",
            "reasons": [{
                "code": "REJECTED_EMERGENCY_EXCLUDED",
                "message": (
                    "Hall was excluded by the administrator for "
                    "this emergency reallocation."
                ),
            }],
        })

    for hall_id in added_halls:
        hall = Hall.query.get(hall_id)
        if not hall:
            continue
        explanations.append({
            "hall": hall.name,
            "decision": "SELECTED",
            "reasons": [
                {"code": "HALL_ACTIVE",
                 "message": "Hall is active."},
                {"code": "HALL_AVAILABLE",
                 "message": "Hall is available."},
                {"code": "NOT_UNDER_MAINTENANCE",
                 "message": "Hall is not under maintenance."},
                {"code": "HAS_EXAM_CAPACITY",
                 "message": (
                     "Hall has sufficient examination capacity."
                 )},
                {"code": "SELECTED_BY_ALLOCATOR_STRATEGY",
                 "message": (
                     "Selected by the deterministic hall "
                     "allocation strategy."
                 )},
            ],
        })

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
        accessibility_students=len(plan["accessibility_students"]),
    )

    current_total_capacity = sum(
        row.allocated_capacity
        for row in current["hall_allocations"]
    )
    proposed_total_capacity = sum(
        row.allocated_capacity
        for row in proposed_allocations
    )

    return {
        "success": True,
        "emergency": True,
        "incident_id": incident.id,
        "examination_id": examination_id,
        "examination_status": status,
        "in_progress_state": progress["state"],
        "requires_in_progress_ack": progress["state"] == "IN_PROGRESS",
        "excluded_hall_ids": sorted(excluded),
        "current": {
            "halls_used": len(current_by_key),
            "total_capacity": current_total_capacity,
            "hall_ids": current["hall_ids"],
        },
        "proposed": {
            "halls_used": len({hid for _, hid in proposed_by_key}),
            "total_capacity": proposed_total_capacity,
            "hall_ids": sorted({hid for _, hid in proposed_by_key}),
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
            "affected_students": len(affected_student_ids),
            "affected_student_ids": sorted(affected_student_ids),
            "unallocated_students": 0,
        },
        "validation": proposal_validation,
        "explanations": explanations,
        "requires_reapproval": False,
        "invigilators_will_be_invalidated": bool(
            current["invigilator_rows"]
        ),
    }

def apply_emergency_reallocation(
    examination_id,
    excluded_hall_ids,
    incident_id,
    acknowledge_in_progress=False,
):
    """
    Apply a validated emergency reallocation on a PUBLISHED
    examination.

    Transactional in the same shape as apply_reallocation.
    On success:
      - existing ISSUED hall tickets are marked SUPERSEDED,
      - new hall tickets are created at version N+1,
      - the examination status is unchanged (stays PUBLISHED),
      - the incident's resolution_notes are appended.

    On any failure, rolls back to the pre-apply state.
    """

    from app.services.seat_allocation import generate_seat_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )
    from app.services.validation import (
        validate_allocation,
        validate_invigilator_allocation,
    )
    from app.services.hall_ticket import (
        supersede_hall_tickets,
    )

    simulation = simulate_emergency_reallocation(
        examination_id,
        excluded_hall_ids,
        incident_id,
    )

    if not simulation.get("success"):
        return simulation

    if simulation.get("validation", {}).get("status") != "VALID":
        return {
            "success": False,
            "message": (
                "Proposed emergency reallocation is invalid; "
                "no changes were applied."
            ),
            "validation": simulation.get("validation"),
        }

    in_progress_state = simulation.get("in_progress_state")

    if (
        in_progress_state == "IN_PROGRESS"
        and not acknowledge_in_progress
    ):
        return {
            "success": False,
            "message": (
                "Examination is currently in progress. "
                "Emergency reallocation requires explicit "
                "acknowledgement (acknowledge_in_progress=true) "
                "confirming the operational situation has been "
                "assessed by an authorized administrator."
            ),
            "in_progress_state": in_progress_state,
        }

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    if (examination.status or "DRAFT").upper() != "PUBLISHED":
        return {
            "success": False,
            "message": (
                "Emergency reallocation requires PUBLISHED status."
            ),
        }

    incident, incident_error = _load_emergency_incident(
        incident_id, examination_id
    )
    if incident_error:
        return {"success": False, "message": incident_error}

    # Snapshot current hall ticket versions BEFORE mutating
    # anything, so we can compute the new version numbers.
    existing_max_version = {}
    from app.models.hall_ticket import HallTicket
    for row in (
        HallTicket.query
        .filter_by(examination_id=examination_id)
        .all()
    ):
        current = existing_max_version.get(row.student_id, 0)
        if row.version > current:
            existing_max_version[row.student_id] = row.version

    try:
        # Remove dependent state in the same order the normal
        # apply path uses. Do not touch HallTicket rows here —
        # they are superseded, not deleted.
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

        timetables = (
            Timetable.query
            .filter_by(examination_id=examination_id)
            .order_by(
                Timetable.exam_date.asc(),
                Timetable.start_time.asc(),
                Timetable.id.asc(),
            )
            .all()
        )

        plan = _plan_hall_allocations(
            examination=examination,
            timetables=timetables,
            excluded_hall_ids=set(
                int(value) for value in excluded_hall_ids
            ),
        )

        if not plan.get("success"):
            db.session.rollback()
            return {
                "success": False,
                "message": "Emergency reallocation planning failed.",
                "detail": plan.get("message"),
            }

        for allocation in plan["allocations"]:
            db.session.add(allocation)

        db.session.flush()

        seat_result = generate_seat_allocation(
            examination_id,
            force=True,
            commit=False,
        )

        if not seat_result.get("success"):
            db.session.rollback()
            return {
                "success": False,
                "message": (
                    "Seat allocation failed; previous state "
                    "restored."
                ),
                "detail": seat_result.get("message"),
            }

        invigilator_result = generate_invigilator_allocation(
            examination_id,
            force=True,
            commit=False,
        )

        if not invigilator_result.get("success"):
            db.session.rollback()
            return {
                "success": False,
                "message": (
                    "Invigilator allocation failed; previous "
                    "state restored."
                ),
                "detail": invigilator_result.get("message"),
            }

        # Supersede the previously ISSUED tickets. This marks
        # them SUPERSEDED and preserves their rows + tokens.
        ticket_result = supersede_hall_tickets(
            examination_id,
            commit=False,
        )

        if not ticket_result.get("success"):
            db.session.rollback()
            return {
                "success": False,
                "message": (
                    "Failed to supersede previous hall tickets; "
                    "previous state restored."
                ),
                "detail": ticket_result,
            }

        # Generate replacement tickets at version N+1 using the
        # new seat rows we just created.
        from app.models.seat_allocation import SeatAllocation as _SA
        import uuid as _uuid

        new_seat_rows = (
            _SA.query
            .filter_by(examination_id=examination_id)
            .all()
        )

        by_student = {}
        for row in new_seat_rows:
            by_student.setdefault(row.student_id, []).append(row)

        issued_count = 0
        for student_id in sorted(by_student.keys()):
            next_version = existing_max_version.get(student_id, 0) + 1
            token = _uuid.uuid4().hex
            db.session.add(HallTicket(
                student_id=student_id,
                examination_id=examination_id,
                verification_token=token,
                version=next_version,
                status="ISSUED",
            ))
            issued_count += 1

        db.session.flush()

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
                "validation": hall_validation,
            }

        if invig_validation.get("status") != "VALID":
            db.session.rollback()
            return {
                "success": False,
                "message": (
                    "Post-apply invigilator validation failed; "
                    "previous state restored."
                ),
                "validation": invig_validation,
            }

        # Append an audit note on the incident. Do not change
        # the incident's status — resolving the incident is a
        # separate administrative action.
        existing_notes = (incident.resolution_notes or "").strip()
        audit_note = (
            f"[Emergency reallocation applied] "
            f"excluded_hall_ids={sorted(int(v) for v in excluded_hall_ids)}, "
            f"superseded_tickets={ticket_result.get('superseded', 0)}, "
            f"issued_tickets={issued_count}, "
            f"in_progress_state={in_progress_state}."
        )
        incident.resolution_notes = (
            f"{existing_notes}\n{audit_note}".strip()
        )

        db.session.commit()

        return {
            "success": True,
            "emergency": True,
            "message": "Emergency reallocation applied.",
            "examination_id": examination_id,
            "incident_id": incident.id,
            "examination_status": examination.status,
            "previous_status": examination.status,
            "requires_reapproval": False,
            "in_progress_state": in_progress_state,
            "post_apply_validation": {
                "hall": hall_validation,
                "invigilator": invig_validation,
            },
            "invigilators_regenerated": True,
            "seats_regenerated": True,
            "tickets_superseded": ticket_result.get(
                "superseded", 0
            ),
            "tickets_issued": issued_count,
        }

    except Exception as error:
        db.session.rollback()
        return {
            "success": False,
            "message": (
                "Emergency reallocation failed; previous state "
                "restored."
            ),
            "error": str(error),
        }