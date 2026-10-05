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
    # FINAL HALL RESULT (aggregate)
    # ---------------------------------------------------------

    allocated_capacity = sum(
        allocation.allocated_capacity
        for allocation in allocations
    )

    halls_used = len({
        allocation.hall_id
        for allocation in allocations
    })

    # ---------------------------------------------------------
    # SEAT ALLOCATION COVERAGE
    # ---------------------------------------------------------

    from app.models.seat_allocation import SeatAllocation

    seat_rows = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    seat_by_timetable = {}

    for row in seat_rows:
        seat_by_timetable.setdefault(
            row.timetable_id, []
        ).append(row)

    for timetable in timetables:

        timetable_seats = seat_by_timetable.get(
            timetable.id, []
        )

        timetable_student_ids = {
            row.student_id for row in timetable_seats
        }

        expected_student_ids = {
            student.id for student in eligible_students
        }

        missing = expected_student_ids - timetable_student_ids

        if missing:
            errors.append(
                f"Missing seat for {len(missing)} student(s) "
                f"in timetable #{timetable.id}"
            )

        # Duplicate student seat within a timetable
        seen_students = set()
        for row in timetable_seats:
            if row.student_id in seen_students:
                errors.append(
                    f"Duplicate seat for student "
                    f"#{row.student_id} in timetable "
                    f"#{timetable.id}"
                )
            seen_students.add(row.student_id)

        # Duplicate seat number within a hall for the timetable
        seen_seats = set()
        for row in timetable_seats:
            key = (row.hall_id, row.seat_number)
            if key in seen_seats:
                errors.append(
                    f"Duplicate seat {row.seat_number} in "
                    f"hall #{row.hall_id} (timetable "
                    f"#{timetable.id})"
                )
            seen_seats.add(key)

        # Student must be seated in a hall allocated to this
        # timetable entry.
        timetable_hall_ids = {
            allocation.hall_id
            for allocation in allocations
            if allocation.timetable_id == timetable.id
        }

        # Student must be seated in a hall allocated to this
        # timetable entry.
        timetable_hall_ids = {
            allocation.hall_id
            for allocation in allocations
            if allocation.timetable_id == timetable.id
        }

        accessibility_student_ids = {
            student.id
            for student in eligible_students
            if getattr(student, "disability", False)
        }

        allocation_map = {
            allocation.hall_id: allocation
            for allocation in timetable_allocations
        }

        for row in timetable_seats:
            if row.hall_id not in timetable_hall_ids:
                errors.append(
                    f"Student #{row.student_id} seated in "
                    f"hall #{row.hall_id} not allocated to "
                    f"timetable #{timetable.id}"
                )
                continue

            # Accessibility students must always be seated in
            # accessible ground-floor halls.
            if row.student_id in accessibility_student_ids:
                hall = row.hall

                if (
                    hall is None
                    or not hall.is_accessible
                    or hall.floor_no != 0
                ):
                    errors.append(
                        f"Accessibility student #{row.student_id} "
                        f"is seated in a non-accessible hall "
                        f"for timetable #{timetable.id}"
                    )

        # -----------------------------------------------------
        # MIXED-COURSE SEATING VALIDATION
        # -----------------------------------------------------
        #
        # Validate each hall independently because the mixing
        # requirement applies to students sharing the same hall.
        timetable_hall_allocations = [
            allocation
            for allocation in allocations
            if allocation.timetable_id == timetable.id
        ]

        for allocation in timetable_hall_allocations:
            hall_seats = [
                row
                for row in timetable_seats
                if row.hall_id == allocation.hall_id
            ]

            mixing_error = _validate_course_mixing(
                hall_seats
            )

            if mixing_error:
                errors.append(
                    f"Hall #{allocation.hall_id}, "
                    f"timetable #{timetable.id}: "
                    f"{mixing_error}"
                )
    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    if errors:
        return {
            "status": "INVALID",
            "message": (
                "Hall and seat allocation validation failed"
            ),
            "errors": errors,
            "eligible_students": eligible_count,
            "allocated_capacity": allocated_capacity,
            "unallocated_students": max(
                0,
                eligible_count - allocated_capacity
            ),
            "halls_used": halls_used,
            "timetable_entries": len(timetables),
            "seat_records": len(seat_rows)
        }

    return {
        "status": "VALID",
        "message": "Hall and seat allocation is valid",
        "eligible_students": eligible_count,
        "allocated_capacity": allocated_capacity,
        "unallocated_students": 0,
        "halls_used": halls_used,
        "timetable_entries": len(timetables),
        "seat_records": len(seat_rows),
        "errors": []
    }

