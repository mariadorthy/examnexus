from datetime import date

from flask import Blueprint
from app.auth.decorators import roles_required
from app.models.student import Student
from app.models.staff import Staff
from app.models.course import Course
from app.models.department import Department
from app.models.subject import Subject
from app.models.hall import Hall
from app.models.examination import Examination
from app.models.allocation import Allocation
from app.models.activity import Activity

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

    upcoming_examinations = (
        Examination.query
        .filter(
            Examination.exam_date >= date.today(),
            Examination.status == "SCHEDULED"
        )
        .order_by(
            Examination.exam_date.asc(),
            Examination.start_time.asc()
        )
        .limit(5)
        .all()
    )

    upcoming_exams = []

    for examination in upcoming_examinations:

        upcoming_exams.append({
            "id": examination.id,
            "subject_id": examination.subject_id,
            "subject_name": (
                examination.subject.subject_name
                if examination.subject
                else None
            ),
            "subject_code": (
                examination.subject.subject_code
                if examination.subject
                else None
            ),
            "exam_date": examination.exam_date.isoformat(),
            "session": examination.session,
            "start_time": examination.start_time.strftime("%H:%M"),
            "end_time": examination.end_time.strftime("%H:%M"),
            "duration_minutes": examination.duration_minutes,
            "exam_type": examination.exam_type,
            "status": examination.status
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
