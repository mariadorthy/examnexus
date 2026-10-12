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

# ============================================================
# Service-level tests for app/services/timetable.py
#
# The original Phase 5 tests are DB-state checks. These tests
# drive the service functions directly to cover validation
# branches the previous suite doesn't exercise.
# ============================================================

import pytest
from datetime import date, time, timedelta

from app.services.timetable import (
    get_session_time,
    get_examination_session_times,
    get_available_dates,
    validate_timetable_entry,
    update_timetable_entry,
)
from app.models.subject import Subject


def test_get_session_time_returns_default_fixed_times():
    """FN and AN return the module default session times."""
    start, end = get_session_time("FN")
    assert start == time(10, 0)
    assert end == time(13, 0)

    start, end = get_session_time("AN")
    assert start == time(14, 0)
    assert end == time(17, 0)


def test_get_session_time_rejects_unknown_session():
    """Anything other than FN/AN is a hard error."""
    with pytest.raises(ValueError) as exc:
        get_session_time("EVENING")

    assert "invalid session" in str(exc.value).lower()


def test_get_available_dates_excludes_sundays_and_excluded():
    """Sundays and explicit exclusions are removed; the rest survive."""
    # Monday 2026-03-02 .. Sunday 2026-03-08
    start = date(2026, 3, 2)
    end = date(2026, 3, 8)
    excluded = {date(2026, 3, 4)}  # Wednesday

    available = get_available_dates(start, end, excluded)

    # Expect Mon, Tue, Thu, Fri, Sat — six days, one Sunday removed
    # and one excluded weekday removed.
    assert date(2026, 3, 2) in available   # Mon
    assert date(2026, 3, 3) in available   # Tue
    assert date(2026, 3, 4) not in available  # excluded
    assert date(2026, 3, 5) in available   # Thu
    assert date(2026, 3, 6) in available   # Fri
    assert date(2026, 3, 7) in available   # Sat
    assert date(2026, 3, 8) not in available  # Sun
    assert len(available) == 5


def test_get_available_dates_rejects_inverted_range():
    """start_date > end_date is a hard error, not an empty list."""
    with pytest.raises(ValueError) as exc:
        get_available_dates(
            date(2026, 3, 10), date(2026, 3, 1)
        )
    assert "cannot be after" in str(exc.value).lower()


def test_validate_timetable_entry_rejects_unknown_subject(
    app_context, examination_id
):
    """A subject_id that does not exist must fail fast."""
    with pytest.raises(ValueError) as exc:
        validate_timetable_entry(
            examination_id=examination_id,
            subject_id=999999999,
            exam_date=date.today(),
            session="FN",
            start_time=time(10, 0),
            end_time=time(13, 0),
        )
    assert "subject not found" in str(exc.value).lower()


def test_validate_timetable_entry_rejects_date_outside_exam_window(
    app_context, examination_id
):
    """A date before the exam start or after the exam end is rejected."""
    from app.models.examination import Examination
    from app.models.subject import Subject
    from app import db as _db

    exam = _db.session.get(Examination, examination_id)
    assert exam is not None

    subject = (
        Subject.query
        .filter_by(
            course_id=exam.course_id, semester=exam.semester
        )
        .first()
    )
    if subject is None:
        pytest.skip("no subject for this exam's course+semester")

    too_early = exam.start_date - timedelta(days=1)

    with pytest.raises(ValueError) as exc:
        validate_timetable_entry(
            examination_id=examination_id,
            subject_id=subject.id,
            exam_date=too_early,
            session="FN",
            start_time=time(10, 0),
            end_time=time(13, 0),
        )
    assert "before" in str(exc.value).lower()


def test_validate_timetable_entry_accepts_valid_date(
    app_context, examination_id
):
    """A valid subject on a date inside the exam window returns True."""
    from app.models.examination import Examination
    from app.models.subject import Subject
    from app import db as _db

    exam = _db.session.get(Examination, examination_id)
    assert exam is not None

    subject = (
        Subject.query
        .filter_by(
            course_id=exam.course_id, semester=exam.semester
        )
        .first()
    )
    if subject is None:
        pytest.skip("no subject for this exam's course+semester")

    result = validate_timetable_entry(
        examination_id=examination_id,
        subject_id=subject.id,
        exam_date=exam.start_date,
        session="FN",
        start_time=time(10, 0),
        end_time=time(13, 0),
    )
    assert result is True


def test_update_timetable_entry_rejects_out_of_window_date(
    app_context, examination_id
):
    """Update cannot move an entry outside the exam window."""
    from app.models.examination import Examination
    from app import db as _db

    exam = _db.session.get(Examination, examination_id)
    entries = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .all()
    )
    if not entries:
        pytest.skip("no timetable entries to update")
    entry = entries[0]

    too_early = exam.start_date - timedelta(days=1)

    with pytest.raises(ValueError) as exc:
        update_timetable_entry(
            timetable_id=entry.id,
            exam_date=too_early,
            session=entry.session,
        )
    assert "before" in str(exc.value).lower()