def validate_invigilator_allocation(examination_id):
    """
    Independent validation of invigilator allocations.

    Reads persisted InvigilatorAllocation rows and cross-checks them
    against HallAllocation, Timetable and Staff. Does NOT trust the
    generation result.
    """

    from app.models.invigilator_allocation import InvigilatorAllocation
    from app.models.staff import Staff

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "status": "INVALID",
            "errors": ["Examination not found"],
            "warnings": [],
            "invigilator_assignments": 0
        }

    hall_allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    invigilator_rows = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    errors = []
    warnings = []

    if not hall_allocations:
        return {
            "status": "INVALID",
            "errors": ["Hall allocation not found"],
            "warnings": [],
            "invigilator_assignments": 0
        }

    if not invigilator_rows:
        return {
            "status": "INVALID",
            "errors": ["Invigilator allocation has not been generated"],
            "warnings": [],
            "invigilator_assignments": 0
        }

    # ---------------------------------------------------------
    # Coverage check: every HallAllocation must be covered
    # ---------------------------------------------------------

    import math

    def _required(capacity):
        if capacity <= 0:
            return 1
        return max(1, math.ceil(capacity / 30))

    covered = {}

    for row in invigilator_rows:
        key = (row.timetable_id, row.hall_id)
        covered.setdefault(key, 0)
        covered[key] += 1

    for allocation in hall_allocations:
        key = (allocation.timetable_id, allocation.hall_id)
        required = _required(allocation.allocated_capacity)
        assigned = covered.get(key, 0)

        if assigned < required:
            errors.append(
                f"Hall allocation #{allocation.id} "
                f"(timetable #{allocation.timetable_id}, "
                f"hall #{allocation.hall_id}) has "
                f"{assigned}/{required} invigilators"
            )

    # ---------------------------------------------------------
    # Duplicate (timetable, hall, staff)
    # ---------------------------------------------------------

    seen = set()
    for row in invigilator_rows:
        key = (row.timetable_id, row.hall_id, row.staff_id)
        if key in seen:
            errors.append(
                f"Duplicate invigilator (staff #{row.staff_id}) "
                f"for timetable #{row.timetable_id} "
                f"hall #{row.hall_id}"
            )
        seen.add(key)

    # ---------------------------------------------------------
    # Staff validity
    # ---------------------------------------------------------

    staff_ids = {row.staff_id for row in invigilator_rows}
    staff_map = {
        s.id: s
        for s in Staff.query.filter(
            Staff.id.in_(list(staff_ids))
        ).all()
    } if staff_ids else {}

    for row in invigilator_rows:
        staff = staff_map.get(row.staff_id)

        if not staff:
            errors.append(
                f"Staff #{row.staff_id} not found"
            )
            continue

        if not staff.is_active:
            errors.append(
                f"Staff {staff.name} is inactive"
            )

        if not staff.availability:
            errors.append(
                f"Staff {staff.name} is not available"
            )

    # ---------------------------------------------------------
    # Cross-session conflict check
    # ---------------------------------------------------------

    by_staff = {}
    for row in invigilator_rows:
        by_staff.setdefault(row.staff_id, []).append(row)

    for staff_id, rows in by_staff.items():
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                ta = a.timetable
                tb = b.timetable

                if not ta or not tb:
                    continue

                if ta.id == tb.id:
                    continue

                if ta.exam_date != tb.exam_date:
                    continue

                if (
                    ta.start_time < tb.end_time
                    and ta.end_time > tb.start_time
                ):
                    errors.append(
                        f"Staff #{staff_id} is assigned to "
                        f"overlapping timetable entries "
                        f"#{ta.id} and #{tb.id}"
                    )

    if errors:
        return {
            "status": "INVALID",
            "errors": errors,
            "warnings": warnings,
            "invigilator_assignments": len(invigilator_rows)
        }

    return {
        "status": "VALID",
        "errors": [],
        "warnings": warnings,
        "invigilator_assignments": len(invigilator_rows),
        "distinct_staff": len(by_staff)
    }

