from flask import Blueprint, request
from app import db
from app.models.exam_registration import ExamRegistration

exam_registrations_bp = Blueprint(
    "exam_registrations",
    __name__
)


@exam_registrations_bp.route("/", methods=["GET"])
def get_exam_registrations():
    registrations = ExamRegistration.query.all()

    return [
        {
            "id": registration.id,
            "student_id": registration.student_id,
            "examination_id": registration.examination_id,
            "status": registration.status,
            "registered_at": registration.registered_at.isoformat()
        }
        for registration in registrations
    ]


@exam_registrations_bp.route("/", methods=["POST"])
def create_exam_registration():
    data = request.get_json()

    registration = ExamRegistration(
        student_id=data["student_id"],
        examination_id=data["examination_id"]
    )

    db.session.add(registration)
    db.session.commit()

    return {
        "message": "Student registered for examination successfully",
        "id": registration.id
    }, 201