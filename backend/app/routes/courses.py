from flask import Blueprint, request
from app import db
from app.models.course import Course
from app.models.department import Department
from app.auth.decorators import roles_required


courses_bp = Blueprint("courses", __name__)


# =========================================================
# GET ALL COURSES
# =========================================================

@courses_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_courses():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    return [
        {
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "course_abbreviation": course.course_abbreviation,
            "program_level": course.program_level,
            "department_id": course.department_id,
            "study_shift": course.study_shift,
            "session": course.session,
            "total_semesters": course.total_semesters,
            "is_active": course.is_active
        }
        for course in courses
    ]


# =========================================================
# CREATE COURSE
# =========================================================

@courses_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_course():

    data = request.get_json(silent=True) or {}

    course_code = (
        data.get("course_code") or ""
    ).strip().upper()

    course_name = (
        data.get("course_name") or ""
    ).strip()

    course_abbreviation = (
        data.get("course_abbreviation") or ""
    ).strip().upper()

    program_level = (
        data.get("program_level") or ""
    ).strip()

    study_shift = (
        data.get("study_shift") or ""
    ).strip()

    session = (
        data.get("session") or ""
    ).strip()

    department_id = data.get("department_id")
    total_semesters = data.get("total_semesters")


    if not course_code:
        return {
            "message": "Course code is required."
        }, 400

    if not course_name:
        return {
            "message": "Course name is required."
        }, 400

    if not course_abbreviation:
        return {
            "message": "Course abbreviation is required."
        }, 400

    if not program_level:
        return {
            "message": "Program level is required."
        }, 400

    if not study_shift:
        return {
            "message": "Study shift is required."
        }, 400

    if not session:
        return {
            "message": "Session is required."
        }, 400

    if department_id is None:
        return {
            "message": "Department is required."
        }, 400

    if total_semesters is None:
        return {
            "message": "Total semesters is required."
        }, 400


    try:
        department_id = int(department_id)
        total_semesters = int(total_semesters)
    except (TypeError, ValueError):
        return {
            "message": "Department and total semesters must be valid numbers."
        }, 400


    if total_semesters <= 0:
        return {
            "message": "Total semesters must be greater than zero."
        }, 400


    department = Department.query.get(department_id)

    if not department:
        return {
            "message": "Selected department does not exist."
        }, 400


    existing_code = Course.query.filter_by(
        course_code=course_code
    ).first()

    if existing_code:
        return {
            "message": "Course code already exists."
        }, 409


    existing_abbreviation = Course.query.filter_by(
        course_abbreviation=course_abbreviation
    ).first()

    if existing_abbreviation:
        return {
            "message": "Course abbreviation already exists."
        }, 409


    course = Course(
        course_code=course_code,
        course_name=course_name,
        course_abbreviation=course_abbreviation,
        program_level=program_level,
        department_id=department_id,
        study_shift=study_shift,
        session=session,
        total_semesters=total_semesters,
        is_active=True
    )

    db.session.add(course)
    db.session.commit()


    return {
        "message": "Course created successfully",
        "id": course.id
    }, 201


# =========================================================
# GET SINGLE COURSE
# =========================================================

@courses_bp.route("/<int:course_id>", methods=["GET"])
@roles_required("admin")
def get_course(course_id):

    course = Course.query.get_or_404(course_id)

    return {
        "id": course.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "course_abbreviation": course.course_abbreviation,
        "program_level": course.program_level,
        "department_id": course.department_id,
        "study_shift": course.study_shift,
        "session": course.session,
        "total_semesters": course.total_semesters,
        "is_active": course.is_active
    }


# =========================================================
# UPDATE COURSE
# =========================================================

@courses_bp.route("/<int:course_id>", methods=["PUT"])
@roles_required("admin")
def update_course(course_id):

    course = Course.query.get_or_404(course_id)

    data = request.get_json(silent=True) or {}

    course_code = (
        data.get("course_code") or ""
    ).strip().upper()

    course_name = (
        data.get("course_name") or ""
    ).strip()

    course_abbreviation = (
        data.get("course_abbreviation") or ""
    ).strip().upper()

    program_level = (
        data.get("program_level") or ""
    ).strip()

    study_shift = (
        data.get("study_shift") or ""
    ).strip()

    session = (
        data.get("session") or ""
    ).strip()

    department_id = data.get("department_id")
    total_semesters = data.get("total_semesters")


    if not course_code:
        return {
            "message": "Course code is required."
        }, 400

    if not course_name:
        return {
            "message": "Course name is required."
        }, 400

    if not course_abbreviation:
        return {
            "message": "Course abbreviation is required."
        }, 400

    if not program_level:
        return {
            "message": "Program level is required."
        }, 400

    if not study_shift:
        return {
            "message": "Study shift is required."
        }, 400

    if not session:
        return {
            "message": "Session is required."
        }, 400

    if department_id is None:
        return {
            "message": "Department is required."
        }, 400

    if total_semesters is None:
        return {
            "message": "Total semesters is required."
        }, 400


    try:
        department_id = int(department_id)
        total_semesters = int(total_semesters)
    except (TypeError, ValueError):
        return {
            "message": "Department and total semesters must be valid numbers."
        }, 400


    if total_semesters <= 0:
        return {
            "message": "Total semesters must be greater than zero."
        }, 400


    department = Department.query.get(department_id)

    if not department:
        return {
            "message": "Selected department does not exist."
        }, 400


    existing_code = Course.query.filter(
        Course.course_code == course_code,
        Course.id != course.id
    ).first()

    if existing_code:
        return {
            "message": "Course code already exists."
        }, 409


    existing_abbreviation = Course.query.filter(
        Course.course_abbreviation == course_abbreviation,
        Course.id != course.id
    ).first()

    if existing_abbreviation:
        return {
            "message": "Course abbreviation already exists."
        }, 409


    course.course_code = course_code
    course.course_name = course_name
    course.course_abbreviation = course_abbreviation
    course.program_level = program_level
    course.department_id = department_id
    course.study_shift = study_shift
    course.session = session
    course.total_semesters = total_semesters

    db.session.commit()


    return {
        "message": "Course updated successfully"
    }


# =========================================================
# ACTIVATE / DEACTIVATE
# =========================================================

@courses_bp.route(
    "/<int:course_id>/status",
    methods=["PATCH"]
)
@roles_required("admin")
def toggle_course_status(course_id):

    course = Course.query.get_or_404(course_id)

    data = request.get_json(silent=True) or {}

    if "is_active" not in data:
        return {
            "message": "is_active is required."
        }, 400


    if not isinstance(data["is_active"], bool):
        return {
            "message": "is_active must be true or false."
        }, 400


    course.is_active = data["is_active"]

    db.session.commit()


    return {
        "message": (
            "Course activated successfully"
            if course.is_active
            else "Course deactivated successfully"
        ),
        "is_active": course.is_active
    }