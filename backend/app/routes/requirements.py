"""
Natural-language requirement understanding API.

Feature 18 / Phase 8 enhancement.

Only authenticated administrators can use this endpoint.

The endpoint:
1. Accepts natural-language requirements.
2. Sends them to the deterministic parser.
3. Validates the structured output.
4. Returns recognized and unsupported requirements.

It does NOT:
- modify the database
- create/update examinations
- allocate halls
- allocate seats
- allocate invigilators
- approve examinations
- publish examinations
"""

from flask import Blueprint, jsonify, request

from app.auth.decorators import roles_required
from app.services.requirement_parser import parse_requirements


requirements_bp = Blueprint(
    "requirements",
    __name__,
    url_prefix="/api/requirements",
)


@requirements_bp.route("/understand", methods=["POST"])
@roles_required("admin")
def understand_requirements():
    """
    Understand an administrator's natural-language requirements.

    Expected JSON:
    {
        "requirement": "Use minimum halls and keep accessibility students in accessible halls."
    }
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    requirement = data.get("requirement")

    if not isinstance(requirement, str):
        return jsonify({
            "success": False,
            "message": "The 'requirement' field must be a string.",
        }), 400

    result = parse_requirements(requirement)

    if not result["validation"]["valid"]:
        return jsonify(result), 400

    return jsonify(result), 200


@requirements_bp.route(
    "/apply/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def apply_requirements_to_allocation(examination_id):
    """
    Feature 18 → Allocation integration.

    Accepts either:
      { "requirement": "Use the minimum number of halls..." }
    or:
      { "requirements": { "minimize_halls": true, ... } }

    Dry-run by default. Only when the client sends
    {"confirm": true} together with a validated request is
    the allocator allowed to write.

    The natural-language layer never touches the DB directly;
    the deterministic allocation service remains authoritative.
    """

    from app.services.allocation_options import (
        build_allocation_options,
        describe_options,
    )
    from app.services.allocation import generate_allocation
    from app.services.validation import validate_allocation

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    confirm = bool(data.get("confirm", False))

    # ---------------------------------------------------------
    # 1. OBTAIN STRUCTURED REQUIREMENTS
    # ---------------------------------------------------------

    structured = None

    if "requirement" in data:
        raw = data.get("requirement")
        if not isinstance(raw, str):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirement' field must be a string."
                ),
            }), 400

        parsed = parse_requirements(raw)
        if not parsed["validation"]["valid"]:
            return jsonify(parsed), 400

        structured = parsed["requirements"]
        parsed_payload = parsed

    elif "requirements" in data:
        structured = data.get("requirements")
        if not isinstance(structured, dict):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirements' field must be an object."
                ),
            }), 400
        parsed_payload = None

    else:
        return jsonify({
            "success": False,
            "message": (
                "Provide either 'requirement' (natural language) "
                "or 'requirements' (structured object)."
            ),
        }), 400

    # ---------------------------------------------------------
    # 2. CONVERT TO TYPED ALLOCATION OPTIONS
    # ---------------------------------------------------------

    options_result = build_allocation_options(structured)

    if not options_result["success"]:
        return jsonify({
            "success": False,
            "message": "Invalid structured requirements.",
            "errors": options_result["errors"],
        }), 400

    options = options_result["options"]

    # Refuse to regenerate the whole allocation when the
    # requirement parsed to nothing supported. This prevents
    # a no-op or a fully-unsupported input from silently
    # replacing an existing allocation.
    if not any(options.values()):
        return jsonify({
            "success": False,
            "message": (
                "No supported requirements were identified. "
                "Nothing to apply."
            ),
            "parsed": parsed_payload,
            "allocation_options": options,
        }), 400

    # ---------------------------------------------------------
    # 3. DRY RUN (no writes)
    # ---------------------------------------------------------

    if not confirm:
        return jsonify({
            "success": True,
            "mode": "preview",
            "examination_id": examination_id,
            "parsed": parsed_payload,
            "allocation_options": options,
            "applied_options": describe_options(options),
            "message": (
                "Preview only. Send confirm=true to apply these "
                "options to a fresh allocation."
            ),
        }), 200

    # ---------------------------------------------------------
    # 4. APPLY (deterministic allocator performs the write)
    # ---------------------------------------------------------

    result = generate_allocation(
        examination_id,
        force=True,
        allocation_options=options,
    )

    if not result.get("success"):
        return jsonify(result), 400

    validation = validate_allocation(examination_id)

    return jsonify({
        "success": True,
        "mode": "applied",
        "examination_id": examination_id,
        "allocation_options": options,
        "applied_options": describe_options(options),
        "allocation": result,
        "validation": validation,
    }), 200