from flask import Blueprint

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.auth.decorators import roles_required
from app.services.eligibility import get_eligible_students
from app.services.hall_availability import get_hall_readiness
from app.services.allocation import get_available_halls


readiness_bp = Blueprint(
    "readiness",
    __name__
)


@readiness_bp.route(
    "/examination/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def examination_readiness(examination_id):

    examination = Examination.query.get(
        examination_id
    )

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
        }, 404

    timetable_entries = Timetable.query.filter_by(
        examination_id=examination_id
    ).all()

    students = get_eligible_students(
        examination_id
    )

    hall_readiness = get_hall_readiness()

    eligible_count = len(students)
    available_capacity = hall_readiness[
        "total_available_capacity"
    ]

    # ---------------------------------------------------------
    # GLOBAL CAPACITY CHECK
    # ---------------------------------------------------------
    #
    # Does the campus own enough total exam capacity for this
    # examination, ignoring date/time scheduling?
    #

    global_sufficient = (
        available_capacity >= eligible_count
    )

    # ---------------------------------------------------------
    # PER-TIMETABLE CAPACITY CHECK
    # ---------------------------------------------------------
    #
    # For each timetable entry, compute the halls that are
    # usable at that specific date/time (same filters used by
    # the allocation engine). This is what Stage 7 will
    # actually be able to allocate.
    #

    per_timetable = []
    per_timetable_all_sufficient = True
    worst_shortage = 0

    for entry in timetable_entries:

        usable_halls = get_available_halls(entry)

        entry_capacity = sum(
            hall.examination_capacity
            for hall in usable_halls
        )

        entry_sufficient = (
            entry_capacity >= eligible_count
        )

        entry_shortage = max(
            0,
            eligible_count - entry_capacity
        )

        if not entry_sufficient:
            per_timetable_all_sufficient = False

        if entry_shortage > worst_shortage:
            worst_shortage = entry_shortage

        per_timetable.append(
            {
                "timetable_id": entry.id,
                "exam_date": entry.exam_date.isoformat(),
                "session": entry.session,
                "start_time": entry.start_time.strftime("%H:%M"),
                "end_time": entry.end_time.strftime("%H:%M"),
                "required_capacity": eligible_count,
                "available_capacity": entry_capacity,
                "available_hall_count": len(usable_halls),
                "sufficient": entry_sufficient,
                "shortage": entry_shortage
            }
        )

    # Overall: sufficient only if every slot is sufficient.
    # If there are no timetable entries, defer to global.
    if timetable_entries:
        capacity_sufficient = per_timetable_all_sufficient
    else:
        capacity_sufficient = global_sufficient

    return {
        "success": True,
        "examination": {
            "id": examination.id,
            "name": examination.name,
            "course_id": examination.course_id,
            "semester": examination.semester,
            "status": examination.status
        },
        "timetable": {
            "entry_count": len(timetable_entries),
            "entries": [
                {
                    "id": entry.id,
                    "subject_id": entry.subject_id,
                    "exam_date": entry.exam_date.isoformat(),
                    "session": entry.session,
                    "start_time": entry.start_time.strftime("%H:%M"),
                    "end_time": entry.end_time.strftime("%H:%M"),
                    "status": entry.status
                }
                for entry in timetable_entries
            ]
        },
        "student_eligibility": {
            "eligible_student_count": eligible_count
        },
        "hall_readiness": {
            "available_hall_count": hall_readiness[
                "available_hall_count"
            ],
            "total_available_capacity": available_capacity,
            "accessible_hall_count": hall_readiness[
                "accessible_hall_count"
            ],
            "accessible_capacity": hall_readiness[
                "accessible_capacity"
            ]
        },
                "capacity_check": {
            "required_capacity": eligible_count,
            "available_capacity": available_capacity,
            "sufficient": capacity_sufficient,
            "shortage": worst_shortage if timetable_entries else max(
                0,
                eligible_count - available_capacity
            ),
            "global": {
                "required_capacity": eligible_count,
                "available_capacity": available_capacity,
                "sufficient": global_sufficient,
                "shortage": max(
                    0,
                    eligible_count - available_capacity
                )
            },
            "per_timetable": per_timetable
        },
        "ready_for_allocation": (
            bool(timetable_entries)
            and eligible_count > 0
            and capacity_sufficient
        )
    }