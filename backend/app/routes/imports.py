from flask import Blueprint, jsonify, request

from app.auth.decorators import roles_required
from app.services.csv_import_service import (
    normalize_entity,
    validate_csv_file,
    validate_csv,
    import_valid_rows,
)


imports_bp = Blueprint(
    "imports",
    __name__,
    url_prefix="/api/import",
)


@imports_bp.route("/<entity>/validate", methods=["POST"])
@roles_required("admin")
def validate_import(entity):
    """
    Validate an uploaded CSV without inserting anything
    into the database.
    """

    normalized_entity = normalize_entity(entity)

    if not normalized_entity:
        return jsonify({
            "success": False,
            "message": "Unsupported import entity.",
        }), 400

    file = request.files.get("file")

    file_result = validate_csv_file(file)

    if not file_result["success"]:
        return jsonify(file_result), 400

    validation_result = validate_csv(
        normalized_entity,
        file_result["content"],
    )

    if not validation_result["success"]:
        return jsonify(validation_result), 400

    return jsonify(validation_result), 200


@imports_bp.route("/<entity>/import", methods=["POST"])
@roles_required("admin")
def import_csv(entity):
    """
    Validate and import an uploaded CSV.

    The CSV is validated again immediately before import.
    The backend never trusts validation data supplied by
    the frontend.
    """

    normalized_entity = normalize_entity(entity)

    if not normalized_entity:
        return jsonify({
            "success": False,
            "message": "Unsupported import entity.",
        }), 400

    file = request.files.get("file")

    file_result = validate_csv_file(file)

    if not file_result["success"]:
        return jsonify(file_result), 400

    validation_result = validate_csv(
        normalized_entity,
        file_result["content"],
    )

    if not validation_result["success"]:
        return jsonify(validation_result), 400

    if validation_result["valid_rows"] == 0:
        return jsonify({
            "success": False,
            "message": (
                "There are no valid rows available for import."
            ),
            "validation": validation_result,
        }), 400

    import_result = import_valid_rows(
        normalized_entity,
        validation_result,
    )

    if not import_result["success"]:
        return jsonify(import_result), 500

    return jsonify({
        "success": True,
        "message": (
            f"{import_result['imported_rows']} "
            f"{normalized_entity} record(s) imported successfully."
        ),
        "validation": validation_result,
        "summary": import_result,
    }), 200