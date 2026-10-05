from flask import Blueprint, request

from app.auth.decorators import roles_required

from app.services.hall_ticket import (
    generate_hall_tickets,
    get_hall_ticket,
    verify_hall_ticket
)


hall_tickets_bp = Blueprint("hall_tickets", __name__)


@hall_tickets_bp.route(
    "/generate/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def generate(examination_id):

    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))

    result = generate_hall_tickets(
        examination_id,
        force=force
    )

    return result, (200 if result.get("success") else 400)


@hall_tickets_bp.route(
    "/<int:examination_id>/<int:student_id>",
    methods=["GET"]
)
@roles_required("admin")
def fetch_one(examination_id, student_id):

    result = get_hall_ticket(student_id, examination_id)

    return result, (200 if result.get("success") else 404)


@hall_tickets_bp.route(
    "/verify/<string:verification_token>",
    methods=["GET"]
)
def verify(verification_token):

    # Public endpoint. No auth required. Returns only safe fields.
    result = verify_hall_ticket(verification_token)

    return result, (200 if result.get("valid") else 404)