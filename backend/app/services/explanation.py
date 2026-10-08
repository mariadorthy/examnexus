"""
Feature 20 — Explainable Allocation.

Read-only projection over the EXISTING deterministic allocator
(services/allocation.py) and validation layer
(services/validation.py).

Hard rules:
  - Never writes to the database.
  - Never re-evaluates constraints with a different rule than
    the allocator itself.
  - Emits only reason codes from the closed enum below.
  - Reason ordering is deterministic.
"""
from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation

from app.services.eligibility import get_eligible_students
from app.services.allocation import hall_conflicts


# Closed enum of every reason code this service may emit.
REASON_CODES = frozenset({
    # selected
    "HALL_ACTIVE",
    "HALL_AVAILABLE",
    "NOT_UNDER_MAINTENANCE",
    "HAS_EXAM_CAPACITY",
    "NO_TIMETABLE_CONFLICT",
    "ACCESSIBILITY_SUITABLE",
    "SELECTED_BY_ALLOCATOR_STRATEGY",
    "PURPOSE_NORMAL",
    "PURPOSE_ACCESSIBILITY",
    "PURPOSE_MIXED",
    # rejected
    "REJECTED_INACTIVE",
    "REJECTED_UNAVAILABLE",
    "REJECTED_MAINTENANCE",
    "REJECTED_NO_EXAM_CAPACITY",
    "REJECTED_TIMETABLE_CONFLICT",
    "REJECTED_TRANSIENTLY_EXCLUDED",
    "REJECTED_NO_REMAINING_CAPACITY",
    # aggregate
    "AGGREGATE_INSUFFICIENT_TOTAL_CAPACITY",
    "AGGREGATE_INSUFFICIENT_ACCESSIBLE_CAPACITY",
    "AGGREGATE_NO_AVAILABLE_HALLS",
})

def _r(code, message):
    return {"code": code, "message": message}


def _selected_reasons(hall, timetable, allocation, excluded=None):
    """
    Reasons a hall was chosen. Read-only. Uses the SAME
    predicates the allocator uses (is_active, is_available,
    is_under_maintenance, examination_capacity > 0,
    hall_conflicts()).
    """
    reasons = []

    if hall.is_active:
        reasons.append(_r("HALL_ACTIVE", "Hall is active"))

    if hall.is_available:
        reasons.append(
            _r("HALL_AVAILABLE",
               "Hall is available for the examination session")
        )

    if not hall.is_under_maintenance:
        reasons.append(
            _r("NOT_UNDER_MAINTENANCE",
               "Hall is not under maintenance")
        )

    if hall.examination_capacity > 0:
        reasons.append(
            _r("HAS_EXAM_CAPACITY",
               f"Hall has examination capacity "
               f"{hall.examination_capacity}")
        )

    if not hall_conflicts(
        hall.id,
        timetable,
        excluded_hall_ids=excluded,
        ignore_examination_id=allocation.examination_id,
    ):
        reasons.append(
            _r("NO_TIMETABLE_CONFLICT",
               "No overlapping timetable allocation for this hall")
        )

    if allocation.purpose in ("ACCESSIBILITY", "MIXED"):
        if hall.is_accessible and hall.floor_no == 0:
            reasons.append(
                _r("ACCESSIBILITY_SUITABLE",
                   "Ground-floor accessible hall for "
                   "accessibility students")
            )

    # The deterministic allocator uses different capacity-based
    # strategies depending on the entry point (interactive
    # planner is smallest-fit-first with largest fallback;
    # bulk planner is largest-fit-first). Report the general
    # deterministic-strategy fact rather than claiming a
    # specific minimization that may not apply.
    reasons.append(
        _r(
            "SELECTED_BY_ALLOCATOR_STRATEGY",
            "Selected by the deterministic hall allocation strategy."
        )
    )
    purpose = (allocation.purpose or "NORMAL").upper()
    if purpose == "NORMAL":
        reasons.append(_r("PURPOSE_NORMAL", "Allocated for normal seating"))
    elif purpose == "ACCESSIBILITY":
        reasons.append(
            _r("PURPOSE_ACCESSIBILITY",
               "Allocated for accessibility seating")
        )
    elif purpose == "MIXED":
        reasons.append(
            _r("PURPOSE_MIXED",
               "Allocated for mixed normal + accessibility seating")
        )

    reasons.sort(key=lambda item: item["code"])
    return reasons


