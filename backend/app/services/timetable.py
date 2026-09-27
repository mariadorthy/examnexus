from datetime import datetime, date, time, timedelta

from app import db
from app.models.timetable import Timetable
from app.models.examination import Examination
from app.models.subject import Subject


SESSION_TIMES = {
    "FN": (
        time(10, 0),
        time(13, 0)
    ),
    "AN": (
        time(14, 0),
        time(17, 0)
    )
}


def get_session_time(session):
    """
    Return the default start and end time for a session.
    """

    normalized_session = session.strip().upper()

    if normalized_session not in SESSION_TIMES:
        raise ValueError(
            f"Invalid session: {session}. "
            "Allowed sessions are FN and AN."
        )

    return SESSION_TIMES[normalized_session]


def get_available_dates(start_date, end_date, excluded_dates=None):
    """
    Return all available dates between start_date and end_date.

    Excluded dates are not returned.
    """

    if start_date > end_date:
        raise ValueError(
            "Examination start date cannot be after end date."
        )

    excluded_dates = excluded_dates or set()

    available_dates = []

    current_date = start_date

    while current_date <= end_date:
        if current_date not in excluded_dates:
            available_dates.append(current_date)

        current_date += timedelta(days=1)

    return available_dates


def validate_timetable_entry(
    examination_id,
    subject_id,
    exam_date,
    session,
    start_time,
    end_time
):
    """
    Validate a timetable entry against basic timetable rules.
    """

    examination = db.session.get(
        Examination,
        examination_id
    )

    if not examination:
        raise ValueError(
            "Examination not found."
        )

    subject = db.session.get(
        Subject,
        subject_id
    )

    if not subject:
        raise ValueError(
            "Subject not found."
        )

    normalized_session = session.strip().upper()

    if normalized_session not in SESSION_TIMES:
        raise ValueError(
            "Invalid session. Allowed sessions are FN and AN."
        )

    if start_time >= end_time:
        raise ValueError(
            "Start time must be before end time."
        )
    if exam_date < examination.start_date:
        raise ValueError(
            "Timetable date is before the examination start date."
        )

    if exam_date > examination.end_date:
        raise ValueError(
            "Timetable date is after the examination end date."
        )

    return True


def generate_timetable(
    examination_id,
    subject_ids,
    start_date,
    end_date,
    sessions,
    excluded_dates=None,
    clear_existing=False
):
    """
    Generate timetable entries for an examination.

    This function intentionally uses deterministic scheduling.
    It does not use AI or random scheduling.
    """

    examination = db.session.get(
        Examination,
        examination_id
    )

    if not examination:
        raise ValueError(
            "Examination not found."
        )

    if not subject_ids:
        raise ValueError(
            "At least one subject is required."
        )

    if start_date < examination.start_date:
        raise ValueError(
            "Generation start date cannot be before "
            "the examination start date."
        )

    if end_date > examination.end_date:
        raise ValueError(
            "Generation end date cannot be after "
            "the examination end date."
        )
    if not sessions:
        raise ValueError(
            "At least one session is required."
        )

    normalized_sessions = [
        session.strip().upper()
        for session in sessions
    ]

    for session in normalized_sessions:
        if session not in SESSION_TIMES:
            raise ValueError(
                f"Invalid session: {session}. "
                "Allowed sessions are FN and AN."
            )

    available_dates = get_available_dates(
        start_date,
        end_date,
        excluded_dates
    )

    if not available_dates:
        raise ValueError(
            "No available examination dates found."
        )

    subjects = (
        Subject.query
        .filter(Subject.id.in_(subject_ids))
        .order_by(Subject.id)
        .all()
    )

    if len(subjects) != len(set(subject_ids)):
        raise ValueError(
            "One or more selected subjects were not found."
        )

    if clear_existing:
        Timetable.query.filter_by(
            examination_id=examination_id
        ).delete(
            synchronize_session=False
        )

    timetable_entries = []

    slot_index = 0

    for subject in subjects:

        date_index = (
            slot_index // len(normalized_sessions)
        ) % len(available_dates)

        session_index = (
            slot_index % len(normalized_sessions)
        )

        exam_date = available_dates[date_index]
        session = normalized_sessions[session_index]

        start_time, end_time = get_session_time(
            session
        )

        duration_minutes = int(
            (
                datetime.combine(
                    date.today(),
                    end_time
                )
                -
                datetime.combine(
                    date.today(),
                    start_time
                )
            ).total_seconds() / 60
        )

        existing_entry = Timetable.query.filter_by(
            examination_id=examination_id,
            subject_id=subject.id
        ).first()

        if existing_entry:
            slot_index += 1
            continue

        entry = Timetable(
            examination_id=examination_id,
            subject_id=subject.id,
            exam_date=exam_date,
            session=session,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            status="GENERATED"
        )

        db.session.add(entry)
        timetable_entries.append(entry)

        slot_index += 1

    db.session.commit()

    return timetable_entries


def get_timetable_for_examination(examination_id):
    """
    Return all timetable entries for an examination.
    """

    return (
        Timetable.query
        .filter_by(
            examination_id=examination_id
        )
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
            Timetable.subject_id
        )
        .all()
    )


def update_timetable_entry(
    timetable_id,
    exam_date,
    session,
    start_time=None,
    end_time=None
):
    """
    Update an existing timetable entry.
    """

    entry = db.session.get(
        Timetable,
        timetable_id
    )

    if not entry:
        raise ValueError(
            "Timetable entry not found."
        )

    normalized_session = session.strip().upper()

    if normalized_session not in SESSION_TIMES:
        raise ValueError(
            "Invalid session. Allowed sessions are FN and AN."
        )

    if start_time is None or end_time is None:
        start_time, end_time = get_session_time(
            normalized_session
        )

    if start_time >= end_time:
        raise ValueError(
            "Start time must be before end time."
        )

    entry.exam_date = exam_date
    entry.session = normalized_session
    entry.start_time = start_time
    entry.end_time = end_time

    entry.duration_minutes = int(
        (
            datetime.combine(
                date.today(),
                end_time
            )
            -
            datetime.combine(
                date.today(),
                start_time
            )
        ).total_seconds() / 60
    )

    entry.status = "GENERATED"

    db.session.commit()

    return entry