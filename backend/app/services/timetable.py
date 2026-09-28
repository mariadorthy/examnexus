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
    clear_existing=False,
):
    """
    Generate timetable entries for multiple examinations.

    Rules:
    - Each examination/cohort gets only ONE subject per exam date.
    - Multiple different examinations can run on the same date.
    - Selected sessions are distributed across examinations.
    - Sundays and excluded dates are skipped.
    - Gap days are respected between exam dates for each examination.
    """

    if not examination_ids:
        raise ValueError("At least one examination must be selected.")

    normalized_sessions = [
        str(session).strip().upper()
        for session in (sessions or [])
        if str(session).strip()
    ]

    if not normalized_sessions:
        raise ValueError("At least one session must be selected.")

    invalid_sessions = [
        session
        for session in normalized_sessions
        if session not in SESSION_TIMES
    ]

    if invalid_sessions:
        raise ValueError(
            f"Invalid session(s): {', '.join(invalid_sessions)}"
        )

    if gap_days < 0:
        raise ValueError("Gap days cannot be negative.")

    # Remove duplicate IDs while preserving order.
    examination_ids = list(dict.fromkeys(examination_ids))

    examinations = (
        Examination.query
        .filter(Examination.id.in_(examination_ids))
        .order_by(
            Examination.course_id.asc(),
            Examination.semester.asc(),
            Examination.id.asc(),
        )
        .all()
    )

    if not examinations:
        raise ValueError("No valid examinations were found.")

    if len(examinations) != len(examination_ids):
        found_ids = {exam.id for exam in examinations}

        missing_ids = [
            exam_id
            for exam_id in examination_ids
            if exam_id not in found_ids
        ]

        raise ValueError(
            f"Examination(s) not found: {missing_ids}"
        )

    # ---------------------------------------------------------
    # Make sure all selected examinations belong to one plan.
    # ---------------------------------------------------------
    reference_exam = examinations[0]

    for examination in examinations[1:]:
        if (
            examination.name != reference_exam.name
            or examination.exam_type != reference_exam.exam_type
            or examination.start_date != reference_exam.start_date
            or examination.end_date != reference_exam.end_date
        ):
            raise ValueError(
                "All selected examinations must belong to the same "
                "examination plan."
            )

    # ---------------------------------------------------------
    # Build excluded dates.
    # ---------------------------------------------------------
    excluded_dates = excluded_dates or []

    normalized_excluded_dates = set()

    for value in excluded_dates:
        if isinstance(value, date):
            normalized_excluded_dates.add(value)
        else:
            normalized_excluded_dates.add(
                date.fromisoformat(str(value))
            )

    # ---------------------------------------------------------
    # Get available dates.
    # Sundays are already removed by get_available_dates().
    # ---------------------------------------------------------
    available_dates = get_available_dates(
        reference_exam.start_date,
        reference_exam.end_date,
        normalized_excluded_dates,
    )

    if not available_dates:
        raise ValueError(
            "No available examination dates exist within the "
            "selected examination plan."
        )

    # ---------------------------------------------------------
    # Clear existing entries if requested.
    # ---------------------------------------------------------
    if clear_existing:
        Timetable.query.filter(
            Timetable.examination_id.in_(examination_ids)
        ).delete(
            synchronize_session=False
        )

        db.session.flush()

    created_entries = []
    skipped_entries = []

    # ---------------------------------------------------------
    # Generate subjects for every examination.
    #
    # Each examination represents a course + semester cohort.
    # A cohort can have only ONE exam on a particular date.
    # ---------------------------------------------------------
    examination_subjects = {}

    for examination in examinations:
        subjects = (
            Subject.query
            .filter(
                Subject.course_id == examination.course_id,
                Subject.semester == examination.semester,
                Subject.is_active.is_(True),
            )
            .order_by(Subject.id.asc())
            .all()
        )

        if not subjects:
            continue

        examination_subjects[examination.id] = subjects

    if not examination_subjects:
        raise ValueError(
            "No active subjects were found for the selected examinations."
        )

    # ---------------------------------------------------------
    # Track how many subjects have already been scheduled
    # for every examination.
    # ---------------------------------------------------------
    subject_indexes = {
        examination_id: 0
        for examination_id in examination_subjects
    }

    # ---------------------------------------------------------
    # Track the next available date for each examination.
    #
    # This guarantees that the same cohort does not receive
    # two examinations on the same date.
    # ---------------------------------------------------------
    next_date_indexes = {
        examination_id: 0
        for examination_id in examination_subjects
    }

    # ---------------------------------------------------------
    # Schedule date by date.
    #
    # Example with FN + AN:
    #
    # Oct 1:
    #   Semester 1 -> FN -> Subject 1
    #   Semester 2 -> AN -> Subject 1
    #
    # Oct 3:
    #   Semester 1 -> FN -> Subject 2
    #   Semester 2 -> AN -> Subject 2
    #
    # No examination receives both FN and AN on the same date.
    # ---------------------------------------------------------
    while True:
        progress_made = False

        for examination_index, examination in enumerate(examinations):

            if examination.id not in examination_subjects:
                continue

            subjects = examination_subjects[examination.id]

            subject_index = subject_indexes[examination.id]

            if subject_index >= len(subjects):
                continue

            date_index = next_date_indexes[examination.id]

            if date_index >= len(available_dates):
                raise ValueError(
                    f"Not enough available examination dates for "
                    f"{examination.name} - Semester "
                    f"{examination.semester}."
                )

            exam_date = available_dates[date_index]

            subject = subjects[subject_index]

            # -------------------------------------------------
            # Assign ONE session to this examination.
            #
            # Sessions rotate across examinations.
            # -------------------------------------------------
            session = normalized_sessions[
                examination_index % len(normalized_sessions)
            ]

            start_time, end_time = get_examination_session_times(
                examination,
                session,
            )

            # -------------------------------------------------
            # Check whether this exact timetable entry already
            # exists.
            # -------------------------------------------------
            existing_entry = Timetable.query.filter_by(
                examination_id=examination.id,
                subject_id=subject.id,
            ).first()

            if existing_entry and not clear_existing:

                skipped_entries.append({
                    "examination_id": examination.id,
                    "subject_id": subject.id,
                    "exam_date": existing_entry.exam_date.isoformat(),
                    "session": existing_entry.session,
                })

                subject_indexes[examination.id] += 1

                # Existing subject already occupies a timetable
                # date, so move this examination forward.
                current_date_index = date_index

                next_date = (
                    available_dates[current_date_index]
                    + timedelta(days=gap_days + 1)
                )

                next_index = current_date_index + 1

                while (
                    next_index < len(available_dates)
                    and available_dates[next_index] < next_date
                ):
                    next_index += 1

                next_date_indexes[examination.id] = next_index

                progress_made = True
                continue

            # -------------------------------------------------
            # Prevent another subject of the SAME examination
            # from being placed on the same date.
            # -------------------------------------------------
            same_day_entry = Timetable.query.filter_by(
                examination_id=examination.id,
                exam_date=exam_date,
            ).first()

            if same_day_entry:
                raise ValueError(
                    f"Scheduling conflict detected for "
                    f"{examination.name}: "
                    f"multiple subjects cannot be scheduled "
                    f"on {exam_date.isoformat()}."
                )

            entry = Timetable(
                examination_id=examination.id,
                subject_id=subject.id,
                exam_date=exam_date,
                session=session,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=examination.duration_minutes,
                status="GENERATED",
            )

            db.session.add(entry)

            created_entries.append(entry)

            subject_indexes[examination.id] += 1

            # -------------------------------------------------
            # Move this examination to the next valid date.
            # -------------------------------------------------
            next_date = (
                exam_date
                + timedelta(days=gap_days + 1)
            )

            next_index = date_index + 1

            while (
                next_index < len(available_dates)
                and available_dates[next_index] < next_date
            ):
                next_index += 1

            next_date_indexes[examination.id] = next_index

            progress_made = True

        # -----------------------------------------------------
        # Stop when every examination has all subjects scheduled.
        # -----------------------------------------------------
        all_completed = all(
            subject_indexes[examination_id]
            >= len(examination_subjects[examination_id])
            for examination_id in examination_subjects
        )

        if all_completed:
            break

        if not progress_made:
            raise ValueError(
                "Unable to generate timetable with the available "
                "dates, sessions, and gap configuration."
            )

    db.session.commit()

    return {
        "created_count": len(created_entries),
        "skipped_count": len(skipped_entries),
        "created": [
            {
                "id": entry.id,
                "examination_id": entry.examination_id,
                "subject_id": entry.subject_id,
                "exam_date": entry.exam_date.isoformat(),
                "session": entry.session,
                "start_time": entry.start_time.strftime("%H:%M"),
                "end_time": entry.end_time.strftime("%H:%M"),
                "duration_minutes": entry.duration_minutes,
                "status": entry.status,
            }
            for entry in created_entries
        ],
        "skipped": skipped_entries,
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