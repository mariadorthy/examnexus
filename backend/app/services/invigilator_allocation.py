"""
Invigilator allocation service.

Allocates active + available Staff to HallAllocation records for an
examination. Deterministic ordering: staff_id ascending.

Rules:
  - Required invigilators per hall slot = max(1, ceil(allocated_capacity / 30))
  - Candidate pool: Staff.is_active == True AND Staff.availability == True
  - A staff member cannot be assigned to overlapping timetable sessions
  - Duplicate (timetable, hall, staff) prevented by DB unique constraint
  - If any hall slot cannot be covered, whole operation rolls back
"""

import math
from datetime import datetime

from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.staff import Staff
from app.models.invigilator_allocation import InvigilatorAllocation


SEATS_PER_INVIGILATOR = 30


def _required_invigilators(allocated_capacity):
    """
    Required invigilators for a hall slot. Minimum 1.
    """

    if allocated_capacity <= 0:
        return 1

    return max(
        1,
        math.ceil(allocated_capacity / SEATS_PER_INVIGILATOR)
    )


def _candidate_staff():
    """
    Active + available staff, deterministic ordering by id ascending.
    """

    return (
        Staff.query
        .filter(
            Staff.is_active.is_(True),
            Staff.availability.is_(True)
        )
        .order_by(Staff.id.asc())
        .all()
    )


def _overlaps(timetable_a, timetable_b):
    """
    True if two timetable entries overlap in date + time window.
    """

    if timetable_a.exam_date != timetable_b.exam_date:
        return False

    return (
        timetable_a.start_time < timetable_b.end_time
        and timetable_a.end_time > timetable_b.start_time
    )

def _staff_has_conflict(
    staff_id,
    timetable,
    planned_slots,
    examination_id=None
):
    """
    Check whether a staff member is already assigned to an
    overlapping timetable.

    Current-examination persisted rows are ignored when
    force-regenerating that examination. Conflicts from other
    examinations are still enforced.
    """

    # In-memory conflicts created during this generation run.
    for planned_staff_id, planned_timetable in planned_slots:
        if planned_staff_id != staff_id:
            continue

        if _overlaps(planned_timetable, timetable):
            return True

    # Persisted conflicts from other examinations.
    existing = (
        InvigilatorAllocation.query
        .join(
            Timetable,
            InvigilatorAllocation.timetable_id == Timetable.id
        )
        .filter(
            InvigilatorAllocation.staff_id == staff_id,
            Timetable.exam_date == timetable.exam_date
        )
        .all()
    )

    for row in existing:
        if (
            examination_id is not None
            and row.examination_id == examination_id
        ):
            continue

        other = row.timetable

        if other is None:
            continue

        if _overlaps(other, timetable):
            return True

    return False

