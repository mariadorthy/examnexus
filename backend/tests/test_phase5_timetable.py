"""
Phase 5 — Timetable entries.
"""

from app import db
from app.models.timetable import Timetable


def _timetables(examination_id):
    return (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
        )
        .all()
    )


def test_timetable_entries_exist(app_context, examination_id):
    assert len(_timetables(examination_id)) > 0


def test_timetable_entries_have_no_duplicate_ids(
    app_context, examination_id
):
    ids = [t.id for t in _timetables(examination_id)]
    assert len(ids) == len(set(ids))


def test_all_timetable_entries_belong_to_target_examination(
    app_context, examination_id
):
    for entry in _timetables(examination_id):
        assert entry.examination_id == examination_id


def test_all_timetable_entries_have_exam_dates(
    app_context, examination_id
):
    for entry in _timetables(examination_id):
        assert entry.exam_date is not None