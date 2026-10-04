from datetime import datetime

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


def generate_allocation(examination_id, force=False):
    """
    Generate Exam → Hall allocation for every timetable entry
    belonging to the examination, then generate seat allocation.

    If force=True, existing hall + seat allocations for this
    examination are cleared before regeneration.
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

        if not force:
            return {
                "success": False,
                "message": (
                    "Hall allocation already exists for this "
                    "examination. Use force=true to regenerate."
                ),
                "examination_id": examination_id
            }

        # Transactional cleanup of dependent seat allocations
        # first, then the hall allocations themselves.
        from app.models.seat_allocation import SeatAllocation

        try:
            (
                SeatAllocation.query
                .filter_by(examination_id=examination_id)
                .delete(synchronize_session=False)
            )

            (
                HallAllocation.query
                .filter_by(examination_id=examination_id)
                .delete(synchronize_session=False)
            )

            db.session.commit()

        except Exception as error:
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    "Failed to clear previous allocation for "
                    "regeneration"
                ),
                "error": str(error)
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

    # ---------------------------------------------------------
    # SEAT ALLOCATION (integrated)
    # ---------------------------------------------------------

    from app.services.seat_allocation import (
        generate_seat_allocation
    )

    seat_result = generate_seat_allocation(
        examination_id=examination.id,
        force=True
    )

    if not seat_result.get("success"):
        return {
            "success": False,
            "message": (
                "Hall allocation succeeded but seat "
                "allocation failed"
            ),
            "hall_allocation": {
                "eligible_students": total_students,
                "allocated_capacity": total_allocated_capacity,
                "halls_used": halls_used
            },
            "seat_allocation": seat_result
        }

    return {
        "success": True,
        "message": (
            "Hall and seat allocation generated successfully"
        ),
        "examination_id": examination.id,
        "eligible_students": total_students,
        "students_requiring_accessibility": len(
            accessibility_students
        ),
        "allocated_capacity": total_allocated_capacity,
        "unallocated_students": 0,
        "halls_used": halls_used,
        "timetable_entries": len(timetables),
        "allocation_records": len(allocations),
        "seat_records": seat_result.get("seat_records", 0),
        "regenerated": bool(force)
    }

def update_hall_allocation(
    allocation_id,
    hall_id=None,
    allocated_capacity=None,
    purpose=None
):
    """
    Update an existing Exam → Hall allocation.

    Only hall, allocated capacity and purpose can be edited.
    Examination and timetable relationships remain unchanged.
    """

    allocation = HallAllocation.query.get(allocation_id)

    if not allocation:
        return {
            "success": False,
            "message": "Hall allocation not found."
        }

    hall = None

    if hall_id is not None:
        try:
            hall_id = int(hall_id)
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "Invalid hall ID."
            }

        hall = Hall.query.get(hall_id)

        if not hall:
            return {
                "success": False,
                "message": "Selected hall not found."
            }

        if not hall.is_active:
            return {
                "success": False,
                "message": "Selected hall is inactive."
            }

        if not hall.is_available:
            return {
                "success": False,
                "message": "Selected hall is currently unavailable."
            }

        if hall.is_under_maintenance:
            return {
                "success": False,
                "message": "Selected hall is under maintenance."
            }

    else:
        hall = allocation.hall

    if not hall:
        return {
            "success": False,
            "message": "Hall information is unavailable."
        }

    if allocated_capacity is not None:
        try:
            allocated_capacity = int(allocated_capacity)
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "Allocated capacity must be a number."
            }

        if allocated_capacity <= 0:
            return {
                "success": False,
                "message": "Allocated capacity must be greater than zero."
            }

        if allocated_capacity > hall.examination_capacity:
            return {
                "success": False,
                "message": (
                    "Allocated capacity cannot exceed the "
                    "hall examination capacity."
                ),
                "hall_capacity": hall.examination_capacity,
                "requested_capacity": allocated_capacity
            }

    else:
        allocated_capacity = allocation.allocated_capacity

        if allocated_capacity > hall.examination_capacity:
            return {
                "success": False,
                "message": (
                    "Existing allocated capacity exceeds "
                    "the selected hall capacity. Please "
                    "provide a new allocated_capacity."
                ),
                "hall_capacity": hall.examination_capacity,
                "allocated_capacity": allocated_capacity
            }

      # ---------------------------------------------------------
    # CHECK UNIQUE (timetable_id, hall_id)
    # ---------------------------------------------------------

    duplicate = (
        HallAllocation.query
        .filter(
            HallAllocation.timetable_id == allocation.timetable_id,
            HallAllocation.hall_id == hall.id,
            HallAllocation.id != allocation.id
        )
        .first()
    )

    if duplicate:
        return {
            "success": False,
            "message": (
                "This hall is already allocated to the "
                "same timetable entry."
            )
        }

    # ---------------------------------------------------------
    # CHECK HALL CONFLICT
    # ---------------------------------------------------------

    timetable = allocation.timetable

    if not timetable:
        return {
            "success": False,
            "message": "Timetable information not found."
        }

    conflicting_allocations = (
        HallAllocation.query
        .join(
            Timetable,
            HallAllocation.timetable_id == Timetable.id
        )
        .filter(
            HallAllocation.hall_id == hall.id,
            Timetable.exam_date == timetable.exam_date,
            HallAllocation.id != allocation.id
        )
        .all()
    )

    for existing_allocation in conflicting_allocations:
        existing_timetable = existing_allocation.timetable

        if not existing_timetable:
            continue

        if (
            existing_timetable.start_time < timetable.end_time
            and existing_timetable.end_time > timetable.start_time
        ):
            return {
                "success": False,
                "message": (
                    "Selected hall is already allocated during "
                    "an overlapping examination."
                ),
                "hall_id": hall.id,
                "exam_date": timetable.exam_date.isoformat(),
                "session": timetable.session
            }

    if purpose is not None:
        allowed_purposes = {
            "NORMAL",
            "ACCESSIBILITY",
            "MIXED"
        }

        purpose = str(purpose).upper()

        if purpose not in allowed_purposes:
            return {
                "success": False,
                "message": (
                    "Invalid purpose. Allowed values are "
                    "NORMAL, ACCESSIBILITY or MIXED."
                )
            }
    else:
        purpose = allocation.purpose

    try:
        allocation.hall_id = hall.id
        allocation.allocated_capacity = allocated_capacity
        allocation.purpose = purpose
        allocation.updated_at = datetime.utcnow()

        db.session.commit()

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to update hall allocation.",
            "error": str(error)
        }

    return {
        "success": True,
        "message": "Hall allocation updated successfully.",
        "allocation": {
            "id": allocation.id,
            "examination_id": allocation.examination_id,
            "timetable_id": allocation.timetable_id,
            "hall_id": allocation.hall_id,
            "allocated_capacity": allocation.allocated_capacity,
            "purpose": allocation.purpose,
            "status": allocation.status
        }
    }