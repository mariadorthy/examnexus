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

    Scheduling model:

    - Examination = one course + one semester/cohort.
    - Semesters of the SAME course are divided into sets.

    Examples:
        2 semesters:
            Set 1 -> Sem 1
            Set 2 -> Sem 2

        4 semesters:
            Set 1 -> Sem 1, Sem 2
            Set 2 -> Sem 3, Sem 4

        6 semesters:
            Set 1 -> Sem 1, Sem 2, Sem 3
            Set 2 -> Sem 4, Sem 5, Sem 6

        8 semesters:
            Set 1 -> Sem 1, Sem 2, Sem 3, Sem 4
            Set 2 -> Sem 5, Sem 6, Sem 7, Sem 8

    - Set 1 starts on the examination plan start date.
    - Set 2 starts on the next available examination date.
    - Each semester gets one subject per examination day.
    - Subjects continue on the next available examination day.
    - Sundays are automatically skipped.
    - Excluded dates are automatically skipped.
    - Sunday/excluded dates do NOT reset or change the current set.
    - Different courses may use the same calendar dates.
    - Within each set, semesters are distributed across FN/AN.
    - gap_days is optional spacing between available examination days.
      For normal scheduling, use gap_days=0.
    """

    # =========================================================
    # BASIC VALIDATION
    # =========================================================

    if not examination_ids:
        raise ValueError(
            "At least one examination must be selected."
        )

    normalized_sessions = [
        str(session).strip().upper()
        for session in (sessions or [])
        if str(session).strip()
    ]

    normalized_sessions = list(
        dict.fromkeys(normalized_sessions)
    )

    if not normalized_sessions:
        raise ValueError(
            "At least one session must be selected."
        )

    invalid_sessions = [
        session
        for session in normalized_sessions
        if session not in SESSION_TIMES
    ]

    if invalid_sessions:
        raise ValueError(
            f"Invalid session(s): "
            f"{', '.join(invalid_sessions)}"
        )

    try:
        gap_days = int(gap_days)
    except (TypeError, ValueError):
        raise ValueError(
            "Gap days must be a whole number."
        )

    if gap_days < 0:
        raise ValueError(
            "Gap days cannot be negative."
        )

    examination_ids = list(
        dict.fromkeys(examination_ids)
    )

    # =========================================================
    # LOAD EXAMINATIONS
    # =========================================================

    examinations = (
        Examination.query
        .filter(
            Examination.id.in_(examination_ids)
        )
        .order_by(
            Examination.course_id.asc(),
            Examination.semester.asc(),
            Examination.id.asc(),
        )
        .all()
    )

    if not examinations:
        raise ValueError(
            "No valid examinations were found."
        )

    if len(examinations) != len(examination_ids):

        found_ids = {
            examination.id
            for examination in examinations
        }

        missing_ids = [
            examination_id
            for examination_id in examination_ids
            if examination_id not in found_ids
        ]

        raise ValueError(
            f"Examination(s) not found: {missing_ids}"
        )

    # =========================================================
    # ALL SELECTED EXAMS MUST BELONG TO SAME PLAN
    # =========================================================

    reference_exam = examinations[0]

    for examination in examinations[1:]:

        if (
            examination.name
            != reference_exam.name
            or examination.exam_type
            != reference_exam.exam_type
            or examination.start_date
            != reference_exam.start_date
            or examination.end_date
            != reference_exam.end_date
        ):
            raise ValueError(
                "All selected examinations must belong "
                "to the same examination plan."
            )

    # =========================================================
    # EXCLUDED DATES
    # =========================================================

    normalized_excluded_dates = set()

    # 1. Excluded dates supplied from the Timetable form.
    for value in (excluded_dates or []):

        if isinstance(value, datetime):
            normalized_excluded_dates.add(
                value.date()
            )

        elif isinstance(value, date):
            normalized_excluded_dates.add(value)

        else:
            try:
                normalized_excluded_dates.add(
                    date.fromisoformat(str(value))
                )
            except ValueError:
                raise ValueError(
                    f"Invalid excluded date: {value}"
                )
    # 2. Excluded dates saved in Examination Creation.
    # These apply to the entire selected examination plan.
    for examination in examinations:

        for value in (
            examination.excluded_dates or []
        ):

            if isinstance(value, datetime):
                normalized_excluded_dates.add(
                    value.date()
                )

            elif isinstance(value, date):
                normalized_excluded_dates.add(value)

            else:
                try:
                    normalized_excluded_dates.add(
                       date.fromisoformat(str(value))
                    )
                except ValueError:
                    raise ValueError(
                        f"Invalid examination excluded date: {value}"
                    )

    # =========================================================
    # AVAILABLE DATES
    #
    # IMPORTANT:
    # get_available_dates() already removes Sundays.
    #
    # Example:
    #
    # Friday
    # Saturday
    # Sunday      <- removed
    # Monday
    #
    # The scheduler therefore sees:
    #
    # Friday
    # Saturday
    # Monday
    #
    # Sunday does NOT reset the current set.
    # =========================================================

    available_dates = get_available_dates(
        reference_exam.start_date,
        reference_exam.end_date,
        normalized_excluded_dates,
    )

    if not available_dates:
        raise ValueError(
            "No available examination dates exist "
            "within the selected examination plan."
        )

    # =========================================================
    # LOAD SUBJECTS FOR EACH EXAMINATION
    # =========================================================

    examination_subjects = {}

    for examination in examinations:

        subjects = (
            Subject.query
            .filter(
                Subject.course_id
                == examination.course_id,

                Subject.semester
                == examination.semester,

                Subject.is_active.is_(True),
            )
            .order_by(
                Subject.id.asc()
            )
            .all()
        )

        examination_subjects[
            examination.id
        ] = subjects

    # Only examinations that actually have subjects
    # can participate in timetable generation.

    schedulable_examinations = [
        examination
        for examination in examinations
        if examination_subjects[
            examination.id
        ]
    ]

    if not schedulable_examinations:
        raise ValueError(
            "No active subjects were found for "
            "the selected examinations."
        )

    # =========================================================
    # GROUP EXAMINATIONS BY COURSE
    # =========================================================

    examinations_by_course = {}

    for examination in schedulable_examinations:

        examinations_by_course.setdefault(
            examination.course_id,
            []
        ).append(
            examination
        )

    # =========================================================
    # SORT SEMESTERS WITHIN EACH COURSE
    # =========================================================

    for course_id in examinations_by_course:

        examinations_by_course[
            course_id
        ].sort(
            key=lambda examination: (
                examination.semester,
                examination.id
            )
        )

    # =========================================================
    # BUILD SEMESTER SETS
    #
    # 2 semesters:
    #   Set 1 -> Sem 1
    #   Set 2 -> Sem 2
    #
    # 4 semesters:
    #   Set 1 -> Sem 1,2
    #   Set 2 -> Sem 3,4
    #
    # 6 semesters:
    #   Set 1 -> Sem 1,2,3
    #   Set 2 -> Sem 4,5,6
    #
    # 8 semesters:
    #   Set 1 -> Sem 1,2,3,4
    #   Set 2 -> Sem 5,6,7,8
    #
    # The split is balanced and sequential.
    # =========================================================

    course_sets = {}

    for course_id, course_examinations in (
        examinations_by_course.items()
    ):

        total_semesters = len(
            course_examinations
        )

        split_point = (
            total_semesters + 1
        ) // 2

        first_set = course_examinations[
            :split_point
        ]

        second_set = course_examinations[
            split_point:
        ]

        sets = []

        if first_set:
            sets.append(first_set)

        if second_set:
            sets.append(second_set)

        course_sets[course_id] = sets

    # =========================================================
    # ASSIGN START DATE TO EACH SET
    #
    # Set 1 starts on the first available date.
    #
    # Set 2 starts on the next available date.
    #
    # Since Sundays are already removed from available_dates,
    # a Sunday between these dates has no effect.
    #
    # Example:
    #
    # available_dates:
    #   Friday
    #   Saturday
    #   Monday
    #
    # Set 1 -> Friday
    # Set 2 -> Saturday
    #
    # If a later subject reaches Sunday, it simply continues
    # on Monday.
    # =========================================================

    scheduled_set_dates = {}

    for course_id, sets in course_sets.items():

        scheduled_set_dates[
            course_id
        ] = []

        date_index = 0

        for semester_set in sets:

            if date_index >= len(
                available_dates
            ):
                raise ValueError(
                    "Not enough available examination "
                    "dates to create semester sets."
                )

            set_start_date = available_dates[
                date_index
            ]

            scheduled_set_dates[
                course_id
            ].append(
                (
                    semester_set,
                    set_start_date
                )
            )
    # Each semester set starts on the next
    # available examination day.
    #
    # The gap applies to subjects INSIDE
    # each set, not between semester sets.
    #
    # Example with gap_days=1:
    #
    # Set 1 -> Oct 1
    # Set 2 -> Oct 2
    #
    # Then subjects inside each set are spaced:
    #
    # Set 1 -> Oct 1, Oct 3, Oct 6, ...
    # Set 2 -> Oct 2, Oct 4, Oct 7, ...
    #
    # Sundays are already removed from
    # available_dates.
            date_index += 1

    # =========================================================
    # CLEAR EXISTING ENTRIES
    # =========================================================

    if clear_existing:

        Timetable.query.filter(
            Timetable.examination_id.in_(
                examination_ids
            )
        ).delete(
            synchronize_session=False
        )

        db.session.flush()

    created_entries = []
    skipped_entries = []

    # =========================================================
    # GENERATE SUBJECT TIMETABLE
    # =========================================================

    for course_id, semester_sets in (
        scheduled_set_dates.items()
    ):

        for semester_set, set_start_date in (
            semester_sets
        ):

            # -------------------------------------------------
            # DISTRIBUTE SEMESTERS ACROSS FN / AN
            #
            # 4 semesters:
            #
            # Sem 1 -> FN
            # Sem 2 -> FN
            # Sem 3 -> AN
            # Sem 4 -> AN
            #
            # 3 semesters:
            #
            # Sem 1 -> FN
            # Sem 2 -> FN
            # Sem 3 -> AN
            #
            # 2 semesters:
            #
            # Sem 1 -> FN
            # Sem 2 -> AN
            # -------------------------------------------------

            total_in_set = len(
                semester_set
            )

            fn_count = (
                total_in_set + 1
            ) // 2

            for index, examination in enumerate(
                semester_set
            ):

                if len(normalized_sessions) == 1:

                    session = (
                        normalized_sessions[0]
                    )

                else:

                    if index < fn_count:

                        session = (
                            normalized_sessions[0]
                        )

                    else:

                        session = (
                            normalized_sessions[1]
                        )

                # -------------------------------------------------
                # SESSION TIME
                # -------------------------------------------------

                start_time, end_time = (
                    get_examination_session_times(
                        examination,
                        session
                    )
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
                    ).total_seconds()
                    / 60
                )

                # -------------------------------------------------
                # FIND START INDEX OF THIS SET
                # -------------------------------------------------

                set_start_index = (
                    available_dates.index(
                        set_start_date
                    )
                )

                # -------------------------------------------------
                # SCHEDULE SUBJECTS
                #
                # Subject 1:
                #   set start date
                #
                # Subject 2:
                #   next available examination date
                #
                # Subject 3:
                #   next available examination date
                #
                # ...
                #
                # IMPORTANT:
                #
                # Sunday is NOT handled here.
                #
                # It was already removed from available_dates.
                #
                # Therefore:
                #
                # Saturday -> Sunday -> Monday
                #
                # becomes:
                #
                # Saturday -> Monday
                #
                # The same set continues normally.
                # -------------------------------------------------

                for subject_index, subject in enumerate(
                    examination_subjects[
                        examination.id
                    ]
                ):

                    subject_date_index = (
                        set_start_index
                        + (
                            subject_index
                            * (1 + gap_days)
                        )
                    )

                    if (
                        subject_date_index
                        >= len(available_dates)
                    ):
                        raise ValueError(
                            "Not enough available "
                            "examination dates to complete "
                            f"{examination.name} - "
                            f"Semester "
                            f"{examination.semester}."
                        )

                    exam_date = (
                        available_dates[
                            subject_date_index
                        ]
                    )

                    # -------------------------------------------------
                    # CHECK EXISTING SUBJECT ENTRY
                    # -------------------------------------------------

                    existing_entry = (
                        Timetable.query
                        .filter_by(
                            examination_id=(
                                examination.id
                            ),
                            subject_id=subject.id
                        )
                        .first()
                    )

                    if existing_entry:

                        skipped_entries.append({
                            "examination_id":
                                examination.id,

                            "subject_id":
                                subject.id,

                            "exam_date":
                                existing_entry
                                .exam_date
                                .isoformat(),

                            "session":
                                existing_entry.session
                        })

                        continue

                    # -------------------------------------------------
                    # SAFETY CHECK
                    #
                    # One semester/cohort cannot have two
                    # subjects on the same examination day.
                    # -------------------------------------------------

                    same_day_entry = (
                        Timetable.query
                        .filter_by(
                            examination_id=(
                                examination.id
                            ),
                            exam_date=exam_date
                        )
                        .first()
                    )

                    if same_day_entry:

                        raise ValueError(
                            f"Scheduling conflict detected for "
                            f"{examination.name} - Semester "
                            f"{examination.semester}: "
                            f"multiple subjects cannot be "
                            f"scheduled on "
                            f"{exam_date.isoformat()}."
                        )

                    # -------------------------------------------------
                    # CREATE TIMETABLE ENTRY
                    # -------------------------------------------------

                    entry = Timetable(
                        examination_id=(
                            examination.id
                        ),
                        subject_id=subject.id,
                        exam_date=exam_date,
                        session=session,
                        start_time=start_time,
                        end_time=end_time,
                        duration_minutes=(
                            duration_minutes
                        ),
                        status="GENERATED"
                    )

                    db.session.add(entry)

                    created_entries.append(
                        entry
                    )

    # =========================================================
    # COMMIT
    # =========================================================

    db.session.commit()

    # =========================================================
    # RETURN RESULT
    # =========================================================

    return {
        "created_count": len(
            created_entries
        ),

        "skipped_count": len(
            skipped_entries
        ),

        "created": [
            {
                "id": entry.id,
                "examination_id":
                    entry.examination_id,
                "subject_id":
                    entry.subject_id,
                "exam_date":
                    entry.exam_date.isoformat(),
                "session":
                    entry.session,
                "start_time":
                    entry.start_time.strftime(
                        "%H:%M"
                    ),
                "end_time":
                    entry.end_time.strftime(
                        "%H:%M"
                    ),
                "duration_minutes":
                    entry.duration_minutes,
                "status":
                    entry.status,
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