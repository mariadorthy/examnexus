"""
Phase 9 — Natural-language database query tests.

Feature 19.

The layer must:
- interpret supported read-only questions
- reject non-admin users
- reject empty / invalid input
- reject unsupported questions explicitly
- never guess
- reject mutation-style input
- reject SQL-like input
- never modify protected data
- be deterministic
"""
import pytest
from app.services.natural_language_query_parser import parse_query

# ============================================================
# Parser — supported intents
# ============================================================

def test_understands_list_examinations():
    r = parse_query("Show all examinations.")
    assert r["success"] is True
    assert r["intent"] == "LIST_EXAMINATIONS"


def test_understands_examination_status():
    r = parse_query("What is the status of the examination?")
    assert r["success"] is True
    assert r["intent"] == "EXAMINATION_STATUS"

def test_examination_status_extracts_name():
    result = parse_query(
        "What is the status of Database Management Examination?"
    )

    assert result["success"] is True
    assert result["intent"] == "EXAMINATION_STATUS"
    assert result["params"]["name"] == "Database Management Examination"

def test_hall_capacity():
    result = parse_query(
        "What is the capacity of Hall H204?"
    )

    assert result["success"] is True
    assert result["intent"] == "HALL_CAPACITY"
    assert result["params"]["hall"] == "H204"

def test_timetable_extracts_course():
    result = parse_query(
        "Show the examination timetable for Computer Science."
    )

    assert result["success"] is True
    assert result["intent"] == "EXAMINATION_TIMETABLE"
    assert result["params"]["course"] == "Computer Science"

def test_understands_eligible_student_count():
    r = parse_query("How many eligible students are there?")
    assert r["success"] is True
    assert r["intent"] == "ELIGIBLE_STUDENT_COUNT"


def test_understands_registered_student_count():
    r = parse_query("How many registered students?")
    assert r["success"] is True
    assert r["intent"] == "REGISTERED_STUDENT_COUNT"


def test_understands_available_halls():
    r = parse_query("Which halls are available?")
    assert r["success"] is True
    assert r["intent"] == "HALLS_BY_STATUS"
    assert r["params"]["status"] == "available"


def test_understands_maintenance_halls():
    r = parse_query("Which halls are under maintenance?")
    assert r["success"] is True
    assert r["intent"] == "HALLS_BY_STATUS"
    assert r["params"]["status"] == "maintenance"


def test_understands_unavailable_halls():
    r = parse_query("Show unavailable halls.")
    assert r["success"] is True
    assert r["intent"] == "HALLS_BY_STATUS"
    assert r["params"]["status"] == "unavailable"


def test_understands_students_in_hall():
    r = parse_query("How many students are allocated to Hall H204?")
    assert r["success"] is True
    assert r["intent"] == "STUDENTS_IN_HALL"
    assert r["params"]["hall"] == "H204"


def test_understands_hall_allocation_summary():
    r = parse_query("How many students are assigned to each hall?")
    assert r["success"] is True
    assert r["intent"] == "HALL_ALLOCATION_SUMMARY"


def test_understands_unallocated_students():
    r = parse_query(
        "Show unallocated students for examination 5."
    )

    assert r["success"] is True
    assert r["intent"] == "UNALLOCATED_STUDENT_COUNT"
    assert r["params"]["examination_id"] == 5

def test_unallocated_students_requires_examination():
    r = parse_query("Show unallocated students.")

    assert r["success"] is False
    assert r["intent"] is None

def test_understands_timetable():
    r = parse_query("Show the examination timetable for Computer Science.")
    assert r["success"] is True
    assert r["intent"] == "EXAMINATION_TIMETABLE"


def test_multiple_phrasings_map_to_same_intent():
    a = parse_query("Show all examinations.")
    b = parse_query("List examinations.")
    c = parse_query("Display upcoming examinations.")
    assert a["intent"] == b["intent"] == c["intent"] == "LIST_EXAMINATIONS"


# ============================================================
# Rejections
# ============================================================

def test_empty_question_rejected():
    r = parse_query("")
    assert r["success"] is False
    assert r["rejected_reason"] == "EMPTY_INPUT"


def test_whitespace_question_rejected():
    r = parse_query("    ")
    assert r["success"] is False


def test_non_string_question_rejected():
    r = parse_query(None)
    assert r["success"] is False
    assert r["rejected_reason"] == "INVALID_INPUT"


