"""
Phase 4 — Examination creation.
"""

from app import db
from app.models.examination import Examination


def test_examination_records_exist(app_context):
    assert Examination.query.count() > 0


def test_target_examination_exists(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination is not None


def test_examination_has_name(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination and examination.name


def test_examination_linked_to_course(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination and examination.course_id is not None


def test_examination_has_semester(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination and examination.semester is not None


def test_examination_has_valid_date_range(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination
    assert examination.start_date is not None
    assert examination.end_date is not None


def test_examination_has_valid_duration(app_context, examination_id):
    examination = db.session.get(Examination, examination_id)
    assert examination
    assert examination.duration_minutes is not None
    assert examination.duration_minutes > 0