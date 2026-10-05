"""
Read-only reporting service. No writes. No new tables.
"""

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.eligibility import get_eligible_students
from app.services.validation import (
    validate_allocation,
    validate_invigilator_allocation
)


def allocation_report(examination_id):
    """
    Examination allocation report: one row per HallAllocation.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .order_by(
            HallAllocation.timetable_id.asc(),
            HallAllocation.hall_id.asc()
        )
        .all()
    )

    rows = []

    for allocation in allocations:

        timetable = allocation.timetable
        hall = allocation.hall

        seat_count = (
            SeatAllocation.query
            .filter_by(hall_allocation_id=allocation.id)
            .count()
        )

        invig_count = (
            InvigilatorAllocation.query
            .filter_by(hall_allocation_id=allocation.id)
            .count()
        )

        rows.append({
            "timetable_id": allocation.timetable_id,
            "exam_date": (
                timetable.exam_date.isoformat()
                if timetable else None
            ),
            "session": timetable.session if timetable else None,
            "hall_id": allocation.hall_id,
            "hall": hall.name if hall else None,
            "building_name": (
                hall.building_name if hall else None
            ),
            "purpose": allocation.purpose,
            "allocated_capacity": allocation.allocated_capacity,
            "seats_used": seat_count,
            "invigilators": invig_count
        })

    hall_val = validate_allocation(examination_id)
    invig_val = validate_invigilator_allocation(examination_id)

    return {
        "success": True,
        "examination_id": examination_id,
        "examination_name": examination.name,
        "status": examination.status,
        "rows": rows,
        "hall_validation": hall_val.get("status"),
        "invigilator_validation": invig_val.get("status")
    }


def student_allocation_report(examination_id):
    """
    Student allocation report: one row per (student, timetable).
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    seats = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .join(Timetable, SeatAllocation.timetable_id == Timetable.id)
        .order_by(
            Timetable.exam_date.asc(),
            Timetable.start_time.asc(),
            SeatAllocation.student_id.asc()
        )
        .all()
    )

    rows = []

    for seat in seats:
        rows.append({
            "student_id": seat.student_id,
            "student_code": (
                seat.student.student_id if seat.student else None
            ),
            "student_name": (
                seat.student.name if seat.student else None
            ),
            "timetable_id": seat.timetable_id,
            "exam_date": (
                seat.timetable.exam_date.isoformat()
                if seat.timetable else None
            ),
            "session": (
                seat.timetable.session if seat.timetable else None
            ),
            "hall_id": seat.hall_id,
            "hall": seat.hall.name if seat.hall else None,
            "seat_number": seat.seat_number,
            "row_label": seat.row_label
        })

    return {
        "success": True,
        "examination_id": examination_id,
        "examination_name": examination.name,
        "rows": rows
    }


def hall_utilization_report(examination_id):
    """
    Hall utilization: capacity vs seats used, per hall per timetable.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .order_by(
            HallAllocation.timetable_id.asc(),
            HallAllocation.hall_id.asc()
        )
        .all()
    )

    rows = []

    for allocation in allocations:

        seats_used = (
            SeatAllocation.query
            .filter_by(hall_allocation_id=allocation.id)
            .count()
        )

        capacity = allocation.allocated_capacity or 0

        utilization = (
            round(seats_used / capacity * 100, 2)
            if capacity > 0 else 0.0
        )

        rows.append({
            "timetable_id": allocation.timetable_id,
            "exam_date": (
                allocation.timetable.exam_date.isoformat()
                if allocation.timetable else None
            ),
            "session": (
                allocation.timetable.session
                if allocation.timetable else None
            ),
            "hall_id": allocation.hall_id,
            "hall": (
                allocation.hall.name if allocation.hall else None
            ),
            "allocated_capacity": capacity,
            "seats_used": seats_used,
            "utilization_percent": utilization
        })

    return {
        "success": True,
        "examination_id": examination_id,
        "examination_name": examination.name,
        "rows": rows
    }


def invigilator_workload_report(examination_id):
    """
    Invigilator workload: duty count + sessions per staff.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {"success": False, "message": "Examination not found"}

    rows = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .order_by(
            InvigilatorAllocation.staff_id.asc(),
            InvigilatorAllocation.timetable_id.asc()
        )
        .all()
    )

    by_staff = {}

    for row in rows:
        entry = by_staff.setdefault(row.staff_id, {
            "staff_id": row.staff_id,
            "staff_name": row.staff.name if row.staff else None,
            "email": row.staff.email if row.staff else None,
            "duties": 0,
            "sessions": []
        })

        entry["duties"] += 1

        if row.timetable:
            entry["sessions"].append({
                "timetable_id": row.timetable_id,
                "exam_date": row.timetable.exam_date.isoformat(),
                "session": row.timetable.session,
                "hall_id": row.hall_id,
                "hall": row.hall.name if row.hall else None
            })

    ordered = [
        by_staff[staff_id]
        for staff_id in sorted(by_staff.keys())
    ]

    return {
        "success": True,
        "examination_id": examination_id,
        "examination_name": examination.name,
        "rows": ordered
    }