def generate_invigilator_allocation(examination_id, force=False):
    """
    Generate invigilator allocations for every HallAllocation of the
    examination. If force=True, existing rows for the examination are
    cleared first.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
        }

    hall_allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .order_by(
            HallAllocation.timetable_id.asc(),
            HallAllocation.hall_id.asc()
        )
        .all()
    )

    if not hall_allocations:
        return {
            "success": False,
            "message": (
                "Hall allocation must be generated before "
                "invigilator allocation"
            )
        }

    existing_count = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .count()
    )

    if existing_count > 0 and not force:
        return {
            "success": False,
            "message": (
                "Invigilator allocation already exists for this "
                "examination. Use force=true to regenerate."
            ),
            "examination_id": examination_id
        }

    candidates = _candidate_staff()

    if not candidates:
        return {
            "success": False,
            "message": (
                "No active and available staff members found"
            )
        }

    # ---------------------------------------------------------
    # BUILD PLAN IN MEMORY
    # ---------------------------------------------------------

    planned_slots = []       # list of (staff_id, timetable)
    new_rows = []            # list of InvigilatorAllocation
    per_hall_summary = []
    staff_duty_count = {}

    for allocation in hall_allocations:

        timetable = allocation.timetable
        hall = allocation.hall

        if not timetable or not hall:
            return {
                "success": False,
                "message": (
                    f"Hall allocation #{allocation.id} is missing "
                    f"timetable or hall"
                )
            }

        required = _required_invigilators(
            allocation.allocated_capacity
        )

        assigned_here = 0

        for staff in candidates:

            if assigned_here >= required:
                break

            if _staff_has_conflict(
                staff.id,
                timetable,
                planned_slots,
                examination_id=examination_id
            ):
                continue

            new_rows.append(
                InvigilatorAllocation(
                    examination_id=examination.id,
                    timetable_id=timetable.id,
                    hall_allocation_id=allocation.id,
                    hall_id=hall.id,
                    staff_id=staff.id,
                    role="INVIGILATOR",
                    status="GENERATED"
                )
            )

            planned_slots.append((staff.id, timetable))

            staff_duty_count[staff.id] = (
                staff_duty_count.get(staff.id, 0) + 1
            )

            assigned_here += 1

        if assigned_here < required:
            return {
                "success": False,
                "message": (
                    f"Insufficient invigilators for hall "
                    f"{hall.name} (timetable #{timetable.id})"
                ),
                "timetable_id": timetable.id,
                "hall_id": hall.id,
                "required": required,
                "assigned": assigned_here,
                "shortage": required - assigned_here
            }

        per_hall_summary.append(
            {
                "timetable_id": timetable.id,
                "hall_id": hall.id,
                "required": required,
                "assigned": assigned_here
            }
        )

    # ---------------------------------------------------------
    # PERSIST
    # ---------------------------------------------------------

    try:
        if force and existing_count > 0:
            (
                InvigilatorAllocation.query
                .filter_by(examination_id=examination_id)
                .delete(synchronize_session=False)
            )

        db.session.add_all(new_rows)
        db.session.commit()

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to save invigilator allocation",
            "error": str(error)
        }

    total_assigned = len(new_rows)

    distinct_staff = len({
        row.staff_id for row in new_rows
    })

    return {
        "success": True,
        "message": "Invigilator allocation generated successfully",
        "examination_id": examination.id,
        "hall_slots": len(hall_allocations),
        "invigilator_assignments": total_assigned,
        "distinct_staff_used": distinct_staff,
        "regenerated": bool(force and existing_count > 0),
        "per_hall": per_hall_summary
    }


def get_invigilator_allocations(examination_id):
    """
    Read-only listing for the given examination, ordered
    deterministically.
    """

    rows = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .join(Timetable, InvigilatorAllocation.timetable_id == Timetable.id)
        .order_by(
            Timetable.exam_date.asc(),
            Timetable.start_time.asc(),
            InvigilatorAllocation.hall_id.asc(),
            InvigilatorAllocation.staff_id.asc()
        )
        .all()
    )

    result = []

    for row in rows:
        result.append({
            "id": row.id,
            "examination_id": row.examination_id,
            "timetable_id": row.timetable_id,
            "exam_date": (
                row.timetable.exam_date.isoformat()
                if row.timetable else None
            ),
            "session": (
                row.timetable.session if row.timetable else None
            ),
            "start_time": (
                row.timetable.start_time.strftime("%H:%M")
                if row.timetable else None
            ),
            "end_time": (
                row.timetable.end_time.strftime("%H:%M")
                if row.timetable else None
            ),
            "hall_id": row.hall_id,
            "hall": row.hall.name if row.hall else None,
            "building_name": (
                row.hall.building_name if row.hall else None
            ),
            "floor_no": row.hall.floor_no if row.hall else None,
            "staff_id": row.staff_id,
            "staff_name": row.staff.name if row.staff else None,
            "staff_email": row.staff.email if row.staff else None,
            "role": row.role,
            "status": row.status
        })

    return result


def clear_invigilator_allocations(examination_id):
    """
    Delete all invigilator allocations for an examination.
    """

    deleted = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .delete(synchronize_session=False)
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Invigilator allocation cleared",
        "deleted": deleted
    }


def invigilator_workload(examination_id):
    """
    Duty count per staff member for the examination.
    """

    rows = (
        InvigilatorAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    counts = {}

    for row in rows:
        counts.setdefault(row.staff_id, 0)
        counts[row.staff_id] += 1

    staff_map = {
        staff.id: staff
        for staff in Staff.query.filter(
            Staff.id.in_(list(counts.keys()))
        ).all()
    } if counts else {}

    result = []

    for staff_id in sorted(counts.keys()):
        staff = staff_map.get(staff_id)
        result.append({
            "staff_id": staff_id,
            "staff_name": staff.name if staff else None,
            "email": staff.email if staff else None,
            "duties": counts[staff_id]
        })

    return result

def generate_bulk_invigilator_allocation(
    examination_ids,
    force=False
):
    """
    Generate invigilator allocation for multiple examinations.

    Non-atomic by design: each examination is processed
    independently through the existing single-examination
    service.

    Reuses generate_invigilator_allocation() — does NOT
    duplicate the allocation algorithm.
    """

    results = []

    for examination_id in examination_ids:

        single_result = generate_invigilator_allocation(
            examination_id,
            force=force
        )

        if single_result.get("success"):

            results.append({
                "examination_id": examination_id,
                "status": "GENERATED",
                "invigilator_assignments": (
                    single_result.get(
                        "invigilator_assignments", 0
                    )
                ),
                "hall_slots": single_result.get(
                    "hall_slots", 0
                ),
                "distinct_staff_used": single_result.get(
                    "distinct_staff_used", 0
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
                    "message",
                    "Invigilator allocation failed"
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