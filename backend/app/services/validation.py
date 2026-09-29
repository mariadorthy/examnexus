from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation

from app.services.eligibility import get_eligible_students


def validate_allocation(examination_id):

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "status": "INVALID",
            "message": "Examination not found",
            "allocated_students": 0,
            "unallocated_students": 0,
            "halls_used": 0
        }

    timetables = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time
        )
        .all()
    )

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    eligible_students = get_eligible_students(
        examination_id
    )

    eligible_count = len(eligible_students)

    accessibility_count = sum(
        1
        for student in eligible_students
        if getattr(student, "disability", False)
    )

    if not allocations:
        return {
            "status": "NOT GENERATED",
            "message": "Hall allocation has not been generated",
            "allocated_students": 0,
            "unallocated_students": eligible_count,
            "halls_used": 0,
            "allocated_capacity": 0
        }

    errors = []

    # ---------------------------------------------------------
    # CHECK TIMETABLE COVERAGE
    # ---------------------------------------------------------

    allocated_timetable_ids = {
        allocation.timetable_id
        for allocation in allocations
    }

    missing_timetables = [
        timetable.id
        for timetable in timetables
        if timetable.id not in allocated_timetable_ids
    ]

    if missing_timetables:
        errors.append(
            f"Missing hall allocation for timetable entries: "
            f"{missing_timetables}"
        )

    # ---------------------------------------------------------
    # CHECK EACH HALL ALLOCATION
    # ---------------------------------------------------------

    seen_timetable_halls = set()

    for allocation in allocations:

        hall = allocation.hall
        timetable = allocation.timetable

        if not hall:
            errors.append(
                f"Hall not found for allocation #{allocation.id}"
            )
            continue

        if not timetable:
            errors.append(
                f"Timetable not found for allocation #{allocation.id}"
            )
            continue

        # Hall must be usable
        if not hall.is_active:
            errors.append(
                f"Hall {hall.name} is inactive"
            )

        if not hall.is_available:
            errors.append(
                f"Hall {hall.name} is unavailable"
            )

        if hall.is_under_maintenance:
            errors.append(
                f"Hall {hall.name} is under maintenance"
            )

        if hall.examination_capacity <= 0:
            errors.append(
                f"Hall {hall.name} has no examination capacity"
            )

        # Allocated capacity must be valid
        if allocation.allocated_capacity <= 0:
            errors.append(
                f"Hall {hall.name} has invalid allocated capacity"
            )

        if (
            allocation.allocated_capacity
            > hall.examination_capacity
        ):
            errors.append(
                f"Hall {hall.name} exceeds examination capacity"
            )

        # Same hall cannot occur twice in same timetable
        key = (
            allocation.timetable_id,
            allocation.hall_id
        )

        if key in seen_timetable_halls:
            errors.append(
                f"Hall {hall.name} is duplicated for "
                f"timetable #{timetable.id}"
            )

        seen_timetable_halls.add(key)

    # ---------------------------------------------------------
    # CHECK HALL TIME CONFLICTS
    # ---------------------------------------------------------

    for index, first in enumerate(allocations):

        first_timetable = first.timetable

        if not first_timetable:
            continue

        for second in allocations[index + 1:]:

            if first.hall_id != second.hall_id:
                continue

            second_timetable = second.timetable

            if not second_timetable:
                continue

            if first.timetable_id == second.timetable_id:
                continue

            if (
                first_timetable.exam_date
                != second_timetable.exam_date
            ):
                continue

            if (
                first_timetable.start_time
                < second_timetable.end_time
                and first_timetable.end_time
                > second_timetable.start_time
            ):
                errors.append(
                    f"Hall {first.hall.name} has overlapping "
                    f"timetable allocations"
                )

    # ---------------------------------------------------------
    # CAPACITY CHECK PER TIMETABLE
    # ---------------------------------------------------------

    for timetable in timetables:

        timetable_allocations = [
            allocation
            for allocation in allocations
            if allocation.timetable_id == timetable.id
        ]

        allocated_capacity = sum(
            allocation.allocated_capacity
            for allocation in timetable_allocations
        )

        if allocated_capacity < eligible_count:
            errors.append(
                f"Insufficient capacity for "
                f"{timetable.exam_date} {timetable.session}: "
                f"{allocated_capacity}/{eligible_count}"
            )

        # -----------------------------------------------------
        # ACCESSIBILITY CAPACITY
        # -----------------------------------------------------

        accessibility_capacity = sum(
            allocation.allocated_capacity
            for allocation in timetable_allocations
            if (
                allocation.purpose in [
                    "ACCESSIBILITY",
                    "MIXED"
                ]
                and allocation.hall
                and allocation.hall.floor_no == 0
                and allocation.hall.is_accessible
            )
        )

        if accessibility_capacity < accessibility_count:
            errors.append(
                f"Insufficient accessibility capacity for "
                f"{timetable.exam_date} {timetable.session}: "
                f"{accessibility_capacity}/{accessibility_count}"
            )

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    allocated_capacity = sum(
        allocation.allocated_capacity
        for allocation in allocations
    )

    halls_used = len({
        allocation.hall_id
        for allocation in allocations
    })

    if errors:
        return {
            "status": "INVALID",
            "message": "Hall allocation validation failed",
            "errors": errors,
            "eligible_students": eligible_count,
            "allocated_capacity": allocated_capacity,
            "unallocated_students": max(
                0,
                eligible_count - allocated_capacity
            ),
            "halls_used": halls_used
        }

    return {
        "status": "VALID",
        "message": "Hall allocation is valid",
        "eligible_students": eligible_count,
        "allocated_capacity": allocated_capacity,
        "unallocated_students": 0,
        "halls_used": halls_used,
        "timetable_entries": len(timetables),
        "errors": []
    }