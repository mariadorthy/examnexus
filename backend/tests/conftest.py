"""
Shared pytest fixtures for the ExamNexus regression suite.

Kept deliberately small. Only fixtures that are actually
reused across multiple test modules live here.

Rule: no test logic in this file. Only setup.
"""

import pytest

from app import create_app, db  # noqa: F401


EXAMINATION_ID = 1

ADMIN_EMAIL = "admin@examnexus.edu"
ADMIN_PASSWORD = "Admin@123"


# ============================================================
# FLASK APP + APP CONTEXT
# ============================================================

@pytest.fixture(scope="session")
def app():
    """
    One Flask app for the entire test session.
    """
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture(scope="session")
def app_context(app):
    """
    Push one app context for the entire session.

    Many tests inspect the database directly. Without this
    fixture each one would need its own app_context() block.
    """
    with app.app_context():
        yield


# ============================================================
# CLIENTS
# ============================================================

@pytest.fixture(scope="session")
def client(app):
    """
    An unauthenticated test client.

    Used for RBAC checks that must reach the server without
    a bearer token.
    """
    return app.test_client()


@pytest.fixture(scope="session")
def admin_token(client):
    """
    Log in once as admin, return the JWT.

    Fails loudly if login does not succeed — there is no
    silent fallback. Auth is the first thing every run
    must prove.
    """
    resp = client.post(
        "/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "role": "admin",
        },
    )

    assert resp.status_code == 200, (
        "Admin login failed. "
        f"Status={resp.status_code} body={resp.get_json()}"
    )

    body = resp.get_json() or {}
    token = body.get("access_token")

    assert token, "Login response missing access_token"

    return token


@pytest.fixture(scope="session")
def admin_client(app, admin_token):
    """
    A test client that automatically sends the admin JWT
    on every request.
    """
    client = app.test_client()
    original_open = client.open

    def open_with_auth(*args, **kwargs):
        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault(
            "Authorization",
            f"Bearer {admin_token}",
        )
        kwargs["headers"] = headers
        return original_open(*args, **kwargs)

    client.open = open_with_auth
    return client


# ============================================================
# SMALL CONSTANTS EXPOSED TO TESTS
# ============================================================

@pytest.fixture(scope="session")
def examination_id():
    """
    The single examination used across the suite.
    """
    return EXAMINATION_ID