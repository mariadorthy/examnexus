from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation

from app.services.eligibility import get_eligible_students


def timetable_overlaps(timetable_a, timetable_b):
    """
    Return True when two timetable entries occur on the same date
    and their examination times overlap.
    """

    if timetable_a.exam_date != timetable_b.exam_date:
        return False

    return (
        timetable_a.start_time < timetable_b.end_time
        and timetable_a.end_time > timetable_b.start_time
    )


def get_bulk_available_halls(timetable, reserved_halls):
    """
    Return halls that are active, available, not under maintenance,
    and not reserved by another overlapping timetable.
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
        if hall.id not in reserved_halls
    ]

def generate_bulk_allocation(examination_ids, force=False):
    """
    Generate Exam -> Hall allocation for multiple examinations.

    If force=True, existing hall + seat allocations for the
    selected examinations are cleared before regeneration.
    """

    # ---------------------------------------------------------
    # INPUT VALIDATION
    # ---------------------------------------------------------

    if not examination_ids:
        return {
            "success": False,
            "message": "No examinations selected."
        }

    # Remove duplicate IDs while preserving order.
    examination_ids = list(dict.fromkeys(examination_ids))

    # ---------------------------------------------------------
    # LOAD EXAMINATIONS
    # ---------------------------------------------------------

    examinations = (
        Examination.query
        .filter(
            Examination.id.in_(examination_ids)
        )
        .order_by(
            Examination.id
        )
        .all()
    )

    if not examinations:
        return {
            "success": False,
            "message": "No valid examinations found."
        }

    found_ids = {
        examination.id
        for examination in examinations
    }

    missing_ids = [
        examination_id
        for examination_id in examination_ids
        if examination_id not in found_ids
    ]

    if missing_ids:
        return {
            "success": False,
            "message": "One or more examinations were not found.",
            "missing_examination_ids": missing_ids
        }

    # ---------------------------------------------------------
    # CHECK EXISTING ALLOCATIONS
    # ---------------------------------------------------------
    existing_allocation = (
        HallAllocation.query
        .filter(
            HallAllocation.examination_id.in_(examination_ids)
        )
        .first()
    )

    if existing_allocation:

        if not force:
            return {
                "success": False,
                "message": (
                    "One or more selected examinations already "
                    "have hall allocations. Use force=true to "
                    "regenerate."
                )
            }

        from app.models.seat_allocation import SeatAllocation

        try:
            (
                SeatAllocation.query
                .filter(
                    SeatAllocation.examination_id.in_(
                        examination_ids
                    )
                )
                .delete(synchronize_session=False)
            )

            (
                HallAllocation.query
                .filter(
                    HallAllocation.examination_id.in_(
                        examination_ids
                    )
                )
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
               
    # ---------------------------------------------------------
    # BUILD TIMETABLE + ELIGIBILITY DATA
    # ---------------------------------------------------------

    timetable_data = []

    examination_results = []

    for examination in examinations:

        timetables = (
            Timetable.query
            .filter_by(
                examination_id=examination.id
            )
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
                    f"No timetable entries found for "
                    f"examination {examination.id}."
                ),
                "examination_id": examination.id
            }

        students = get_eligible_students(
            examination.id
        )

        if not students:
            return {
                "success": False,
                "message": (
                    f"No eligible registered students found "
                    f"for examination {examination.id}."
                ),
                "examination_id": examination.id,
                "eligible_students": 0
            }

        accessibility_students = [
            student
            for student in students
            if getattr(
                student,
                "disability",
                False
            )
        ]

        examination_results.append(
            {
                "examination_id": examination.id,
                "eligible_students": len(students),
                "students_requiring_accessibility": len(
                    accessibility_students
                ),
                "timetable_entries": len(timetables)
            }
        )

        for timetable in timetables:
            timetable_data.append(
                {
                    "examination": examination,
                    "timetable": timetable,
                    "eligible_students": len(students),
                    "accessibility_students": len(
                        accessibility_students
                    )
                }
            )

    # ---------------------------------------------------------
    # PROCESS TIMETABLES CHRONOLOGICALLY
    # ---------------------------------------------------------

    timetable_data.sort(
        key=lambda item: (
            item["timetable"].exam_date,
            item["timetable"].start_time,
            item["timetable"].id
        )
    )

    allocations = []

    try:

        for data in timetable_data:

            examination = data["examination"]
            timetable = data["timetable"]
            total_students = data["eligible_students"]

            # -------------------------------------------------
            # FIND HALLS RESERVED BY OVERLAPPING ALLOCATIONS
            # -------------------------------------------------

            reserved_halls = set()

            # Existing records already stored in the database.
            database_allocations = (
                HallAllocation.query
                .join(
                    Timetable,
                    HallAllocation.timetable_id
                    == Timetable.id
                )
                .all()
            )

            for existing_allocation in database_allocations:

                existing_timetable = (
                    existing_allocation.timetable
                )

                if not existing_timetable:
                    continue

                if timetable_overlaps(
                    existing_timetable,
                    timetable
                ):
                    reserved_halls.add(
                        existing_allocation.hall_id
                    )

            # Allocations created during this bulk operation.
            for new_allocation in allocations:

                existing_timetable = (
                    Timetable.query.get(
                        new_allocation.timetable_id
                    )
                )

                if not existing_timetable:
                    continue

                if timetable_overlaps(
                    existing_timetable,
                    timetable
                ):
                    reserved_halls.add(
                        new_allocation.hall_id
                    )

            # -------------------------------------------------
            # AVAILABLE HALLS
            # -------------------------------------------------

            available_halls = get_bulk_available_halls(
                timetable,
                reserved_halls
            )

            if not available_halls:

                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        f"No available halls for "
                        f"examination {examination.id} "
                        f"on "
                        f"{timetable.exam_date} "
                        f"{timetable.session}."
                    ),
                    "examination_id": examination.id,
                    "exam_date": (
                        timetable.exam_date.isoformat()
                    ),
                    "session": timetable.session,
                    "eligible_students": total_students
                }

            # -------------------------------------------------
            # CAPACITY CHECK
            # -------------------------------------------------

            total_available_capacity = sum(
                hall.examination_capacity
                for hall in available_halls
            )

            if total_students > total_available_capacity:

                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Insufficient hall capacity."
                    ),
                    "examination_id": examination.id,
                    "exam_date": (
                        timetable.exam_date.isoformat()
                    ),
                    "session": timetable.session,
                    "eligible_students": total_students,
                    "available_capacity": (
                        total_available_capacity
                    ),
                    "shortage": (
                        total_students
                        - total_available_capacity
                    )
                }

            # -------------------------------------------------
            # ACCESSIBILITY CHECK
            # -------------------------------------------------

            accessibility_students = data[
                "accessibility_students"
            ]

            accessibility_halls = [
                hall
                for hall in available_halls
                if hall.floor_no == 0
                and hall.is_accessible
            ]

            accessibility_capacity = sum(
                hall.examination_capacity
                for hall in accessibility_halls
            )

            if (
                accessibility_students
                > accessibility_capacity
            ):

                db.session.rollback()

                return {
                    "success": False,
                    "message": (
                        "Insufficient accessible hall capacity."
                    ),
                    "examination_id": examination.id,
                    "exam_date": (
                        timetable.exam_date.isoformat()
                    ),
                    "session": timetable.session,
                    "students_requiring_accessibility": (
                        accessibility_students
                    ),
                    "accessible_capacity": (
                        accessibility_capacity
                    ),
                    "shortage": (
                        accessibility_students
                        - accessibility_capacity
                    )
                }

            # -------------------------------------------------
            # ALLOCATE ACCESSIBILITY HALLS FIRST
            # -------------------------------------------------

            remaining_accessibility = (
                accessibility_students
            )

            remaining_normal = (
                total_students
                - accessibility_students
            )

            used_hall_ids = set()

            for hall in accessibility_halls:

                if remaining_accessibility <= 0:
                    break

                capacity = hall.examination_capacity

                accessibility_assigned = min(
                    capacity,
                    remaining_accessibility
                )

                remaining_accessibility -= (
                    accessibility_assigned
                )

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
                        allocated_capacity=(
                            allocated_capacity
                        ),
                        purpose=purpose,
                        status="GENERATED"
                    )
                )

                used_hall_ids.add(hall.id)

            # -------------------------------------------------
            # ALLOCATE NORMAL HALLS
            # -------------------------------------------------

            for hall in available_halls:

                if remaining_normal <= 0:
                    break

                if hall.id in used_hall_ids:
                    continue

                normal_assigned = min(
                    hall.examination_capacity,
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
                        allocated_capacity=(
                            normal_assigned
                        ),
                        purpose="NORMAL",
                        status="GENERATED"
                    )
                )

                used_hall_ids.add(hall.id)

            # -------------------------------------------------
            # FINAL CHECK
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
                        "hall capacity."
                    ),
                    "examination_id": examination.id,
                    "exam_date": (
                        timetable.exam_date.isoformat()
                    ),
                    "session": timetable.session,
                    "eligible_students": total_students,
                    "unallocated_students": (
                        remaining_accessibility
                        + remaining_normal
                    )
                }

    except Exception as error:

        db.session.rollback()

        return {
            "success": False,
            "message": (
                "Failed to generate bulk hall allocation."
            ),
            "error": str(error)
        }

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    try:

        db.session.add_all(
            allocations
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        return {
            "success": False,
            "message": (
                "Failed to save bulk hall allocation."
            ),
            "error": str(error)
        }

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

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
    # SEAT ALLOCATION FOR EACH EXAMINATION
    # ---------------------------------------------------------

    from app.services.seat_allocation import (
        generate_seat_allocation
    )

    seat_totals = {}
    seat_failures = []

    for examination in examinations:

        seat_result = generate_seat_allocation(
            examination_id=examination.id,
            force=True
        )

        if seat_result.get("success"):
            seat_totals[examination.id] = (
                seat_result.get("seat_records", 0)
            )
        else:
            seat_failures.append(
                {
                    "examination_id": examination.id,
                    "message": seat_result.get("message")
                }
            )

    if seat_failures:
        return {
            "success": False,
            "message": (
                "Hall allocation succeeded for all selected "
                "examinations, but seat allocation failed for "
                "one or more examinations."
            ),
            "hall_allocation": {
                "examinations_processed": len(examinations),
                "allocated_capacity": total_allocated_capacity,
                "halls_used": halls_used,
                "allocation_records": len(allocations)
            },
            "seat_failures": seat_failures
        }

    total_seat_records = sum(seat_totals.values())

    return {
        "success": True,
        "message": (
            "Bulk hall and seat allocation generated successfully."
        ),
        "examinations_processed": len(examinations),
        "examination_ids": [
            examination.id
            for examination in examinations
        ],
        "allocated_capacity": total_allocated_capacity,
        "halls_used": halls_used,
        "allocation_records": len(allocations),
        "seat_records": total_seat_records,
        "seat_records_by_examination": seat_totals,
        "regenerated": bool(force),
        "examinations": examination_results
    }