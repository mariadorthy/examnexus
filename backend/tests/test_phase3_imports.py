"""
Phase 3 — CSV import + manual CRUD.

Presence checks only. Phase 3 is marked
IMPLEMENTED / VERIFICATION PENDING in the project
tracker; this file proves the routes exist and the
imported data is reachable, nothing more.
"""

from app.models.student import Student
from app.models.staff import Staff
from app.models.subject import Subject


def test_csv_import_routes_are_registered(app):
    import_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/import")
    }

    assert len(import_routes) > 0, (
        "No /api/import routes registered"
    )


def test_student_records_available_after_import(app_context):
    assert Student.query.count() > 0


def test_staff_records_available_after_import(app_context):
    assert Staff.query.count() > 0


def test_subject_records_available_after_import(app_context):
    assert Subject.query.count() > 0