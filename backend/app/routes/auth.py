from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash

from app.models.admin import Admin
from app.models.staff import Staff
from app.models.student import Student
from app.auth.security import create_access_token


auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not email or not password or not role:
        return jsonify({
            "success": False,
            "message": "Email, password and role are required."
        }), 400

    email = email.strip().lower()
    role = role.strip().lower()

    if role == "admin":

        user = Admin.query.filter_by(
            email=email
        ).first()

    elif role == "staff":

        user = Staff.query.filter_by(
            email=email
        ).first()

    elif role == "student":

        user = Student.query.filter_by(
            email=email
        ).first()

    else:

        return jsonify({
            "success": False,
            "message": "Invalid role."
        }), 400

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if not user.is_active:

        return jsonify({
            "success": False,
            "message": "This account is inactive."
        }), 403

    if not check_password_hash(
        user.password_hash,
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    token = create_access_token(
        user.id,
        role
    )

    return jsonify({

        "success": True,

        "message": "Login successful.",

        "access_token": token,

        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role
        }

    }), 200


@auth_bp.route("/verify", methods=["GET"])
def verify():

    from app.auth.security import decode_access_token

    payload = decode_access_token()

    if not payload:

        return jsonify({
            "success": False,
            "message": "Invalid or expired token."
        }), 401

    role = payload.get("role")
    user_id = payload.get("sub")

    if role == "admin":
        user = Admin.query.get(user_id)

    elif role == "staff":
        user = Staff.query.get(user_id)

    elif role == "student":
        user = Student.query.get(user_id)

    else:
        user = None

    if not user:

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 401

    if not user.is_active:

        return jsonify({
            "success": False,
            "message": "This account is inactive."
        }), 403

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role
        }
    }), 200
