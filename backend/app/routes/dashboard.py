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
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation
from app.models.hall_ticket import HallTicket

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
    # ALLOCATION OVERVIEW (Phase 7 persisted system)
    #
    # The dashboard now reads the actual persisted allocation
    # tables: HallAllocation, SeatAllocation and
    # InvigilatorAllocation. The legacy Allocation model is no
    # longer consulted for statistics.
    # =====================================================

    total_examinations = Examination.query.count()

    examinations_with_hall_allocations = (
        HallAllocation.query
        .with_entities(
            HallAllocation.examination_id
        )
        .distinct()
        .count()
    )

    total_hall_allocations = HallAllocation.query.count()
    total_seat_allocations = SeatAllocation.query.count()
    total_invigilator_assignments = (
        InvigilatorAllocation.query.count()
    )

    distinct_invigilators = (
        InvigilatorAllocation.query
        .with_entities(
            InvigilatorAllocation.staff_id
        )
        .distinct()
        .count()
    )

    # ---------------------------------------------------------
    # LIFECYCLE BREAKDOWN
    # ---------------------------------------------------------

    validated_examinations = (
        Examination.query
        .filter(Examination.status == "VALIDATED")
        .count()
    )

    approved_examinations = (
        Examination.query
        .filter(Examination.status == "APPROVED")
        .count()
    )

    published_examinations = (
        Examination.query
        .filter(Examination.status == "PUBLISHED")
        .count()
    )

    total_hall_tickets_issued = HallTicket.query.count()

    # ---------------------------------------------------------
    # AGGREGATED STATUS
    # ---------------------------------------------------------

    allocation_status = "NOT_STARTED"

    if total_examinations > 0:

        if examinations_with_hall_allocations == 0:
            allocation_status = "NOT_STARTED"

        elif (
            examinations_with_hall_allocations
            < total_examinations
        ):
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
            "examinations_with_hall_allocations": (
                examinations_with_hall_allocations
            ),
            "total_hall_allocations": total_hall_allocations,
            "total_seat_allocations": total_seat_allocations,
            "total_invigilator_assignments": (
                total_invigilator_assignments
            ),
            "distinct_invigilators": distinct_invigilators,
            "validated_examinations": validated_examinations,
            "approved_examinations": approved_examinations,
            "published_examinations": published_examinations,
            "total_hall_tickets_issued": (
                total_hall_tickets_issued
            ),
            "status": allocation_status,

            # Legacy keys retained for backward compatibility
            # with the existing AdminDashboard.jsx. They now
            # reflect the current persisted system.
            "examinations_with_allocations": (
                examinations_with_hall_allocations
            ),
            "total_allocations": total_hall_allocations,
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

    # =====================================================
    # STAFF EXAMINATION DUTIES
    # =====================================================

    staff_duties = (
        InvigilatorAllocation.query
        .filter_by(staff_id=staff.id)
        .join(
            Timetable,
            InvigilatorAllocation.timetable_id == Timetable.id
        )
        .order_by(
            Timetable.exam_date.asc(),
            Timetable.start_time.asc(),
            InvigilatorAllocation.hall_id.asc()
        )
        .all()
    )

    duties = []

    for duty in staff_duties:

        timetable = duty.timetable
        hall = duty.hall
        examination = duty.examination

        if not timetable or not examination:
            continue

        duties.append({
            "id": duty.id,
            "examination_id": examination.id,
            "examination_name": examination.name,
            "exam_type": examination.exam_type,

            "timetable_id": timetable.id,
            "subject_id": timetable.subject_id,
            "subject_name": (
                timetable.subject.subject_name
                if timetable.subject
                else None
            ),
            "subject_code": (
                timetable.subject.subject_code
                if timetable.subject
                else None
            ),

            "exam_date": timetable.exam_date.isoformat(),
            "session": timetable.session,
            "start_time": timetable.start_time.strftime("%H:%M"),
            "end_time": timetable.end_time.strftime("%H:%M"),

            "hall_id": hall.id if hall else None,
            "hall_name": hall.name if hall else None,
            "building_name": (
                hall.building_name
                if hall
                else None
            ),
            "floor_no": (
                hall.floor_no
                if hall
                else None
            ),

            "role": duty.role,
            "status": duty.status
        })

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
        },

        "examination_duties": duties

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

    # =====================================================
    # STUDENT TIMETABLE
    # =====================================================
    student_timetable = (
        Timetable.query
        .join(
            SeatAllocation,
            SeatAllocation.timetable_id == Timetable.id
        )
        .join(
            Examination,
            Timetable.examination_id == Examination.id
        )
        .filter(
            SeatAllocation.student_id == student.id,
            Examination.status == "PUBLISHED",
            Timetable.exam_date >= date.today()
        )
        .order_by(
            Timetable.exam_date.asc(),
            Timetable.start_time.asc()
        )
        .all()
    )

    timetable_entries = []

    for entry in student_timetable:

        examination = entry.examination

        timetable_entries.append({
            "id": entry.id,
            "examination_id": entry.examination_id,
            "examination_name": (
                examination.name
                if examination
                else None
            ),
            "exam_type": (
                examination.exam_type
                if examination
                else None
            ),

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
            "status": entry.status
        })


    # =====================================================
    # STUDENT HALL TICKETS + SEAT INFORMATION
    # =====================================================

    student_tickets = (
        HallTicket.query
        .filter_by(
            student_id=student.id
        )
        .join(
            Examination,
            HallTicket.examination_id == Examination.id
        )
        .filter(
            Examination.status == "PUBLISHED"
        )
        .order_by(
            Examination.start_date.asc()
        )
        .all()
    )

    hall_tickets = []

    from app.services.qr import make_qr_base64

    for ticket in student_tickets:

        seat_rows = (
            SeatAllocation.query
            .filter_by(
                examination_id=ticket.examination_id,
                student_id=student.id
            )
            .order_by(
                SeatAllocation.timetable_id.asc()
            )
            .all()
        )

        entries = []

        for row in seat_rows:

            timetable = row.timetable
            hall = row.hall

            if not timetable or not hall:
                continue

            entries.append({
                "timetable_id": timetable.id,

                "subject_name": (
                    timetable.subject.subject_name
                    if timetable.subject
                    else None
                ),

                "subject_code": (
                    timetable.subject.subject_code
                    if timetable.subject
                    else None
                ),

                "exam_date": timetable.exam_date.isoformat(),
                "session": timetable.session,
                "start_time": timetable.start_time.strftime("%H:%M"),
                "end_time": timetable.end_time.strftime("%H:%M"),

                "hall_name": hall.name,
                "building_name": hall.building_name,
                "floor_no": hall.floor_no,

                "seat_number": row.seat_number,
                "row_label": row.row_label,
                "seat_index": row.seat_index
            })

        hall_tickets.append({
            "id": ticket.id,
            "examination_id": ticket.examination_id,
            "examination_name": (
                ticket.examination.name
                if ticket.examination
                else None
            ),
            "status": ticket.status,
            "issued_at": ticket.issued_at.isoformat(),

            # QR contains ONLY the verification token.
            # Do not expose the raw token separately.
            "qr_base64": make_qr_base64({
                "t": ticket.verification_token
            }),

            "entries": entries
        })


    # =====================================================
    # RESPONSE
    # =====================================================

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
        },

        "timetable": timetable_entries,

        "hall_tickets": hall_tickets

    }, 200