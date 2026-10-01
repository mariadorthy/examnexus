from flask import Blueprint, request

from app import db
from app.models.exam_registration import ExamRegistration
from app.auth.decorators import roles_required
from app.services.exam_registration import (
    preview_bulk_registration,
    create_bulk_registrations,
)
exam_registrations_bp = Blueprint(
    "exam_registrations",
    __name__
)


@exam_registrations_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_exam_registrations():
    registrations = ExamRegistration.query.all()

    return [
        {
        "id": registration.id,
        "student_id": registration.student_id,
        "examination_id": registration.examination_id,
        "status": registration.status,
        "fee_status": registration.fee_status,
        "registered_at": registration.registered_at.isoformat()
        }
        for registration in registrations
    ]


@exam_registrations_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_exam_registration():
    data = request.get_json()

    registration = ExamRegistration(
    student_id=data["student_id"],
    examination_id=data["examination_id"],
    fee_status="PENDING"
)

    db.session.add(registration)
    db.session.commit()

    return {
        "message": "Student registered for examination successfully",
        "id": registration.id
    }, 201

@exam_registrations_bp.route(
    "/<int:registration_id>/fee-status",
    methods=["PATCH"]
)
@roles_required("admin")
def update_fee_status(registration_id):
    registration = ExamRegistration.query.get(
        registration_id
    )

    if not registration:
        return {
            "success": False,
            "message": "Exam registration not found"
        }, 404

    data = request.get_json() or {}
    fee_status = data.get("fee_status")

    if fee_status not in ["PENDING", "PAID"]:
        return {
            "success": False,
            "message": "fee_status must be PENDING or PAID"
        }, 400

    registration.fee_status = fee_status

    db.session.commit()

    return {
        "success": True,
        "message": "Fee status updated successfully",
        "registration_id": registration.id,
        "fee_status": registration.fee_status
    }

@exam_registrations_bp.route(
    "/bulk-preview",
    methods=["POST"]
)
@roles_required("admin")
def bulk_preview():
    data = request.get_json() or {}

    examination_id = data.get("examination_id")

    if not examination_id:
        return {
            "success": False,
            "message": "examination_id is required"
        }, 400

    result = preview_bulk_registration(
        examination_id=examination_id,
        course_id=data.get("course_id"),
        semester=data.get("semester"),
        batch=data.get("batch"),
        active_only=data.get("active_only", True),
    )

    if not result["success"]:
        return result, 400

    return result, 200


@exam_registrations_bp.route(
    "/bulk",
    methods=["POST"]
)
@roles_required("admin")
def bulk_create():
    data = request.get_json() or {}

    examination_id = data.get("examination_id")

    if not examination_id:
        return {
            "success": False,
            "message": "examination_id is required"
        }, 400

    try:
        result = create_bulk_registrations(
            examination_id=examination_id,
            course_id=data.get("course_id"),
            semester=data.get("semester"),
            batch=data.get("batch"),
            active_only=data.get("active_only", True),
        )

        if not result["success"]:
            return result, 400

        return result, 201

    except Exception as error:
        return {
            "success": False,
            "message": "Failed to create bulk registrations",
            "error": str(error),
        }, 500