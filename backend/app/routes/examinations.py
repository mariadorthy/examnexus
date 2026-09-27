from flask import Blueprint, request
from app import db
from app.models.examination import Examination
from app.models.course import Course
from app.auth.decorators import roles_required
examinations_bp = Blueprint("examinations", __name__)

@examinations_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_examinations():
    examinations = Examination.query.all()

    return [
    {
        "id": examination.id,
        "name": examination.name,
        "exam_type": examination.exam_type,
        "course_id": examination.course_id,
        "course_name": (
            examination.course.course_name
            if examination.course
            else None
        ),
        "semester": examination.semester,
        "start_date": examination.start_date.isoformat(),
        "end_date": examination.end_date.isoformat(),
        "duration_minutes": examination.duration_minutes,
        "session_config": examination.session_config,
        "excluded_dates": examination.excluded_dates,
        "status": examination.status
    }
    for examination in examinations
]

@examinations_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_examination():
    data = request.get_json(silent=True) or {}

    from datetime import date

    required_fields = [
        "name",
        "exam_type",
        "course_id",
        "semester",
        "start_date",
        "end_date",
        "duration_minutes",
    ]

    for field in required_fields:
        if field not in data:
            return {
                "success": False,
                "message": f"Missing required field: {field}"
            }, 400

    try:
        start_date = date.fromisoformat(
            data["start_date"]
        )

        end_date = date.fromisoformat(
            data["end_date"]
        )

        if start_date > end_date:
            return {
                "success": False,
                "message": "Start date cannot be after end date."
            }, 400

        duration_minutes = int(
            data["duration_minutes"]
        )

        if duration_minutes <= 0:
            return {
                "success": False,
                "message": "Duration must be greater than zero."
            }, 400

        examination = Examination(
            name=data["name"].strip(),
            exam_type=data["exam_type"].strip().upper(),
            course_id=int(data["course_id"]),
            semester=int(data["semester"]),
            start_date=start_date,
            end_date=end_date,
            duration_minutes=duration_minutes,
            session_config=data.get("session_config", []),
            excluded_dates=data.get("excluded_dates", []),
            status="DRAFT"
        )

        db.session.add(examination)
        db.session.commit()

        return {
            "success": True,
            "message": "Examination created successfully.",
            "id": examination.id
        }, 201

    except (ValueError, TypeError) as exc:
        db.session.rollback()

        return {
            "success": False,
            "message": str(exc)
        }, 400

