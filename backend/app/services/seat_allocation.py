"""
Seat allocation service.

Operates on top of HallAllocation records. For each timetable entry,
distributes eligible students across the halls already allocated to
that timetable entry, and assigns deterministic seat numbers.
"""

from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation

from app.services.eligibility import get_eligible_students


SEATS_PER_ROW = 10


def _row_label(index):
    """
    Convert a 0-based row index into A, B, C, ..., Z, AA, AB, ...
    """

    label = ""
    index += 1

    while index > 0:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label

    return label


def _seat_number(row_index, seat_index):
    """
    Human-readable seat number, e.g. A-01, A-10, B-01.
    """

    return f"{_row_label(row_index)}-{seat_index:02d}"


def _generate_seat_sequence(allocated_capacity):
    """
    Produce a deterministic sequence of (seat_number, row_label,
    seat_index) tuples for a hall with the given allocated capacity.
    """

    seats = []

    for position in range(allocated_capacity):
        row_index = position // SEATS_PER_ROW
        seat_index = (position % SEATS_PER_ROW) + 1

        seats.append(
            (
                _seat_number(row_index, seat_index),
                _row_label(row_index),
                seat_index
            )
        )

    return seats


def _ordered_students(students):
    """
    Deterministic student ordering. Sort by student_id string
    ascending, falling back to numeric id.
    """

    return sorted(
        students,
        key=lambda student: (
            str(getattr(student, "student_id", "")),
            student.id
        )
    )


def _course_key(student):
    """
    Return a stable course identifier for seating distribution.

    Student.course is already the normalized relationship used
    by the current data model, so no duplicate course data is
    stored in SeatAllocation.
    """
    if student.course is None:
        return ("UNKNOWN",)

    return (
        student.course.id,
        str(student.course.course_code or ""),
    )


def _mixed_course_order(students):
    """
    Distribute students from different courses across the hall.

    Examples:
        30 A + 30 B -> A B A B A B ...
        40 A + 20 B -> A A B A A B A A B ...

    The algorithm remains deterministic because each course group
    is ordered using the existing student ordering.
    """
    ordered = _ordered_students(students)

    course_groups = {}

    for student in ordered:
        key = _course_key(student)
        course_groups.setdefault(key, []).append(student)

    # A single course does not need special treatment.
    if len(course_groups) <= 1:
        return ordered

    # Sort course groups deterministically:
    # larger groups first, then stable course key.
    groups = sorted(
        course_groups.values(),
        key=lambda group: (
            -len(group),
            _course_key(group[0]),
        ),
    )

    # The main requirement is two-course mixing.
    # For more than two courses, use deterministic round-robin
    # distribution across the available course groups.
    if len(groups) == 2:
        larger = groups[0]
        smaller = groups[1]

        result = []
        smaller_index = 0
        smaller_count = len(smaller)
        larger_count = len(larger)

        for index, student in enumerate(larger):
            result.append(student)

            # Evenly distribute the smaller course through
            # the larger course.
            target_count = (
                (index + 1) * smaller_count
            ) // larger_count

            while smaller_index < target_count:
                result.append(smaller[smaller_index])
                smaller_index += 1

        while smaller_index < smaller_count:
            result.append(smaller[smaller_index])
            smaller_index += 1

        return result

    # Generic deterministic distribution for 3+ courses.
    result = []

    while any(groups):
        for group in groups:
            if group:
                result.append(group.pop(0))

    return result

def _split_students(students):
    """
    Split students into accessibility-required and normal groups,
    both deterministically ordered.
    """

    accessibility = []
    normal = []

    for student in students:
        disability = getattr(student, "disability", None)

        if isinstance(disability, str):
            has_disability = bool(disability.strip())
        else:
            has_disability = bool(disability)

        if has_disability:
            accessibility.append(student)
        else:
            normal.append(student)

    return (
        _ordered_students(accessibility),
        _ordered_students(normal)
    )


def _is_accessible_hall(hall):
    return (
        hall.is_accessible
        and hall.floor_no == 0
    )


