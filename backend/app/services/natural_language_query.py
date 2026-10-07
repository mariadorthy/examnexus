"""
Natural-language data query executor.

Feature 19 / Phase 9.

This is the ONLY place natural-language intents touch the database.

Rules enforced here:
- READ-ONLY. No add / commit / delete / update / flush of mutations.
- Only predefined SQLAlchemy queries.
- No raw SQL, no string interpolation into SQL.
- Reuses existing services (eligibility) where possible.
"""

from typing import Any, Dict

from sqlalchemy import func

from app import db
from app.models.examination import Examination
from app.models.course import Course
from app.models.student import Student
from app.models.hall import Hall
from app.models.timetable import Timetable
from app.models.hall_allocation import HallAllocation
from app.models.allocation import Allocation
from app.models.seat_allocation import SeatAllocation
from app.models.exam_registration import ExamRegistration
from app.services.eligibility import get_eligible_students


def _ok(data: Any, message: str = "Query executed successfully.") -> Dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def _err(message: str) -> Dict[str, Any]:
    return {"success": False, "data": None, "message": message}


# =========================================================
# INTENT HANDLERS (pure read queries)
# =========================================================

def _list_examinations(params: Dict[str, Any]) -> Dict[str, Any]:
    query = Examination.query

    course = params.get("course")
    if course:
        query = query.join(Examination.course).filter(
            func.lower(Course.course_name).like(f"%{course.lower()}%")
        )

    status = params.get("status")
    if status:
        query = query.filter(Examination.status == status)

    rows = query.order_by(Examination.start_date).all()

    return _ok({
        "count": len(rows),
        "examinations": [
            {
                "id": e.id,
                "name": e.name,
                "course": e.course.course_name if e.course else None,
                "semester": e.semester,
                "status": e.status,
                "start_date": e.start_date.isoformat(),
                "end_date": e.end_date.isoformat(),
            }
            for e in rows
        ],
    })


def _examination_status(params):
    name = params.get("name")

    if not name:
        return _err("Examination name is required.")

    exam = (
        Examination.query
        .filter(func.lower(Examination.name) == name.lower())
        .first()
    )

    if not exam:
        return _err("Examination not found.")

    return _ok([
        {
            "id": exam.id,
            "name": exam.name,
            "status": exam.status,
        }
    ])
    

def _eligible_student_count(params: Dict[str, Any]) -> Dict[str, Any]:
    exam_id = params.get("examination_id")

    if exam_id is None:
        exam = Examination.query.order_by(Examination.id.desc()).first()
        if not exam:
            return _err("No examinations found.")
        exam_id = exam.id
    else:
        exam = Examination.query.get(exam_id)
        if not exam:
            return _err(f"Examination {exam_id} not found.")

    students = get_eligible_students(exam_id)

    return _ok({
        "examination_id": exam_id,
        "examination_name": exam.name,
        "eligible_student_count": len(students),
    })


def _registered_student_count(params: Dict[str, Any]) -> Dict[str, Any]:
    exam_id = params.get("examination_id")

    if exam_id is None:
        exam = Examination.query.order_by(Examination.id.desc()).first()
        if not exam:
            return _err("No examinations found.")
        exam_id = exam.id
    else:
        exam = Examination.query.get(exam_id)
        if not exam:
            return _err(f"Examination {exam_id} not found.")

    count = (
        ExamRegistration.query
        .filter_by(examination_id=exam_id, status="REGISTERED")
        .count()
    )

    return _ok({
        "examination_id": exam_id,
        "examination_name": exam.name,
        "registered_student_count": count,
    })


def _halls_by_status(params: Dict[str, Any]) -> Dict[str, Any]:
    status = params.get("status")

    query = Hall.query.filter(Hall.is_active.is_(True))

    if status == "available":
        query = query.filter(
            Hall.is_available.is_(True),
            Hall.is_under_maintenance.is_(False),
        )
    elif status == "unavailable":
        query = query.filter(Hall.is_available.is_(False))
    elif status == "maintenance":
        query = query.filter(Hall.is_under_maintenance.is_(True))
    else:
        return _err("Unsupported hall status filter.")

    rows = query.order_by(Hall.name).all()

    return _ok({
        "status_filter": status,
        "count": len(rows),
        "halls": [
            {
                "id": h.id,
                "name": h.name,
                "building": h.building_name,
                "floor_no": h.floor_no,
                "examination_capacity": h.examination_capacity,
                "is_available": h.is_available,
                "is_under_maintenance": h.is_under_maintenance,
                "is_accessible": h.is_accessible,
            }
            for h in rows
        ],
    })