def _rejected_reasons(hall, timetable, examination_id, excluded=None):
    """
    Reasons a hall was NOT selected for a given timetable.
    Uses the same predicates the allocator uses.
    """
    reasons = []

    if not hall.is_active:
        reasons.append(_r("REJECTED_INACTIVE", "Hall is inactive"))

    if not hall.is_available:
        reasons.append(
            _r("REJECTED_UNAVAILABLE",
               "Hall is unavailable for this examination session")
        )

    if hall.is_under_maintenance:
        reasons.append(
            _r("REJECTED_MAINTENANCE", "Hall is under maintenance")
        )

    if hall.examination_capacity <= 0:
        reasons.append(
            _r("REJECTED_NO_EXAM_CAPACITY",
               "Hall has no examination capacity")
        )

    if excluded and hall.id in excluded:
        reasons.append(
            _r("REJECTED_TRANSIENTLY_EXCLUDED",
               "Hall was excluded for this operation")
        )

    if hall_conflicts(
        hall.id,
        timetable,
        excluded_hall_ids=excluded,
        ignore_examination_id=examination_id,
    ):
        reasons.append(
            _r("REJECTED_TIMETABLE_CONFLICT",
               "Hall is already allocated to an overlapping "
               "examination session")
        )

    # Hall passed every hard gate but was simply not needed
    # (smallest-fit-first selected other halls instead).
    if not reasons:
        reasons.append(
            _r("REJECTED_NO_REMAINING_CAPACITY",
               "Hall has sufficient capacity but was not needed "
               "after the smallest-fit-first selection")
        )

    reasons.sort(key=lambda item: item["code"])
    return reasons


def explain_hall_decision(
    examination_id,
    hall_id,
    timetable_id,
    excluded_hall_ids=None,
):
    """
    Explain the decision for a single (hall, timetable) pair.

    If the pair exists as a HallAllocation → SELECTED with
    selection reasons. Otherwise → REJECTED with rejection
    reasons computed from the SAME predicates the allocator
    uses.
    """
    examination = Examination.query.get(examination_id)
    if not examination:
        return {"success": False, "message": "Examination not found"}

    timetable = Timetable.query.get(timetable_id)
    if not timetable or timetable.examination_id != examination_id:
        return {
            "success": False,
            "message": "Timetable entry not found for this examination",
        }

    hall = Hall.query.get(hall_id)
    if not hall:
        return {"success": False, "message": "Hall not found"}

    excluded = None
    if excluded_hall_ids:
        try:
            excluded = {int(x) for x in excluded_hall_ids}
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "excluded_hall_ids must be integers",
            }

    allocation = (
        HallAllocation.query
        .filter_by(
            examination_id=examination_id,
            timetable_id=timetable_id,
            hall_id=hall_id,
        )
        .first()
    )

    if allocation:
        return {
            "success": True,
            "hall_id": hall.id,
            "hall": hall.name,
            "timetable_id": timetable.id,
            "exam_date": timetable.exam_date.isoformat(),
            "session": timetable.session,
            "decision": "SELECTED",
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
            "reasons": _selected_reasons(
                hall, timetable, allocation, excluded=excluded
            ),
        }

    return {
        "success": True,
        "hall_id": hall.id,
        "hall": hall.name,
        "timetable_id": timetable.id,
        "exam_date": timetable.exam_date.isoformat(),
        "session": timetable.session,
        "decision": "REJECTED",
        "allocated_capacity": 0,
        "purpose": None,
        "reasons": _rejected_reasons(
            hall, timetable, examination_id, excluded=excluded
        ),
    }