def generate_seat_allocation(examination_id, force=False):
    """
    Generate seat allocation for every timetable entry of the
    examination, using the existing HallAllocation records.

    If force=True, existing seat allocations for this examination
    are deleted first. Existing hall allocations are NOT touched.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
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
            "message": (
                "No timetable entries found for this examination"
            )
        }

    hall_allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    if not hall_allocations:
        return {
            "success": False,
            "message": (
                "Hall allocation must be generated before "
                "seat allocation"
            )
        }

    # ---------------------------------------------------------
    # EXISTING SEAT ALLOCATIONS
    # ---------------------------------------------------------

    existing_seat_count = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .count()
    )

    if existing_seat_count > 0 and not force:
        return {
            "success": False,
            "message": (
                "Seat allocation already exists for this "
                "examination. Use force=true to regenerate."
            ),
            "existing_seat_allocations": existing_seat_count
        }

    students = get_eligible_students(examination_id)

    if not students:
        return {
            "success": False,
            "message": "No eligible registered students found",
            "eligible_students": 0
        }

    accessibility_students, normal_students = _split_students(
        students
    )

    # ---------------------------------------------------------
    # BUILD SEAT RECORDS (IN MEMORY)
    # ---------------------------------------------------------

    seat_records = []
    per_timetable_summary = []

    try:
        for timetable in timetables:

            timetable_allocations = [
                allocation
                for allocation in hall_allocations
                if allocation.timetable_id == timetable.id
            ]

            if not timetable_allocations:
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Missing hall allocation for "
                        f"timetable #{timetable.id}"
                    ),
                    "timetable_id": timetable.id
                }

            total_allocated_capacity = sum(
                allocation.allocated_capacity
                for allocation in timetable_allocations
            )

            total_needed = len(students)

            if total_allocated_capacity < total_needed:
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Allocated hall capacity is less than "
                        "the number of eligible students"
                    ),
                    "timetable_id": timetable.id,
                    "eligible_students": total_needed,
                    "allocated_capacity": total_allocated_capacity,
                    "shortage": (
                        total_needed - total_allocated_capacity
                    )
                }

            # -------------------------------------------------
            # SORT ALLOCATIONS: accessibility-first, then largest
            # -------------------------------------------------

            ordered_allocations = sorted(
                timetable_allocations,
                key=lambda allocation: (
                    0
                    if allocation.purpose in (
                        "ACCESSIBILITY",
                        "MIXED"
                    )
                    else 1,
                    -allocation.allocated_capacity,
                    allocation.id
                )
            )

            remaining_accessibility = list(
                accessibility_students
            )
            remaining_normal = list(normal_students)

            timetable_seats = []

            for allocation in ordered_allocations:

                hall = allocation.hall

                if not hall:
                    db.session.rollback()

                    return {
                        "success": False,
                        "message": (
                            "Hall missing for allocation "
                            f"#{allocation.id}"
                        )
                    }

                is_accessible = _is_accessible_hall(hall)

                students_for_this_hall = []

                if is_accessible and remaining_accessibility:
                    take = min(
                        allocation.allocated_capacity,
                        len(remaining_accessibility)
                    )

                    students_for_this_hall.extend(
                        remaining_accessibility[:take]
                    )

                    del remaining_accessibility[:take]

                space_left = (
                    allocation.allocated_capacity
                    - len(students_for_this_hall)
                )

                if space_left > 0 and remaining_normal:
                    take = min(
                        space_left,
                        len(remaining_normal)
                    )

                    students_for_this_hall.extend(
                        remaining_normal[:take]
                    )

                    del remaining_normal[:take]

                # Any remaining accessibility students may also
                # be seated here if this is a normal hall with
                # space (last resort, should not happen given
                # the earlier validation).
                space_left = (
                    allocation.allocated_capacity
                    - len(students_for_this_hall)
                )

                if space_left > 0 and remaining_accessibility:
                    take = min(
                        space_left,
                        len(remaining_accessibility)
                    )

                    students_for_this_hall.extend(
                        remaining_accessibility[:take]
                    )

                    del remaining_accessibility[:take]

                # ---------------------------------------------------------
                # MIXED-COURSE SEAT DISTRIBUTION
                # ---------------------------------------------------------
                #
                # Hall allocation is already complete at this point.
                # Accessibility and capacity rules have already been handled.
                #
                # Only the physical seat ordering is changed here.
                students_for_this_hall = _mixed_course_order(
                    students_for_this_hall
                )

                seats = _generate_seat_sequence(
                    len(students_for_this_hall)
                )

                for student, (seat_number, row_label, seat_index) \
                        in zip(students_for_this_hall, seats):
                        
                    record = SeatAllocation(
                        examination_id=examination.id,
                        timetable_id=timetable.id,
                        hall_allocation_id=allocation.id,
                        hall_id=hall.id,
                        student_id=student.id,
                        seat_number=seat_number,
                        row_label=row_label,
                        seat_index=seat_index,
                        status="GENERATED"
                    )

                    seat_records.append(record)
                    timetable_seats.append(record)

            if remaining_accessibility or remaining_normal:
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Unable to seat every student for "
                        f"timetable #{timetable.id}"
                    ),
                    "timetable_id": timetable.id,
                    "unseated_accessibility": len(
                        remaining_accessibility
                    ),
                    "unseated_normal": len(remaining_normal)
                }

            per_timetable_summary.append(
                {
                    "timetable_id": timetable.id,
                    "exam_date": timetable.exam_date.isoformat(),
                    "session": timetable.session,
                    "halls": len(timetable_allocations),
                    "students_seated": len(timetable_seats)
                }
            )

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to build seat allocation",
            "error": str(error)
        }

    # ---------------------------------------------------------
    # PERSIST
    # ---------------------------------------------------------

    try:
        if force and existing_seat_count > 0:
            (
                SeatAllocation.query
                .filter_by(examination_id=examination_id)
                .delete(synchronize_session=False)
            )

        db.session.add_all(seat_records)
        db.session.commit()

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to save seat allocation",
            "error": str(error)
        }

    return {
        "success": True,
        "message": "Seat allocation generated successfully",
        "examination_id": examination.id,
        "eligible_students": len(students),
        "accessibility_students": len(accessibility_students),
        "timetable_entries": len(timetables),
        "seat_records": len(seat_records),
        "regenerated": bool(force and existing_seat_count > 0),
        "timetables": per_timetable_summary
    }


def clear_seat_allocation(examination_id):
    """
    Delete all seat allocations for an examination.
    """

    deleted = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .delete(synchronize_session=False)
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Seat allocation cleared",
        "deleted": deleted
    }


def get_seat_allocations(examination_id):
    """
    Return seat allocations for the examination, joined with
    timetable + hall + student, ordered deterministically.
    """

    rows = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .join(Timetable, SeatAllocation.timetable_id == Timetable.id)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
            SeatAllocation.hall_id,
            SeatAllocation.row_label,
            SeatAllocation.seat_index
        )
        .all()
    )

    result = []

    for row in rows:
        result.append(
            {
                "id": row.id,
                "examination_id": row.examination_id,
                "timetable_id": row.timetable_id,
                "exam_date": (
                    row.timetable.exam_date.isoformat()
                    if row.timetable else None
                ),
                "session": (
                    row.timetable.session
                    if row.timetable else None
                ),
                "hall_id": row.hall_id,
                "hall": row.hall.name if row.hall else None,
                "building_name": (
                    row.hall.building_name if row.hall else None
                ),
                "floor_no": (
                    row.hall.floor_no if row.hall else None
                ),
                "purpose": (
                    row.hall_allocation.purpose
                    if row.hall_allocation else None
                ),
                "student_id": row.student_id,
                "student_code": (
                    row.student.student_id
                    if row.student else None
                ),
                "course_id": (
                    row.student.course.id
                    if row.student and row.student.course
                    else None
                ),
                "course_code": (
                    row.student.course.course_code
                    if row.student and row.student.course
                    else None
                ),
                "course_name": (
                    row.student.course.course_name
                    if row.student and row.student.course
                    else None
                ),
                "course_abbreviation": (
                    row.student.course.course_abbreviation
                    if row.student and row.student.course
                    else None
                ),
                "student_name": (
                    row.student.name if row.student else None
                ),
                "seat_number": row.seat_number,
                "row_label": row.row_label,
                "seat_index": row.seat_index,
                "status": row.status
            }
        )

    return result


def get_hall_seating(hall_allocation_id):
    """
    Return the seat map for a single HallAllocation.
    """

    allocation = HallAllocation.query.get(hall_allocation_id)

    if not allocation:
        return {
            "success": False,
            "message": "Hall allocation not found"
        }

    rows = (
        SeatAllocation.query
        .filter_by(hall_allocation_id=hall_allocation_id)
        .order_by(
            SeatAllocation.row_label,
            SeatAllocation.seat_index
        )
        .all()
    )

    seats = [
        {
            "seat_number": row.seat_number,
            "row_label": row.row_label,
            "seat_index": row.seat_index,
            "student_id": row.student_id,
            "student_code": (
                row.student.student_id if row.student else None
            ),
            "student_name": (
                row.student.name if row.student else None
            ),
            "course_id": (
                row.student.course.id
                if row.student and row.student.course
                else None
            ),
            "course_code": (
                row.student.course.course_code
                if row.student and row.student.course
                else None
            ),
            "course_name": (
                row.student.course.course_name
                if row.student and row.student.course
                else None
            ),
            "course_abbreviation": (
                row.student.course.course_abbreviation
                if row.student and row.student.course
                else None
            ),
            "status": row.status
        }
        for row in rows
    ]

    return {
        "success": True,
        "hall_allocation_id": hall_allocation_id,
        "hall_id": allocation.hall_id,
        "hall_name": allocation.hall.name if allocation.hall else None,
        "allocated_capacity": allocation.allocated_capacity,
        "seats_used": len(seats),
        "seats": seats
    }

def generate_bulk_seat_allocation(
    examination_ids,
    force=False
):
    """
    Generate seat allocation for multiple examinations.

    Non-atomic by design: each examination is processed
    independently through the existing single-examination
    service. One failure does not roll back the others.

    Reuses generate_seat_allocation() — does NOT duplicate the
    seat allocation algorithm.
    """

    results = []

    for examination_id in examination_ids:

        single_result = generate_seat_allocation(
            examination_id,
            force=force
        )

        if single_result.get("success"):

            results.append({
                "examination_id": examination_id,
                "status": "GENERATED",
                "seat_records": single_result.get(
                    "seat_records", 0
                ),
                "eligible_students": single_result.get(
                    "eligible_students", 0
                ),
                "regenerated": single_result.get(
                    "regenerated", False
                ),
            })

        else:

            results.append({
                "examination_id": examination_id,
                "status": "FAILED",
                "message": single_result.get(
                    "message", "Seat allocation failed"
                ),
            })

    any_success = any(
        r["status"] == "GENERATED" for r in results
    )

    return {
        "success": any_success,
        "processed": len(results),
        "results": results,
    }