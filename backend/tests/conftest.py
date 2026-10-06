"""
Shared pytest fixtures for the ExamNexus regression suite.

Kept deliberately small. Only fixtures that are actually
reused across multiple test modules live here.

Rule: no test logic in this file. Only setup.
"""

import os

import pytest
from dotenv import load_dotenv
from app import create_app, db  # noqa: F401
load_dotenv(".env.test")

EXAMINATION_ID = 1

ADMIN_EMAIL = "admin@examnexus.edu"
ADMIN_PASSWORD = "Admin@123"


# ============================================================
# FLASK APP + APP CONTEXT
# ============================================================
@pytest.fixture(scope="session")
def app():
    test_db_url = os.getenv("TEST_DATABASE_URL")

    assert test_db_url, (
        "TEST_DATABASE_URL is missing. "
        "Check backend/.env.test"
    )

    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_url,
    })

    assert flask_app.config["SQLALCHEMY_DATABASE_URI"] == test_db_url

    return flask_app
    
@pytest.fixture(scope="session")
def app_context(app):
    """
    Push one app context for the entire session.

    Also ensures the shared test admin account exists.
    """
    with app.app_context():
        from app.models.admin import Admin
        from werkzeug.security import generate_password_hash

        admin = Admin.query.filter_by(
            email=ADMIN_EMAIL
        ).first()

        if admin is None:
            admin = Admin(
                name="Test Admin",
                email=ADMIN_EMAIL,
                password_hash=generate_password_hash(
                    ADMIN_PASSWORD
                ),
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()
        yield

@pytest.fixture(scope="session", autouse=True)
def clean_phase7_allocations(app_context):
    """
    Prepare a controlled Phase 7 test database.

    Generated allocation records are cleared first.
    If the required examination/test data do not exist,
    the controlled Phase 7 fixture creates them.
    """

    from app.models.seat_allocation import SeatAllocation
    from app.models.invigilator_allocation import (
        InvigilatorAllocation
    )
    from app.models.hall_allocation import HallAllocation
    from app.models.examination import Examination

    SeatAllocation.query.delete(
        synchronize_session=False
    )

    InvigilatorAllocation.query.delete(
        synchronize_session=False
    )

    HallAllocation.query.delete(
        synchronize_session=False
    )

    db.session.commit()

    # Create controlled Phase 7 data when the test database
    # does not already contain Examination #1.
    if Examination.query.get(EXAMINATION_ID) is None:
        from tests.fixtures.phase7_data import seed_phase7_data

        seed_phase7_data()

    from app.models.seat_allocation import SeatAllocation
    from app.models.invigilator_allocation import (
        InvigilatorAllocation
    )
    from app.models.hall_allocation import HallAllocation

    SeatAllocation.query.delete(
        synchronize_session=False
    )

    InvigilatorAllocation.query.delete(
        synchronize_session=False
    )

    HallAllocation.query.delete(
        synchronize_session=False
    )

    db.session.commit()


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
def admin_token(client, app_context):
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