from flask import Blueprint, request
from app import db
from app.models.course import Course

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/", methods=["GET"])
def get_courses():
    courses = Course.query.all()

    return [
        {
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "course_abbreviation": course.course_abbreviation,
            "program_level": course.program_level,
            "department_id": course.department_id,
            "total_semesters": course.total_semesters,
            "is_active": course.is_active
        }
        for course in courses
    ]


@courses_bp.route("/", methods=["POST"])
def create_course():
    data = request.get_json()

    course = Course(
        course_code=data["course_code"],
        course_name=data["course_name"],
        course_abbreviation=data["course_abbreviation"],
        program_level=data["program_level"],
        department_id=data["department_id"],
        study_shift=data["study_shift"],
        session=data["session"],
        total_semesters=data["total_semesters"]
    )

    db.session.add(course)
    db.session.commit()

    return {
        "message": "Course created successfully",
        "id": course.id
    }, 201