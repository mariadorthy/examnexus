"""
Natural-language database query API.

Feature 19 / Phase 9.

READ-ONLY. Admin-only.

- Interprets an administrator's question.
- Returns a structured, safe answer.
- Rejects unsupported, empty, malformed, mutating, or SQL-like input.
- Never accepts or executes arbitrary SQL.
"""

from flask import Blueprint, jsonify, request

from app.auth.decorators import roles_required
from app.services.natural_language_query_parser import parse_query
from app.services.natural_language_query import execute_query


nl_queries_bp = Blueprint(
    "nl_queries",
    __name__,
    url_prefix="/api/nl-queries",
)


@nl_queries_bp.route("/ask", methods=["POST"])
@roles_required("admin")
def ask_natural_language_query():
    """
    Accept a natural-language data question and return a read-only answer.

    Expected JSON:
    {
        "question": "How many students are allocated to Hall H204?"
    }
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    question = data.get("question")

    if not isinstance(question, str):
        return jsonify({
            "success": False,
            "message": "The 'question' field must be a string.",
        }), 400

    parsed = parse_query(question)

    if not parsed["success"]:
        return jsonify(parsed), 400

    result = execute_query(parsed["intent"], parsed["params"])

    if not result["success"]:
        return jsonify({
            "success": False,
            "intent": parsed["intent"],
            "params": parsed["params"],
            "message": result["message"],
            "data": None,
        }), 400

    return jsonify({
        "success": True,
        "intent": parsed["intent"],
        "params": parsed["params"],
        "message": result["message"],
        "data": result["data"],
    }), 200