from flask import Blueprint, request
from app import db
from app.models.subject import Subject

subjects_bp = Blueprint("subjects", __name__)


@subjects_bp.route("/", methods=["GET"])
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
def create_subject():
    data = request.get_json()

    subject = Subject(
        subject_code=data["subject_code"],
        subject_name=data["subject_name"],
        course_id=data["course_id"],
        semester=data["semester"],
        subject_type=data["subject_type"]
    )

    db.session.add(subject)
    db.session.commit()

    return {
        "message": "Subject created successfully",
        "id": subject.id
    }, 201