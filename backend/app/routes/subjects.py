from flask import Blueprint, request

from app import db
from app.auth.decorators import roles_required
from app.models.course import Course
from app.models.subject import Subject

subjects_bp = Blueprint("subjects", __name__)


@subjects_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_subjects():
    subjects = Subject.query.all()

    return [
        {
            "id": subject.id,
            "subject_code": subject.subject_code,
            "subject_name": subject.subject_name,
            "course_id": subject.course_id,
            "semester": subject.semester,
            "subject_type": subject.subject_type,
            "is_active": subject.is_active
        }
        for subject in subjects
    ]


@subjects_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_subject():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "subject_code",
        "subject_name",
        "course_id",
        "semester",
        "subject_type"
    ]

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    try:
        course_id = int(data["course_id"])
        semester = int(data["semester"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "course_id and semester must be valid numbers."
        }, 400

    course = db.session.get(Course, course_id)

    if not course:
        return {
            "success": False,
            "message": "Selected course does not exist."
        }, 400

    if semester < 1 or semester > course.total_semesters:
        return {
            "success": False,
            "message": "Semester is outside the selected course's semester range."
        }, 400

    subject_code = data["subject_code"].strip().upper()
    subject_name = data["subject_name"].strip()
    subject_type = data["subject_type"].strip().upper()

    if not subject_code or not subject_name or not subject_type:
        return {
            "success": False,
            "message": "Subject code, name, and type cannot be empty."
        }, 400

    if Subject.query.filter_by(subject_code=subject_code).first():
        return {
            "success": False,
            "message": "Subject code already exists."
        }, 409

    subject = Subject(
        subject_code=subject_code,
        subject_name=subject_name,
        course_id=course_id,
        semester=semester,
        subject_type=subject_type
    )

    db.session.add(subject)
    db.session.commit()

    return {
        "success": True,
        "message": "Subject created successfully",
        "id": subject.id
    }, 201


@subjects_bp.route("/<int:subject_id>", methods=["GET"])
@roles_required("admin")
def get_subject(subject_id):
    subject = db.session.get(Subject, subject_id)

    if not subject:
        return {
            "success": False,
            "message": "Subject not found."
        }, 404

    return {
        "id": subject.id,
        "subject_code": subject.subject_code,
        "subject_name": subject.subject_name,
        "course_id": subject.course_id,
        "semester": subject.semester,
        "subject_type": subject.subject_type,
        "is_active": subject.is_active
    }


@subjects_bp.route("/<int:subject_id>", methods=["PUT"])
@roles_required("admin")
def update_subject(subject_id):
    subject = db.session.get(Subject, subject_id)

    if not subject:
        return {
            "success": False,
            "message": "Subject not found."
        }, 404

    data = request.get_json(silent=True) or {}

    required_fields = [
        "subject_code",
        "subject_name",
        "course_id",
        "semester",
        "subject_type"
    ]

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    try:
        course_id = int(data["course_id"])
        semester = int(data["semester"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "course_id and semester must be valid numbers."
        }, 400

    course = db.session.get(Course, course_id)

    if not course:
        return {
            "success": False,
            "message": "Selected course does not exist."
        }, 400

    if semester < 1 or semester > course.total_semesters:
        return {
            "success": False,
            "message": "Semester is outside the selected course's semester range."
        }, 400

    subject_code = data["subject_code"].strip().upper()
    subject_name = data["subject_name"].strip()
    subject_type = data["subject_type"].strip().upper()

    duplicate = Subject.query.filter(
        Subject.subject_code == subject_code,
        Subject.id != subject_id
    ).first()

    if duplicate:
        return {
            "success": False,
            "message": "Subject code already exists."
        }, 409

    subject.subject_code = subject_code
    subject.subject_name = subject_name
    subject.course_id = course_id
    subject.semester = semester
    subject.subject_type = subject_type

    db.session.commit()

    return {
        "success": True,
        "message": "Subject updated successfully"
    }


@subjects_bp.route("/<int:subject_id>/status", methods=["PATCH"])
@roles_required("admin")
def update_subject_status(subject_id):
    subject = db.session.get(Subject, subject_id)

    if not subject:
        return {
            "success": False,
            "message": "Subject not found."
        }, 404

    data = request.get_json(silent=True) or {}

    if not isinstance(data.get("is_active"), bool):
        return {
            "success": False,
            "message": "is_active must be a boolean."
        }, 400

    subject.is_active = data["is_active"]
    db.session.commit()
    print(
    "SUBJECT STATUS SAVED:",
    subject.id,
    subject.subject_code,
    subject.is_active
)
    return {
        "success": True,
        "message": "Subject status updated successfully",
        "is_active": subject.is_active
    }