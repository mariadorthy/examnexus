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