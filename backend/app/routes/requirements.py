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