def bulk_validate_examinations(examination_ids):
    """
    Read-only validation for multiple examinations.

    Reuses validate_allocation() and
    validate_invigilator_allocation() — does NOT create a third
    validation engine.
    """

    results = []

    for examination_id in examination_ids:

        hall_result = validate_allocation(examination_id)
        invig_result = validate_invigilator_allocation(
            examination_id
        )

        hall_status = hall_result.get(
            "status", "INVALID"
        )
        invig_status = invig_result.get(
            "status", "INVALID"
        )

        if hall_status == "NOT GENERATED":
            combined = "NOT GENERATED"

        elif (
            hall_status == "VALID"
            and invig_status == "VALID"
        ):
            combined = "VALID"

        else:
            combined = "INVALID"

        errors = []
        errors.extend(
            hall_result.get("errors", []) or []
        )
        errors.extend(
            invig_result.get("errors", []) or []
        )

        results.append({
            "examination_id": examination_id,
            "status": combined,
            "hall_status": hall_status,
            "invigilator_status": invig_status,
            "eligible_students": hall_result.get(
                "eligible_students", 0
            ),
            "allocated_capacity": hall_result.get(
                "allocated_capacity", 0
            ),
            "unallocated_students": hall_result.get(
                "unallocated_students", 0
            ),
            "seat_records": hall_result.get(
                "seat_records", 0
            ),
            "halls_used": hall_result.get(
                "halls_used", 0
            ),
            "invigilator_assignments": (
                invig_result.get(
                    "invigilator_assignments", 0
                )
            ),
            "errors": errors,
        })

    return {
        "success": True,
        "processed": len(results),
        "results": results,
    }

def _validate_course_mixing(seats):
    """
    Validate that multiple courses in the same hall are
    reasonably distributed rather than placed in one block.

    For two courses:
        30/30 -> maximum same-course run = 1
        40/20 -> maximum same-course run = 2
        50/10 -> maximum same-course run = 5

    A perfectly alternating pattern is only possible when
    course counts are equal.
    """
    if len(seats) < 2:
        return None

    ordered_seats = sorted(
        seats,
        key=lambda seat: (
            seat.seat_index
            if seat.seat_index is not None
            else 0,
            seat.id,
        ),
    )

    course_sequence = []

    for seat in ordered_seats:
        student = seat.student

        if student is None:
            continue

        course_id = (
            student.course.id
            if student.course is not None
            else None
        )

        course_sequence.append(course_id)

    distinct_courses = {
        course_id
        for course_id in course_sequence
    }

    # No mixing requirement for a single course.
    if len(distinct_courses) <= 1:
        return None

    # The current requirement is primarily two-course mixing.
    if len(distinct_courses) != 2:
        return None

    counts = {}

    for course_id in course_sequence:
        counts[course_id] = counts.get(course_id, 0) + 1

    values = sorted(counts.values())

    smaller_count = values[0]
    larger_count = values[1]

    if smaller_count == 0:
        return None

    allowed_max_run = (
        (larger_count + smaller_count - 1)
        // smaller_count
    )

    max_run = 1
    current_run = 1

    for index in range(1, len(course_sequence)):
        if course_sequence[index] == course_sequence[index - 1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    if max_run > allowed_max_run:
        return (
            "Mixed-course seating is insufficiently distributed: "
            f"maximum consecutive same-course seats={max_run}, "
            f"allowed={allowed_max_run}"
        )

    return None