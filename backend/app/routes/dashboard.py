from datetime import date

from flask import Blueprint
from app.auth.decorators import roles_required
from app.auth.security import decode_access_token
from app.models.student import Student
from app.models.staff import Staff
from app.models.course import Course
from app.models.department import Department
from app.models.subject import Subject
from app.models.hall import Hall
from app.models.examination import Examination
from app.models.allocation import Allocation
from app.models.activity import Activity
from app.models.timetable import Timetable

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_dashboard():

    # =====================================================
    # BASIC STATISTICS
    # =====================================================

    total_students = Student.query.filter_by(
        is_active=True
    ).count()

    total_staff = Staff.query.filter_by(
        is_active=True
    ).count()

    total_courses = Course.query.filter_by(
        is_active=True
    ).count()

    total_departments = Department.query.filter_by(
        is_active=True
    ).count()

    total_subjects = Subject.query.filter_by(
        is_active=True
    ).count()

    total_halls = Hall.query.filter_by(
        is_active=True
    ).count()

    # =====================================================
    # UPCOMING EXAMINATIONS
    # =====================================================

    upcoming_timetable_entries = (
    Timetable.query
    .join(
        Examination,
        Timetable.examination_id == Examination.id
    )
    .filter(
        Timetable.exam_date >= date.today()
    )
    .order_by(
        Timetable.exam_date.asc(),
        Timetable.start_time.asc()
    )
    .limit(5)
    .all()
)

    upcoming_exams = []

    for entry in upcoming_timetable_entries:

        upcoming_exams.append({
            "id": entry.id,
            "examination_id": entry.examination_id,
            "subject_id": entry.subject_id,
            "subject_name": (
                entry.subject.subject_name
                if entry.subject
                else None
            ),
            "subject_code": (
                entry.subject.subject_code
                if entry.subject
                else None
            ),
            "exam_date": entry.exam_date.isoformat(),
            "session": entry.session,
            "start_time": entry.start_time.strftime("%H:%M"),
            "end_time": entry.end_time.strftime("%H:%M"),
            "duration_minutes": entry.duration_minutes,
            "exam_type": entry.examination.exam_type,
            "status": entry.status
        })

    # =====================================================
    # ALLOCATION OVERVIEW
    # =====================================================

    total_examinations = Examination.query.count()

    examinations_with_allocations = (
        Allocation.query
        .with_entities(
            Allocation.examination_id
        )
        .distinct()
        .count()
    )

    total_allocations = Allocation.query.count()

    allocation_status = "NOT_STARTED"

    if total_examinations > 0:

        if examinations_with_allocations == 0:
            allocation_status = "NOT_STARTED"

        elif examinations_with_allocations < total_examinations:
            allocation_status = "PARTIAL"

        else:
            allocation_status = "COMPLETED"

    # =====================================================
    # SYSTEM STATUS
    # =====================================================

    system_status = {
        "departments": total_departments > 0,
        "courses": total_courses > 0,
        "subjects": total_subjects > 0,
        "students": total_students > 0,
        "staff": total_staff > 0,
        "halls": total_halls > 0
    }

    # =====================================================
    # RECENT ACTIVITY
    # =====================================================

    recent_activity_records = (
        Activity.query
        .order_by(
            Activity.created_at.desc()
        )
        .limit(5)
        .all()
    )

    recent_activity = []

    for activity in recent_activity_records:

        recent_activity.append({
            "id": activity.id,
            "action": activity.action,
            "description": activity.description,
            "created_at": activity.created_at.isoformat()
        })

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "success": True,

        "statistics": {
            "students": total_students,
            "staff": total_staff,
            "courses": total_courses,
            "departments": total_departments,
            "subjects": total_subjects,
            "halls": total_halls
        },

        "upcoming_examinations": upcoming_exams,

        "recent_activity": recent_activity,
    
        "allocation": {
            "total_examinations": total_examinations,
            "examinations_with_allocations": examinations_with_allocations,
            "total_allocations": total_allocations,
            "status": allocation_status
        },

        "system_status": system_status
    }

@dashboard_bp.route("/staff", methods=["GET"])
@roles_required("staff")
def get_staff_dashboard():
    from flask import request
    from app.auth.security import decode_access_token

    payload = decode_access_token()
    staff_id = payload.get("sub")

    staff = Staff.query.get(staff_id)

    if not staff:
        return {
            "success": False,
            "message": "Staff user not found."
        }, 404

    if not staff.is_active:
        return {
            "success": False,
            "message": "This account is inactive."
        }, 403

    return {
        "success": True,
        "user": {
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "role": "staff",
            "designation": staff.designation,
            "department_id": staff.department_id,
            "availability": staff.availability,
            "assigned_batch": staff.assigned_batch
        }
    }, 200


@dashboard_bp.route("/student", methods=["GET"])
@roles_required("student")
def get_student_dashboard():
    payload = decode_access_token()
    student_id = payload.get("sub")

    student = Student.query.get(student_id)

    if not student:
        return {
            "success": False,
            "message": "Student user not found."
        }, 404

    if not student.is_active:
        return {
            "success": False,
            "message": "This account is inactive."
        }, 403

    return {
        "success": True,
        "user": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "role": "student",
            "course_id": student.course_id,
            "batch": student.batch,
            "semester": student.semester,
            "class_name": student.class_name,
            "session": student.session
        }
    }, 200