@examinations_bp.route("/bulk", methods=["POST"])
@roles_required("admin")
def create_bulk_examinations():
    data = request.get_json(silent=True) or {}

    from datetime import date

    required_fields = [
        "name",
        "exam_type",
        "selections",
        "start_date",
        "end_date",
        "duration_minutes",
    ]

    for field in required_fields:
        if field not in data:
            return {
                "success": False,
                "message": f"Missing required field: {field}"
            }, 400

    try:
        name = data["name"].strip()
        exam_type = data["exam_type"].strip().upper()

        if not name:
            raise ValueError("Examination name is required.")

        if not isinstance(data["selections"], list):
            raise ValueError("Selections must be a list.")

        if not data["selections"]:
            raise ValueError(
                "At least one course and semester must be selected."
            )

        start_date = date.fromisoformat(
            data["start_date"]
        )

        end_date = date.fromisoformat(
            data["end_date"]
        )

        if start_date > end_date:
            raise ValueError(
                "Start date cannot be after end date."
            )

        duration_minutes = int(
            data["duration_minutes"]
        )

        if duration_minutes <= 0:
            raise ValueError(
                "Duration must be greater than zero."
            )

        session_config = data.get(
            "session_config",
            []
        )

        excluded_dates = data.get(
            "excluded_dates",
            []
        )

        created = []
        skipped = []

        for selection in data["selections"]:
            course_id = int(
                selection["course_id"]
            )

            semesters = selection.get(
                "semesters",
                []
            )

            course = db.session.get(
                Course,
                course_id
            )

            if not course:
                raise ValueError(
                    f"Course {course_id} was not found."
                )

            if not semesters:
                raise ValueError(
                    f"No semesters selected for "
                    f"{course.course_name}."
                )

            for semester in semesters:
                semester = int(semester)

                if semester < 1 or semester > course.total_semesters:
                    raise ValueError(
                        f"Semester {semester} is invalid for "
                        f"{course.course_name}. "
                        f"Valid range: 1-{course.total_semesters}."
                    )

                existing = Examination.query.filter_by(
                    name=name,
                    exam_type=exam_type,
                    course_id=course_id,
                    semester=semester,
                    start_date=start_date,
                    end_date=end_date
                ).first()

                if existing:
                    skipped.append({
                        "course_id": course_id,
                        "course_name": course.course_name,
                        "semester": semester,
                        "reason": "Already exists"
                    })
                    continue

                examination = Examination(
                    name=name,
                    exam_type=exam_type,
                    course_id=course_id,
                    semester=semester,
                    start_date=start_date,
                    end_date=end_date,
                    duration_minutes=duration_minutes,
                    session_config=session_config,
                    excluded_dates=excluded_dates,
                    status="DRAFT"
                )

                db.session.add(examination)
                created.append({
                    "course_id": course_id,
                    "course_name": course.course_name,
                    "semester": semester
                })

        db.session.commit()

        return {
            "success": True,
            "message": "Bulk examinations created successfully.",
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created": created,
            "skipped": skipped
        }, 201

    except (ValueError, TypeError, KeyError) as exc:
        db.session.rollback()

        return {
            "success": False,
            "message": str(exc)
        }, 400
        
@examinations_bp.route(
    "/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def get_examination(examination_id):
    examination = db.session.get(
        Examination,
        examination_id
    )

    if not examination:
        return {
            "success": False,
            "message": "Examination not found."
        }, 404

    return {
        "id": examination.id,
        "name": examination.name,
        "exam_type": examination.exam_type,
        "course_id": examination.course_id,
        "course_name": (
            examination.course.course_name
            if examination.course
            else None
        ),
        "semester": examination.semester,
        "start_date": examination.start_date.isoformat(),
        "end_date": examination.end_date.isoformat(),
        "duration_minutes": examination.duration_minutes,
        "session_config": examination.session_config,
        "excluded_dates": examination.excluded_dates,
        "status": examination.status
    }

@examinations_bp.route(
    "/<int:examination_id>",
    methods=["PUT"]
)
@roles_required("admin")
def update_examination(examination_id):
    data = request.get_json(silent=True) or {}

    examination = db.session.get(
        Examination,
        examination_id
    )

    if not examination:
        return {
            "success": False,
            "message": "Examination not found."
        }, 404

    from datetime import date

    try:
        if "name" in data:
            examination.name = data["name"].strip()

        if "exam_type" in data:
            examination.exam_type = (
                data["exam_type"].strip().upper()
            )

        if "course_id" in data:
            examination.course_id = int(
                data["course_id"]
            )

        if "semester" in data:
            examination.semester = int(
                data["semester"]
            )

        if "start_date" in data:
            examination.start_date = date.fromisoformat(
                data["start_date"]
            )

        if "end_date" in data:
            examination.end_date = date.fromisoformat(
                data["end_date"]
            )

        if "duration_minutes" in data:
            examination.duration_minutes = int(
                data["duration_minutes"]
            )

        if "session_config" in data:
            examination.session_config = (
                data["session_config"]
            )

        if "excluded_dates" in data:
            examination.excluded_dates = (
                data["excluded_dates"]
            )

        if examination.start_date > examination.end_date:
            raise ValueError(
                "Start date cannot be after end date."
            )

        db.session.commit()

        return {
            "success": True,
            "message": "Examination updated successfully."
        }

    except (ValueError, TypeError) as exc:
        db.session.rollback()

        return {
            "success": False,
            "message": str(exc)
        }, 400