def explain_allocation(examination_id, excluded_hall_ids=None):
    """
    Explain every persisted HallAllocation, plus rejected
    alternatives per timetable. Read-only.
    """
    examination = Examination.query.get(examination_id)
    if not examination:
        return {"success": False, "message": "Examination not found"}

    excluded = None
    if excluded_hall_ids:
        try:
            excluded = {int(x) for x in excluded_hall_ids}
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "excluded_hall_ids must be integers",
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

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    if not allocations:
        return {
            "success": False,
            "message": "Hall allocation has not been generated",
            "examination_id": examination_id,
        }

    selected = []
    for allocation in allocations:
        hall = allocation.hall
        timetable = allocation.timetable
        if not hall or not timetable:
            continue
        selected.append({
            "hall_id": hall.id,
            "hall": hall.name,
            "timetable_id": timetable.id,
            "exam_date": timetable.exam_date.isoformat(),
            "session": timetable.session,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
            "decision": "SELECTED",
            "reasons": _selected_reasons(
                hall, timetable, allocation, excluded=excluded
            ),
        })

    selected.sort(key=lambda r: (r["timetable_id"], r["hall_id"]))

    selected_keys = {
        (row["timetable_id"], row["hall_id"])
        for row in selected
    }

    rejected = []
    for timetable in timetables:
        for hall in Hall.query.order_by(Hall.id).all():
            key = (timetable.id, hall.id)
            if key in selected_keys:
                continue
            rejected.append({
                "hall_id": hall.id,
                "hall": hall.name,
                "timetable_id": timetable.id,
                "exam_date": timetable.exam_date.isoformat(),
                "session": timetable.session,
                "allocated_capacity": 0,
                "purpose": None,
                "decision": "REJECTED",
                "reasons": _rejected_reasons(
                    hall, timetable, examination_id,
                    excluded=excluded,
                ),
            })

    rejected.sort(key=lambda r: (r["timetable_id"], r["hall_id"]))

    # Aggregate reasons per timetable (capacity shortfalls,
    # if any), computed from the SAME eligibility helper the
    # allocator uses.
    aggregate = []
    eligible = get_eligible_students(examination_id)
    eligible_count = len(eligible)
    accessibility_count = sum(
        1 for s in eligible if getattr(s, "disability", False)
    )

    for timetable in timetables:
        rows = [r for r in selected if r["timetable_id"] == timetable.id]
        total_capacity = sum(r["allocated_capacity"] for r in rows)

        accessible_capacity = 0
        for r in rows:
            hall = Hall.query.get(r["hall_id"])
            if (
                hall
                and hall.is_accessible
                and hall.floor_no == 0
                and hall.is_active
                and hall.is_available
                and not hall.is_under_maintenance
            ):
                accessible_capacity += r["allocated_capacity"]

        reasons = []

        if total_capacity < eligible_count:
            reasons.append(_r(
                "AGGREGATE_INSUFFICIENT_TOTAL_CAPACITY",
                f"Allocated capacity {total_capacity} < "
                f"eligible students {eligible_count}",
            ))

        if accessible_capacity < accessibility_count:
            reasons.append(_r(
                "AGGREGATE_INSUFFICIENT_ACCESSIBLE_CAPACITY",
                f"Accessible capacity {accessible_capacity} < "
                f"accessibility students {accessibility_count}",
            ))

        if not rows:
            reasons.append(_r(
                "AGGREGATE_NO_AVAILABLE_HALLS",
                "No hall allocation exists for this timetable entry",
            ))

        reasons.sort(key=lambda item: item["code"])
        if reasons:
            aggregate.append({
                "timetable_id": timetable.id,
                "exam_date": timetable.exam_date.isoformat(),
                "session": timetable.session,
                "reasons": reasons,
            })

    return {
        "success": True,
        "examination_id": examination_id,
        "selected": selected,
        "rejected": rejected,
        "aggregate": aggregate,
        "reason_codes": sorted(REASON_CODES),
    }