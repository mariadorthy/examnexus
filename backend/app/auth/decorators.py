from functools import wraps

from flask import jsonify

from app.auth.security import decode_access_token


def login_required(view_function):

    @wraps(view_function)
    def wrapped(*args, **kwargs):

        payload = decode_access_token()

        if not payload:
            return jsonify({
                "success": False,
                "message": "Authentication required."
            }), 401

        return view_function(
            *args,
            **kwargs
        )

    return wrapped


def roles_required(*allowed_roles):

    def decorator(view_function):

        @wraps(view_function)
        def wrapped(*args, **kwargs):

            payload = decode_access_token()

            if not payload:
                return jsonify({
                    "success": False,
                    "message": "Authentication required."
                }), 401

            user_role = payload.get("role")

            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "You do not have permission to access this resource."
                }), 403

            return view_function(
                *args,
                **kwargs
            )

        return wrapped

    return decorator