def test_numeric_question_rejected():
    r = parse_query(12345)
    assert r["success"] is False


def test_unsupported_question_rejected():
    r = parse_query("Which students are likely to fail?")
    assert r["success"] is False
    assert r["rejected_reason"] == "UNSUPPORTED_QUERY"


def test_unknown_question_is_not_guessed():
    r = parse_query("Arrange students by favourite food.")
    assert r["success"] is False
    assert r["intent"] is None


def test_delete_query_rejected():
    r = parse_query("Delete all allocations for tomorrow.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_update_query_rejected():
    r = parse_query("Update the hall capacity for H101.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_insert_query_rejected():
    r = parse_query("Insert a new student record.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_drop_query_rejected():
    r = parse_query("Drop the students table.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_approve_query_rejected():
    r = parse_query("Approve the examination.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_publish_query_rejected():
    r = parse_query("Publish the examination results.")
    assert r["success"] is False
    assert r["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_sql_injection_rejected():
    r = parse_query("Show students; drop table students;")
    assert r["success"] is False
    assert r["rejected_reason"] in ("UNSAFE_INPUT", "READ_ONLY_VIOLATION")


def test_union_select_rejected():
    r = parse_query("Show examinations union select password from students")
    assert r["success"] is False


@pytest.mark.parametrize(
    "question",
    [
        "INSERT a new student",
        "UPDATE student details",
        "DELETE examination",
        "DROP the hall table",
    ],
)
def test_mutation_queries_are_rejected(question):
    result = parse_query(question)

    assert result["success"] is False

# ============================================================
# Determinism
# ============================================================

def test_parser_is_deterministic():
    text = "How many students are allocated to Hall H204?"
    assert parse_query(text) == parse_query(text)


# ============================================================
# API tests
# ============================================================

def test_nl_query_requires_auth(client):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": "Show all examinations."},
    )
    assert response.status_code in (401, 403)


def test_nl_query_rejects_invalid_body(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": 12345},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


def test_nl_query_rejects_empty_question(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": ""},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


def test_nl_query_rejects_mutation(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": "Delete all allocations."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert response.get_json()["rejected_reason"] == "READ_ONLY_VIOLATION"


def test_nl_query_rejects_unsupported(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": "Which students are likely to fail?"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


def test_nl_query_accepts_supported(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": "Show all examinations."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["intent"] == "LIST_EXAMINATIONS"
    assert "data" in data


def test_nl_query_halls_by_status(client, admin_token):
    response = client.post(
        "/api/nl-queries/ask",
        json={"question": "Which halls are under maintenance?"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["intent"] == "HALLS_BY_STATUS"
    assert data["data"]["status_filter"] == "maintenance"


# ============================================================
# Safety: no mutation occurred
# ============================================================

def test_no_mutation_occurs_from_read_only_query(app, client, admin_token):
    from app.models.hall import Hall
    from app.models.student import Student
    from app.models.hall_allocation import HallAllocation
    from app.models.seat_allocation import SeatAllocation

    with app.app_context():
        before = {
            "halls": Hall.query.count(),
            "students": Student.query.count(),
            "hall_alloc": HallAllocation.query.count(),
            "seat_alloc": SeatAllocation.query.count(),
        }

    client.post(
        "/api/nl-queries/ask",
        json={"question": "Show all available halls."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    with app.app_context():
        after = {
            "halls": Hall.query.count(),
            "students": Student.query.count(),
            "hall_alloc": HallAllocation.query.count(),
            "seat_alloc": SeatAllocation.query.count(),
        }

    assert before == after

# ============================================================
# Feature 19 — executor-level tests
#
# The existing suite exercises the parser (40 tests). These
# tests exercise execute_query() directly, which is the only
# place natural-language intents touch the database.
# ============================================================

from app.services.natural_language_query import execute_query


def test_execute_query_hall_capacity_returns_real_record(app_context):
    """HALL_CAPACITY returns one matching hall from the DB."""
    from app.models.hall import Hall

    hall = Hall.query.filter_by(is_active=True).first()
    assert hall is not None, "no active hall in seed data"

    result = execute_query("HALL_CAPACITY", {"hall": hall.name})

    assert result["success"] is True
    assert isinstance(result["data"], list)
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == hall.id
    assert result["data"][0]["name"] == hall.name


def test_execute_query_unknown_hall_returns_error(app_context):
    """HALL_CAPACITY with an unknown hall name returns a clean error."""
    result = execute_query(
        "HALL_CAPACITY", {"hall": "NO-SUCH-HALL-XYZ"}
    )

    assert result["success"] is False
    assert result["data"] is None
    assert "not found" in result["message"].lower()


def test_execute_query_students_in_hall(app_context):
    """STUDENTS_IN_HALL returns a non-negative count for a real hall."""
    from app.models.hall import Hall

    hall = Hall.query.filter_by(is_active=True).first()
    assert hall is not None

    result = execute_query("STUDENTS_IN_HALL", {"hall": hall.name})

    assert result["success"] is True
    assert result["data"]["hall_name"] == hall.name
    assert isinstance(result["data"]["students_allocated"], int)
    assert result["data"]["students_allocated"] >= 0


def test_execute_query_eligible_student_count(
    app_context, examination_id
):
    """ELIGIBLE_STUDENT_COUNT returns a real count for a real exam."""
    result = execute_query(
        "ELIGIBLE_STUDENT_COUNT",
        {"examination_id": examination_id},
    )

    assert result["success"] is True
    assert result["data"]["examination_id"] == examination_id
    assert isinstance(result["data"]["eligible_student_count"], int)
    assert result["data"]["eligible_student_count"] >= 0


def test_execute_query_registered_student_count(
    app_context, examination_id
):
    """REGISTERED_STUDENT_COUNT returns a real count for a real exam."""
    result = execute_query(
        "REGISTERED_STUDENT_COUNT",
        {"examination_id": examination_id},
    )

    assert result["success"] is True
    assert result["data"]["examination_id"] == examination_id
    assert isinstance(
        result["data"]["registered_student_count"], int
    )
    assert result["data"]["registered_student_count"] >= 0


def test_execute_query_halls_by_status_maintenance(app_context):
    """HALLS_BY_STATUS(maintenance) excludes available halls."""
    result = execute_query(
        "HALLS_BY_STATUS", {"status": "maintenance"}
    )

    assert result["success"] is True
    assert result["data"]["status_filter"] == "maintenance"
    for hall in result["data"]["halls"]:
        assert hall["is_under_maintenance"] is True


def test_execute_query_halls_by_status_rejects_unknown_filter(app_context):
    """An unknown status filter is rejected, not silently ignored."""
    result = execute_query(
        "HALLS_BY_STATUS", {"status": "burning"}
    )

    assert result["success"] is False
    assert result["data"] is None
    assert "unsupported" in result["message"].lower()


def test_execute_query_unallocated_students_requires_examination(app_context):
    """Missing examination_id triggers the internal guard."""
    result = execute_query("UNALLOCATED_STUDENT_COUNT", {})

    assert result["success"] is False
    assert "examination" in result["message"].lower()


def test_execute_query_unknown_intent_is_rejected(app_context):
    """An intent not in _HANDLERS is rejected cleanly."""
    result = execute_query("DROP_TABLE_STUDENTS", {})

    assert result["success"] is False
    assert result["data"] is None
    assert "unsupported intent" in result["message"].lower()


def test_execute_query_never_mutates_tables(
    app_context, examination_id
):
    """
    Run several supported intents and prove no table count changed.

    This is the strongest read-only guarantee we can make without
    mocking: after each call, every relevant table has the same
    row count it had before.
    """
    from app.models.examination import Examination
    from app.models.hall import Hall
    from app.models.student import Student
    from app.models.timetable import Timetable
    from app.models.seat_allocation import SeatAllocation
    from app.models.exam_registration import ExamRegistration

    def snapshot():
        return {
            "examinations": Examination.query.count(),
            "halls": Hall.query.count(),
            "students": Student.query.count(),
            "timetable": Timetable.query.count(),
            "seats": SeatAllocation.query.count(),
            "registrations": ExamRegistration.query.count(),
        }

    before = snapshot()

    execute_query("LIST_EXAMINATIONS", {})
    execute_query("HALLS_BY_STATUS", {"status": "available"})
    execute_query(
        "ELIGIBLE_STUDENT_COUNT",
        {"examination_id": examination_id},
    )
    execute_query(
        "REGISTERED_STUDENT_COUNT",
        {"examination_id": examination_id},
    )
    execute_query("HALL_ALLOCATION_SUMMARY", {})
    execute_query(
        "EXAMINATION_TIMETABLE",
        {"examination_id": examination_id},
    )

    after = snapshot()
    assert before == after