def _students_in_hall(params: Dict[str, Any]) -> Dict[str, Any]:
    hall_code = params.get("hall")
    if not hall_code:
        return _err("Hall code was not specified.")

    hall = (
        Hall.query
        .filter(func.lower(Hall.name) == hall_code.lower())
        .first()
    )

    if not hall:
        hall = (
            Hall.query
            .filter(func.lower(Hall.name).like(f"%{hall_code.lower()}%"))
            .first()
        )

    if not hall:
        return _err(f"Hall '{hall_code}' not found.")

    seat_count = (
        SeatAllocation.query
        .filter(SeatAllocation.hall_id == hall.id)
        .count()
    )

    allocated_capacity = (
        db.session.query(
            func.coalesce(func.sum(HallAllocation.allocated_capacity), 0)
        )
        .filter(HallAllocation.hall_id == hall.id)
        .scalar()
    )

    return _ok({
        "hall_id": hall.id,
        "hall_name": hall.name,
        "students_allocated": seat_count,
        "allocated_capacity": int(allocated_capacity or 0),
    })


def _hall_allocation_summary(_params: Dict[str, Any]) -> Dict[str, Any]:
    rows = (
        db.session.query(
            Hall.id,
            Hall.name,
            func.count(SeatAllocation.id).label("students"),
        )
        .join(SeatAllocation, SeatAllocation.hall_id == Hall.id)
        .group_by(Hall.id, Hall.name)
        .order_by(Hall.name)
        .all()
    )

    return _ok({
        "hall_count": len(rows),
        "summary": [
            {"hall_id": r[0], "hall_name": r[1], "students": int(r[2])}
            for r in rows
        ],
    })


def _unallocated_student_count(params):
    examination_id = params.get("examination_id")

    if not examination_id:
        return _err("Examination ID is required.")

    examination = Examination.query.get(examination_id)

    if not examination:
        return _err("Examination not found.")

    registered = ExamRegistration.query.filter_by(
        examination_id=examination_id,
        status="REGISTERED",
    ).count()

    allocated = (
        db.session.query(
            func.count(func.distinct(Allocation.student_id))
        )
        .filter(
            Allocation.examination_id == examination_id
        )
        .scalar()
        or 0
    )

    return _ok({
        "examination_id": examination_id,
        "registered": registered,
        "allocated": allocated,
        "unallocated": max(registered - allocated, 0),
    })


def _examination_timetable(params: Dict[str, Any]) -> Dict[str, Any]:
    exam_id = params.get("examination_id")
    course = params.get("course")

    query = Timetable.query

    if exam_id is not None:
        query = query.filter(Timetable.examination_id == exam_id)

    if course:
        query = (
            query
            .join(Timetable.examination)
            .join(Examination.course)
            .filter(
                func.lower(Course.course_name).like(f"%{course.lower()}%")
            )
        )

    rows = (
        query
        .order_by(Timetable.exam_date, Timetable.start_time, Timetable.id)
        .all()
    )

    return _ok({
        "count": len(rows),
        "timetable": [
            {
                "id": t.id,
                "examination_id": t.examination_id,
                "examination_name": (
                    t.examination.name if t.examination else None
                ),
                "subject_id": t.subject_id,
                "subject_code": (
                    t.subject.subject_code if t.subject else None
                ),
                "subject_name": (
                    t.subject.subject_name if t.subject else None
                ),
                "exam_date": t.exam_date.isoformat(),
                "session": t.session,
                "start_time": t.start_time.isoformat(),
                "end_time": t.end_time.isoformat(),
                "status": t.status,
            }
            for t in rows
        ],
    })
def _hall_capacity(params):
    hall_name = params.get("hall")

    if not hall_name:
        return _err("Hall name is required.")

    hall = (
        Hall.query
        .filter(func.lower(Hall.name) == hall_name.lower())
        .first()
    )

    if not hall:
        return _err("Hall not found.")

    return _ok([
        {
            "id": hall.id,
            "name": hall.name,
            "capacity": hall.capacity,
            "examination_capacity": getattr(
                hall,
                "examination_capacity",
                None,
            ),
        }
    ])

_HANDLERS = {
    "LIST_EXAMINATIONS": _list_examinations,
    "EXAMINATION_STATUS": _examination_status,
    "ELIGIBLE_STUDENT_COUNT": _eligible_student_count,
    "REGISTERED_STUDENT_COUNT": _registered_student_count,
    "HALLS_BY_STATUS": _halls_by_status,
    "STUDENTS_IN_HALL": _students_in_hall,
    "HALL_ALLOCATION_SUMMARY": _hall_allocation_summary,
    "UNALLOCATED_STUDENT_COUNT": _unallocated_student_count,
    "EXAMINATION_TIMETABLE": _examination_timetable,
    "HALL_CAPACITY": _hall_capacity,
}

def execute_query(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a validated intent. READ-ONLY.
    Never accepts raw SQL. Never mutates the database.
    """
    handler = _HANDLERS.get(intent)
    if handler is None:
        return _err(f"Unsupported intent: {intent}")

    try:
        return handler(params or {})
    except Exception as exc:  # noqa: BLE001
        return _err(f"Query execution failed: {type(exc).__name__}")