from flask import Blueprint, request
from app import db
from app.models.examination import Examination
from app.auth.decorators import roles_required
examinations_bp = Blueprint("examinations", __name__)

@examinations_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_examinations():
    examinations = Examination.query.all()

    return [
        {
            "id": examination.id,
            "subject_id": examination.subject_id,
            "exam_date": examination.exam_date.isoformat(),
            "session": examination.session,
            "start_time": examination.start_time.strftime("%H:%M"),
            "end_time": examination.end_time.strftime("%H:%M"),
            "duration_minutes": examination.duration_minutes,
            "exam_type": examination.exam_type,
            "status": examination.status
        }
        for examination in examinations
    ]


@examinations_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_examination():
    data = request.get_json()

    from datetime import date, time

    examination = Examination(
        subject_id=data["subject_id"],
        exam_date=date.fromisoformat(data["exam_date"]),
        session=data["session"],
        start_time=time.fromisoformat(data["start_time"]),
        end_time=time.fromisoformat(data["end_time"]),
        duration_minutes=data["duration_minutes"],
        exam_type=data["exam_type"]
    )

    db.session.add(examination)
    db.session.commit()

    return {
        "message": "Examination created successfully",
        "id": examination.id
    }, 201