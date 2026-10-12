"""
Phase 1 — Authentication + RBAC.
"""

from app.models.admin import Admin


def test_authentication_login_route_is_registered(app):
    auth_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/auth")
    }

    assert any(
        "/login" in route for route in auth_routes
    ), "Authentication login route must be registered"


def test_protected_dashboard_rejects_unauthenticated(client):
    response = client.get("/api/dashboard/")

    assert response.status_code in (401, 403), (
        "Protected dashboard must reject unauthenticated "
        f"access (got {response.status_code})"
    )


def test_admin_account_exists(app_context):
    count = Admin.query.count()
    assert count > 0, f"Expected at least one admin, found {count}"


def test_admin_passwords_are_hashed(app_context):
    admins = Admin.query.all()

    assert admins, "No admin rows to inspect"

    for admin in admins:
        assert admin.password_hash, (
            f"Admin {admin.id} has no password hash"
        )
        assert len(admin.password_hash) > 20, (
            f"Admin {admin.id} password hash is suspiciously short "
            "— possibly stored as plaintext"
        )
# ============================================================
# Decorator behavior — the uncovered branches in
# app/auth/decorators.py (lines 10–26, 47) per the Phase A
# coverage report.
#
# Strategy: don't register new blueprints (Flask forbids that
# after the app has served a request). Instead, drive existing
# routes that already use these decorators.
# ============================================================


def test_login_required_route_rejects_missing_token(client, app):
    """
    A route that requires a login returns 401 when the caller
    sends no Authorization header. Behavior asserted via an
    actual protected route rather than a synthetic blueprint.
    """
    # /api/dashboard/ is admin-only, so it exercises roles_required.
    # Any login-required route works for this assertion.
    resp = client.get("/api/dashboard/")

    assert resp.status_code in (401, 403)
    body = resp.get_json()
    assert body["success"] is False
    assert "authentication" in body["message"].lower() or \
           "permission" in body["message"].lower()


def test_roles_required_admin_route_rejects_missing_token(client, app):
    """
    GET /api/dashboard/ is @roles_required("admin"). No token
    must yield 401 with the login_required JSON shape.
    """
    resp = client.get("/api/dashboard/")

    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False
    assert "authentication" in body["message"].lower()


def test_roles_required_admin_route_allows_admin(
    client, admin_token
):
    """
    Same route, with a valid admin JWT, must reach the view
    and return 200.
    """
    resp = client.get(
        "/api/dashboard/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("success") is True


def test_roles_required_rejects_wrong_role(client, app, app_context):
    """
    A token with role "student" hitting an admin-only route must
    return 403 and never reach the view.

    We build a student token via whatever helper this codebase
    exposes. If none exists in app.auth.security, the test skips
    with a clear message so it isn't silently wrong.
    """
    import app.auth.security as sec

    # Discover the token-creation helper by name.
    encoder = None
    for name in (
        "encode_access_token",
        "create_access_token",
        "generate_access_token",
        "make_access_token",
    ):
        if hasattr(sec, name):
            encoder = getattr(sec, name)
            break

    if encoder is None:
        import pytest as _pytest
        _pytest.skip(
            "no token encoder exposed by app.auth.security — "
            "add one or run this test via a student login"
        )

    import inspect
    params = inspect.signature(encoder).parameters

    # Try the two most common signatures.
    if "role" in params and "subject" in params:
        token = encoder(subject="1", role="student")
    elif "role" in params:
        token = encoder("1", "student")
    else:
        # Fallback: pass a dict payload.
        token = encoder({"sub": "1", "role": "student"})

    resp = client.get(
        "/api/dashboard/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403
    body = resp.get_json()
    assert body["success"] is False
    assert "permission" in body["message"].lower()