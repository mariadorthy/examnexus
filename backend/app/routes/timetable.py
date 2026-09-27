from datetime import date, time

from flask import Blueprint, request

from app.auth.decorators import roles_required
from app.models.timetable import Timetable
from app.services.timetable import (
    generate_timetable,
    get_timetable_for_examination,
    update_timetable_entry
)


timetable_bp = Blueprint(
    "timetable",
    __name__
)


def serialize_timetable(entry):
    return {
        "id": entry.id,
        "examination_id": entry.examination_id,
        "subject_id": entry.subject_id,
        "subject_code": (
            entry.subject.subject_code
            if entry.subject
            else None
        ),
        "subject_name": (
            entry.subject.subject_name
            if entry.subject
            else None
        ),
        "exam_date": entry.exam_date.isoformat(),
        "session": entry.session,
        "start_time": entry.start_time.strftime("%H:%M"),
        "end_time": entry.end_time.strftime("%H:%M"),
        "duration_minutes": entry.duration_minutes,
        "status": entry.status
    }

@timetable_bp.route(
    "/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def get_examination_timetable(
    examination_id
):
    entries = get_timetable_for_examination(
        examination_id
    )

    return [
        serialize_timetable(entry)
        for entry in entries
    ]


@timetable_bp.route(
    "/<int:examination_id>/generate",
    methods=["POST"]
)
@roles_required("admin")
def generate_examination_timetable(
    examination_id
):
    data = request.get_json(
        silent=True
    ) or {}

    try:
        start_date = date.fromisoformat(
            data["start_date"]
        )

        end_date = date.fromisoformat(
            data["end_date"]
        )

        subject_ids = data.get(
            "subject_ids",
            []
        )

        sessions = data.get(
            "sessions",
            []
        )

        excluded_dates = {
            date.fromisoformat(value)
            for value in data.get(
                "excluded_dates",
                []
            )
        }

        clear_existing = bool(
            data.get(
                "clear_existing",
                False
            )
        )

        entries = generate_timetable(
            examination_id=examination_id,
            subject_ids=subject_ids,
            start_date=start_date,
            end_date=end_date,
            sessions=sessions,
            excluded_dates=excluded_dates,
            clear_existing=clear_existing
        )

        return {
            "success": True,
            "message": "Timetable generated successfully.",
            "count": len(entries),
            "data": [
                serialize_timetable(entry)
                for entry in entries
            ]
        }, 201

    except KeyError as exc:
        return {
            "success": False,
            "message": f"Missing required field: {exc.args[0]}"
        }, 400

    except ValueError as exc:
        return {
            "success": False,
            "message": str(exc)
        }, 400


@timetable_bp.route(
    "/<int:timetable_id>",
    methods=["PUT"]
)
@roles_required("admin")
def update_timetable(
    timetable_id
):
    data = request.get_json(
        silent=True
    ) or {}

    try:
        exam_date = date.fromisoformat(
            data["exam_date"]
        )

        session = data["session"]

        start_time = None
        end_time = None

        if data.get("start_time"):
            start_time = time.fromisoformat(
                data["start_time"]
            )

        if data.get("end_time"):
            end_time = time.fromisoformat(
                data["end_time"]
            )

        entry = update_timetable_entry(
            timetable_id=timetable_id,
            exam_date=exam_date,
            session=session,
            start_time=start_time,
            end_time=end_time
        )

        return {
            "success": True,
            "message": "Timetable entry updated successfully.",
            "data": serialize_timetable(entry)
        }

    except KeyError as exc:
        return {
            "success": False,
            "message": f"Missing required field: {exc.args[0]}"
        }, 400

    except ValueError as exc:
        return {
            "success": False,
            "message": str(exc)
        }, 400