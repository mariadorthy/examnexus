from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation

from app.services.eligibility import get_eligible_students


def hall_conflicts(hall_id, timetable):
    """
    Check whether this hall is already allocated to another
    timetable entry on the same date with overlapping exam time.
    """

    existing_allocations = (
        HallAllocation.query
        .join(
            Timetable,
            HallAllocation.timetable_id == Timetable.id
        )
        .filter(
            HallAllocation.hall_id == hall_id,
            Timetable.exam_date == timetable.exam_date
        )
        .all()
    )

    for allocation in existing_allocations:
        existing_timetable = allocation.timetable

        if not existing_timetable:
            continue

        if (
            existing_timetable.start_time < timetable.end_time
            and existing_timetable.end_time > timetable.start_time
        ):
            return True

    return False


def get_available_halls(timetable):
    """
    Return halls that are usable and not occupied during
    the timetable's date/time.
    """

    halls = (
        Hall.query
        .filter(
            Hall.is_active.is_(True),
            Hall.is_available.is_(True),
            Hall.is_under_maintenance.is_(False),
            Hall.examination_capacity > 0
        )
        .order_by(
            Hall.examination_capacity.desc()
        )
        .all()
    )

    return [
        hall
        for hall in halls
        if not hall_conflicts(hall.id, timetable)
    ]


def generate_allocation(examination_id):
    """
    Generate Exam → Hall allocation for every timetable entry
    belonging to the examination.

    This stage does NOT allocate individual students or seats.
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
            "message": "No timetable entries found for this examination"
        }

    existing_allocation = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .first()
    )

    if existing_allocation:
        return {
            "success": False,
            "message": "Hall allocation already exists for this examination",
            "examination_id": examination_id
        }

    students = get_eligible_students(examination_id)

    if not students:
        return {
            "success": False,
            "message": "No eligible registered students found",
            "eligible_students": 0,
            "halls_used": 0
        }

    total_students = len(students)

    accessibility_students = [
        student
        for student in students
        if getattr(student, "disability", False)
    ]

    normal_students_count = (
        total_students - len(accessibility_students)
    )

    allocations = []

    try:
        for timetable in timetables:

            available_halls = get_available_halls(timetable)

            if not available_halls:
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        f"No available halls for "
                        f"{timetable.exam_date} {timetable.session}"
                    ),
                    "eligible_students": total_students,
                    "allocated_capacity": 0,
                    "shortage": total_students
                }

            # -------------------------------------------------
            # ACCESSIBILITY HALLS
            # -------------------------------------------------
            #
            # Floor 0 + accessible flag are used for students
            # requiring accessibility support.
            #

            accessibility_halls = [
                hall
                for hall in available_halls
                if hall.floor_no == 0 and hall.is_accessible
            ]

            accessibility_capacity = sum(
                hall.examination_capacity
                for hall in accessibility_halls
            )

            if len(accessibility_students) > accessibility_capacity:
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Insufficient accessible hall capacity"
                    ),
                    "exam_date": timetable.exam_date.isoformat(),
                    "session": timetable.session,
                    "eligible_students": total_students,
                    "students_requiring_accessibility": len(
                        accessibility_students
                    ),
                    "accessible_capacity": accessibility_capacity,
                    "shortage": (
                        len(accessibility_students)
                        - accessibility_capacity
                    )
                }

            total_available_capacity = sum(
                hall.examination_capacity
                for hall in available_halls
            )

            if total_students > total_available_capacity:
                db.session.rollback()

                return {
                    "success": False,
                    "message": "Insufficient hall capacity",
                    "exam_date": timetable.exam_date.isoformat(),
                    "session": timetable.session,
                    "eligible_students": total_students,
                    "available_capacity": total_available_capacity,
                    "shortage": (
                        total_students
                        - total_available_capacity
                    )
                }

            remaining_accessibility = len(
                accessibility_students
            )

            remaining_normal = normal_students_count

            used_hall_ids = set()

            # -------------------------------------------------
            # STEP 1: ALLOCATE ACCESSIBILITY REQUIREMENT
            # -------------------------------------------------

            for hall in accessibility_halls:

                if remaining_accessibility <= 0:
                    break

                if hall.id in used_hall_ids:
                    continue

                capacity = hall.examination_capacity

                accessibility_assigned = min(
                    capacity,
                    remaining_accessibility
                )

                remaining_accessibility -= accessibility_assigned

                # Use remaining capacity for normal students
                normal_assigned = min(
                    capacity - accessibility_assigned,
                    remaining_normal
                )

                remaining_normal -= normal_assigned

                allocated_capacity = (
                    accessibility_assigned
                    + normal_assigned
                )

                if allocated_capacity <= 0:
                    continue

                if normal_assigned > 0:
                    purpose = "MIXED"
                else:
                    purpose = "ACCESSIBILITY"

                allocations.append(
                    HallAllocation(
                        examination_id=examination.id,
                        timetable_id=timetable.id,
                        hall_id=hall.id,
                        allocated_capacity=allocated_capacity,
                        purpose=purpose,
                        status="GENERATED"
                    )
                )

                used_hall_ids.add(hall.id)

            # -------------------------------------------------
            # STEP 2: ALLOCATE NORMAL STUDENTS
            # -------------------------------------------------

            for hall in available_halls:

                if remaining_normal <= 0:
                    break

                if hall.id in used_hall_ids:
                    continue

                capacity = hall.examination_capacity

                normal_assigned = min(
                    capacity,
                    remaining_normal
                )

                if normal_assigned <= 0:
                    continue

                remaining_normal -= normal_assigned

                allocations.append(
                    HallAllocation(
                        examination_id=examination.id,
                        timetable_id=timetable.id,
                        hall_id=hall.id,
                        allocated_capacity=normal_assigned,
                        purpose="NORMAL",
                        status="GENERATED"
                    )
                )

                used_hall_ids.add(hall.id)

            # -------------------------------------------------
            # FINAL CAPACITY CHECK
            # -------------------------------------------------

            if (
                remaining_accessibility > 0
                or remaining_normal > 0
            ):
                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Unable to allocate sufficient "
                        "hall capacity"
                    ),
                    "exam_date": timetable.exam_date.isoformat(),
                    "session": timetable.session,
                    "eligible_students": total_students,
                    "unallocated_count": (
                        remaining_accessibility
                        + remaining_normal
                    )
                }

        # -----------------------------------------------------
        # SAVE ALL HALL ALLOCATIONS
        # -----------------------------------------------------

        db.session.add_all(allocations)
        db.session.commit()

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to generate hall allocation",
            "error": str(error)
        }

    total_allocated_capacity = sum(
        allocation.allocated_capacity
        for allocation in allocations
    )

    halls_used = len(
        {
            allocation.hall_id
            for allocation in allocations
        }
    )

    return {
        "success": True,
        "message": "Hall allocation generated successfully",
        "examination_id": examination.id,
        "eligible_students": total_students,
        "students_requiring_accessibility": len(
            accessibility_students
        ),
        "allocated_capacity": total_allocated_capacity,
        "unallocated_students": 0,
        "halls_used": halls_used,
        "timetable_entries": len(timetables),
        "allocation_records": len(allocations)
    }