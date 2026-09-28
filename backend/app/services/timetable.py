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

def get_examination_session_times(examination, session):
    normalized_session = session.strip().upper()

    session_config = examination.session_config or []

    for config in session_config:
        if config.get("session", "").strip().upper() == normalized_session:
            try:
                start_time = time.fromisoformat(config["start_time"])
                end_time = time.fromisoformat(config["end_time"])
            except (KeyError, ValueError):
                raise ValueError(
                    f"Invalid time configuration for session {normalized_session}."
                )

            if start_time >= end_time:
                raise ValueError(
                    f"Invalid time range for session {normalized_session}."
                )

            return start_time, end_time

    if normalized_session in SESSION_TIMES:
        return SESSION_TIMES[normalized_session]

    raise ValueError(
        f"Invalid session: {session}. Allowed sessions are FN and AN."
    )

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

    Sundays and explicitly excluded dates are not returned.
    """

    if start_date > end_date:
        raise ValueError(
            "Examination start date cannot be after end date."
        )

    excluded_dates = excluded_dates or set()

    available_dates = []

    current_date = start_date

    while current_date <= end_date:

        # Sunday is always unavailable for examinations.
        is_sunday = current_date.weekday() == 6

        if (
            current_date not in excluded_dates
            and not is_sunday
        ):
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
    .filter(
        Subject.id.in_(subject_ids),
        Subject.is_active.is_(True)
    )
    .order_by(Subject.id)
    .all()
)

    if len(subjects) != len(set(subject_ids)):
        raise ValueError(
        "One or more selected subjects were not found or are inactive."
    )

    invalid_subjects = [
    subject.subject_code
    for subject in subjects
    if (
        subject.course_id != examination.course_id
        or subject.semester != examination.semester
    )
]

    if invalid_subjects:
        raise ValueError( 
        "Selected subjects do not belong to the examination course and semester: "
        + ", ".join(invalid_subjects)
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

        start_time, end_time = get_examination_session_times(
    examination,
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

def generate_bulk_timetable(
    examination_ids,
    sessions,
    gap_days=0,
    excluded_dates=None,
    clear_existing=False
):
    """
    Generate timetables for multiple examinations belonging
    to the same examination plan.

    Each examination automatically uses its active subjects
    based on its course and semester.

    gap_days:
        0 = no gap
        1 = one calendar day between exam days
        2 = two calendar days between exam days
    """

    if not examination_ids:
        raise ValueError(
            "At least one examination is required."
        )

    if not sessions:
        raise ValueError(
            "At least one session is required."
        )

    try:
        gap_days = int(gap_days)
    except (TypeError, ValueError):
        raise ValueError(
            "Gap between exams must be a valid number."
        )

    if gap_days < 0:
        raise ValueError(
            "Gap between exams cannot be negative."
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

    unique_examination_ids = list(
        dict.fromkeys(examination_ids)
    )

    examinations = (
        Examination.query
        .filter(
            Examination.id.in_(unique_examination_ids)
        )
        .order_by(
            Examination.course_id,
            Examination.semester
        )
        .all()
    )

    if len(examinations) != len(unique_examination_ids):
        raise ValueError(
            "One or more selected examinations were not found."
        )

    reference = examinations[0]

    # All examinations must belong to the same
    # Examination Plan.
    for examination in examinations[1:]:
        if (
            examination.name != reference.name
            or examination.exam_type != reference.exam_type
            or examination.start_date != reference.start_date
            or examination.end_date != reference.end_date
        ):
            raise ValueError(
                "Selected examinations must belong "
                "to the same examination plan."
            )

    excluded_dates = excluded_dates or set()

    available_dates = get_available_dates(
        reference.start_date,
        reference.end_date,
        excluded_dates
    )

    if not available_dates:
        raise ValueError(
            "No available examination dates found."
        )

    created_entries = []
    skipped_entries = []

    try:
        if clear_existing:
            Timetable.query.filter(
                Timetable.examination_id.in_(
                    unique_examination_ids
                )
            ).delete(
                synchronize_session=False
            )

        for examination in examinations:

            subjects = (
                Subject.query
                .filter(
                    Subject.course_id == examination.course_id,
                    Subject.semester == examination.semester,
                    Subject.is_active.is_(True)
                )
                .order_by(Subject.id)
                .all()
            )

            if not subjects:
                raise ValueError(
                    f"No active subjects found for "
                    f"{examination.name} - "
                    f"Course {examination.course_id} - "
                    f"Semester {examination.semester}."
                )

            # Make sure every selected session exists
            # in this examination's configuration.
            for session in normalized_sessions:
                get_examination_session_times(
                    examination,
                    session
                )

            session_count = len(normalized_sessions)

            subject_index = 0
            date_pointer = 0

            while subject_index < len(subjects):

                if date_pointer >= len(available_dates):
                    raise ValueError(
                        f"Not enough available dates to schedule "
                        f"all subjects for "
                        f"{examination.name} - "
                        f"Semester {examination.semester}."
                    )

                exam_date = available_dates[date_pointer]

                # Put subjects into the available sessions
                # on this examination day.
                for session_index in range(session_count):

                    if subject_index >= len(subjects):
                        break

                    subject = subjects[subject_index]

                    session = normalized_sessions[
                        session_index
                    ]

                    start_time, end_time = (
                        get_examination_session_times(
                            examination,
                            session
                        )
                    )

                    existing_entry = Timetable.query.filter_by(
                        examination_id=examination.id,
                        subject_id=subject.id
                    ).first()

                    if existing_entry:
                        skipped_entries.append(
                            existing_entry
                        )
                        subject_index += 1
                        continue

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

                    entry = Timetable(
                        examination_id=examination.id,
                        subject_id=subject.id,
                        exam_date=exam_date,
                        session=session,
                        start_time=start_time,
                        end_time=end_time,
                        duration_minutes=duration_minutes,
                        status="GENERATED"
                    )

                    db.session.add(entry)
                    created_entries.append(entry)

                    subject_index += 1

                # Move to the next exam day.
                #
                # gap_days = 0:
                # 1 Oct -> 2 Oct
                #
                # gap_days = 1:
                # 1 Oct -> 3 Oct
                #
                # gap_days = 2:
                # 1 Oct -> 4 Oct
                next_date = (
                    exam_date
                    + timedelta(days=gap_days + 1)
                )

                while (
                    date_pointer < len(available_dates)
                    and available_dates[date_pointer]
                    < next_date
                ):
                    date_pointer += 1

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "created": created_entries,
        "skipped": skipped_entries
    }

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

    examination = db.session.get(
        Examination,
        entry.examination_id
    )

    if not examination:
        raise ValueError(
            "Examination not found."
        )

    if exam_date < examination.start_date:
        raise ValueError(
            "Timetable date is before the examination start date."
        )

    if exam_date > examination.end_date:
        raise ValueError(
            "Timetable date is after the examination end date."
        )

    excluded_dates = {
        date.fromisoformat(value)
        for value in (examination.excluded_dates or [])
    }

    if exam_date in excluded_dates:
        raise ValueError(
            "Timetable date is an excluded examination date."
        )

    normalized_session = session.strip().upper()

    if normalized_session not in SESSION_TIMES:
        raise ValueError(
            "Invalid session. Allowed sessions are FN and AN."
        )

    if start_time is None or end_time is None:
        start_time, end_time = get_examination_session_times(
            examination,
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