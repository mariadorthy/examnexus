from flask import Blueprint, request

from app.auth.decorators import roles_required

from app.services.hall_ticket import (
    generate_hall_tickets,
    get_hall_ticket,
    get_hall_ticket_pdf,
    verify_hall_ticket,
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
    #
    # Wire contract:
    #   200 + {valid: true,  ...}                          -> current, authentic ticket
    #   200 + {valid: false, status: "SUPERSEDED", ...}    -> token resolved; state is terminal
    #   200 + {valid: false, status: "INVALIDATED", ...}   -> token resolved; state is terminal
    #   404 + {valid: false, message: "Ticket not found"}  -> token did not resolve to any row
    #
    # Only a token that resolves to NO row is a real 404. A token that
    # resolves to a known ticket with a terminal status is a found
    # resource whose state is invalid; the body still carries safe
    # identity/exam fields so the public page can explain why.
    result = verify_hall_ticket(verification_token)

    if result.get("valid"):
        return result, 200

    if result.get("status") in ("SUPERSEDED", "INVALIDATED"):
        return result, 200

    return result, 404

@hall_tickets_bp.route(
    "/download/<int:examination_id>/<int:student_id>",
    methods=["GET"]
)
@roles_required("student", "admin")
def download_pdf(examination_id, student_id):

    # roles_required injects identity via flask.g in your auth layer.
    from flask import g

    requester = getattr(g, "current_user", None) or {}
    role = requester.get("role")
    # Student tokens identify the account by ``sub``; they carry no
    # separate student_id claim. The Student primary key is that subject.
    requester_student_id = None
    if role == "student":
        try:
            requester_student_id = int(requester.get("sub"))
        except (TypeError, ValueError):
            requester_student_id = None

    result = get_hall_ticket_pdf(
        student_id=student_id,
        examination_id=examination_id,
        requester_role=role,
        requester_id=requester_student_id,
    )

    if not result.get("success"):
        # Preserve the 404 vs 403 distinction the UI relies on.
        status = (
            403
            if "Not authorized" in (result.get("message") or "")
            else 404
        )
        return result, status

    from flask import Response

    return Response(
        result["pdf_bytes"],
        mimetype=result["content_type"],
        headers={
            "Content-Disposition": (
                f'attachment; filename="{result["filename"]}"'
            ),
            "Cache-Control": "no-store",
        },
    )
