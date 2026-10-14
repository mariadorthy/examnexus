from functools import wraps

from flask import g, jsonify

from app.auth.security import decode_access_token


def _set_current_user(payload: dict) -> None:
    """
    Store the decoded JWT payload on flask.g so that any route
    handler or service can read the caller's identity without
    re-decoding the token.

    Fields guaranteed to be present after this call:
        g.current_user["sub"]   — string user-id (from JWT "sub")
        g.current_user["role"]  — e.g. "admin", "staff", "student"

    Additional JWT claims (e.g. "iat", "exp") are also forwarded.
    """
    g.current_user = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        # Forward any extra claims the token carries so callers
        # such as download_pdf can read student_id if it's present.
        **payload,
    }


def login_required(view_function):

    @wraps(view_function)
    def wrapped(*args, **kwargs):

        payload = decode_access_token()

        if not payload:
            return jsonify({
                "success": False,
                "message": "Authentication required."
            }), 401

        _set_current_user(payload)

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

            # Populate g.current_user so every protected route can
            # read caller identity without repeating token decode.
            _set_current_user(payload)

            return view_function(
                *args,
                **kwargs
            )

        return wrapped

    return decorator
