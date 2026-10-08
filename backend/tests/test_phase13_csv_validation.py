"""
Phase 13 — Intelligent CSV / Data Validation.

Tests the deterministic validator at
POST /api/import/<entity>/validate and the import path at
POST /api/import/<entity>/import.

No LLM. No autonomous correction. No silent insertion.
"""

import io
import uuid

import pytest

from app import db
from app.models.department import Department
from app.models.course import Course


# ============================================================
# Helpers
# ============================================================

def _csv_bytes(text):
    return io.BytesIO(text.encode("utf-8"))


def _post_validate(admin_client, entity, text):
    return admin_client.post(
        f"/api/import/{entity}/validate",
        data={"file": (_csv_bytes(text), "data.csv")},
        content_type="multipart/form-data",
    )


def _post_import(admin_client, entity, text):
    return admin_client.post(
        f"/api/import/{entity}/import",
        data={"file": (_csv_bytes(text), "data.csv")},
        content_type="multipart/form-data",
    )


def _unique_dept_code():
    return "T" + uuid.uuid4().hex[:8].upper()


# ============================================================
# 1. Valid CSV
# ============================================================

def test_valid_department_csv(admin_client, app_context):
    code = _unique_dept_code()
    csv = (
        "department_code,department_name\n"
        f"{code},Test Department {code}\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["valid"] is True
    assert body["summary"]["rows_checked"] == 1
    assert body["summary"]["error_count"] == 0
    assert body["summary"]["warning_count"] == 0
    assert body["errors"] == []
    assert body["warnings"] == []


# ============================================================
# 2. Missing required field
# ============================================================

def test_missing_required_field(admin_client, app_context):
    csv = "department_code,department_name\nABCD,\n"
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "REQUIRED_FIELD_MISSING" in codes
    assert any(
        e["field"] == "department_name"
        for e in body["errors"]
    )


# ============================================================
# 3. Duplicate identifier within CSV
# ============================================================

def test_duplicate_in_csv(admin_client, app_context):
    """
    Two rows sharing the same department_code must be
    flagged even when their department_name differs.
    """
    code = _unique_dept_code()
    csv = (
        "department_code,department_name\n"
        f"{code},First {code}\n"
        f"{code},Second {code}\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "DUPLICATE_IN_CSV" in codes
    assert any(
        "department_code" in e.get("field", "")
        for e in body["errors"]
        if e["code"] == "DUPLICATE_IN_CSV"
    )

def test_duplicate_in_csv_composite(admin_client, app_context):
    """
    Two rows sharing BOTH department_code and
    department_name must still be flagged.
    """
    code = _unique_dept_code()
    name = f"Compositely-Named {code}"
    csv = (
        "department_code,department_name\n"
        f"{code},{name}\n"
        f"{code},{name}\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "DUPLICATE_IN_CSV" in codes

# ============================================================
# 4. Duplicate identifier already in database
# ============================================================

def test_duplicate_in_database(admin_client, app_context):
    code = _unique_dept_code()
    db.session.add(
        Department(
            department_code=code,
            department_name=f"Existing {code}",
            is_active=True,
        )
    )
    db.session.commit()

    csv = (
        "department_code,department_name\n"
        f"{code},Attempted {code}\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "DUPLICATE_IN_DB" in codes


# ============================================================
# 5. Invalid email
# ============================================================

def test_invalid_email_student(admin_client, app_context):
    course = Course.query.first()
    assert course is not None
    csv = (
        "student_id,name,course_id,email,password,batch,semester\n"
        f"ST-{uuid.uuid4().hex[:6]},Test Student,"
        f"{course.id},not-an-email,pw,2024,1\n"
    )
    r = _post_validate(admin_client, "students", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "INVALID_EMAIL_FORMAT" in codes

def test_headers_are_normalized(admin_client, app_context):
    code = _unique_dept_code()

    csv = (
        " Department_Code , Department_Name \n"
        f"{code},Normalized Department\n"
    )

    r = _post_validate(
        admin_client,
        "departments",
        csv,
    )

    assert r.status_code == 200, r.get_json()

    body = r.get_json()

    assert body["valid"] is True
    assert body["errors"] == []

def test_value_normalization(admin_client, app_context):
    code = _unique_dept_code().lower()

    csv = (
        "department_code,department_name\n"
        f"  {code}  ,  Computer Science  \n"
    )

    r = _post_validate(
        admin_client,
        "departments",
        csv,
    )

    assert r.status_code == 200

    body = r.get_json()

    assert body["valid"] is True
    assert body["rows"][0]["data"]["department_code"] == code.upper()
    assert body["rows"][0]["data"]["department_name"] == "Computer Science"
    
# ============================================================
# 6. Unknown foreign key reference
# ============================================================

def test_unknown_course_reference_for_subject(
    admin_client, app_context
):
    csv = (
        "subject_code,subject_name,course_id,semester,subject_type\n"
        "SUB-TEST-1,Test Subject,999999,1,THEORY\n"
    )
    r = _post_validate(admin_client, "subjects", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "UNKNOWN_REFERENCE" in codes


# ============================================================
# 7. Invalid numeric value
# ============================================================

def test_invalid_integer(admin_client, app_context):
    csv = (
        "name,building_name,floor_no,capacity,"
        "examination_capacity,room_type\n"
        "Room X,Bldg A,not-a-number,40,40,LECTURE\n"
    )
    r = _post_validate(admin_client, "halls", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "INVALID_INTEGER" in codes


# ============================================================
# 8A. Invalid boolean value
# ============================================================

def test_invalid_boolean(admin_client, app_context):
    csv = (
        "name,department_id,email,designation,password,availability\n"
        "Test Staff,1,teststaff@example.com,Professor,password,maybe\n"
    )

    r = _post_validate(
        admin_client,
        "staff",
        csv,
    )

    body = r.get_json()

    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "INVALID_BOOLEAN" in codes


# ============================================================
# 8B. Invalid date value
# ============================================================

def test_invalid_date(admin_client, app_context):
    course = Course.query.first()
    assert course is not None

    csv = (
        "student_id,name,course_id,email,password,batch,semester,dob\n"
        f"ST-{uuid.uuid4().hex[:6]},Test Student,"
        f"{course.id},student@example.com,password,2024,1,31-12-2024\n"
    )

    r = _post_validate(
        admin_client,
        "students",
        csv,
    )

    body = r.get_json()

    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "INVALID_DATE" in codes

# ============================================================
# 8. Invalid value relation (exam_capacity > capacity)
# ============================================================

def test_exam_capacity_exceeds_capacity(admin_client, app_context):
    csv = (
        "name,building_name,floor_no,capacity,"
        "examination_capacity,room_type\n"
        "Room Y,Bldg B,0,30,50,LECTURE\n"
    )
    r = _post_validate(admin_client, "halls", csv)
    body = r.get_json()
    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "VALUE_RELATION_INVALID" in codes


# ============================================================
# 9. Empty CSV
# ============================================================

def test_empty_csv(admin_client, app_context):
    r = _post_validate(admin_client, "departments", "")
    assert r.status_code == 400
    body = r.get_json()
    assert body["success"] is False


# ============================================================
# 10. Empty data rows + malformed CSV
# ============================================================

def test_header_only_csv(admin_client, app_context):
    csv = "department_code,department_name\n"
    r = _post_validate(admin_client, "departments", csv)
    assert r.status_code == 400
    body = r.get_json()
    assert body["success"] is False
    assert "no data rows" in body["message"].lower()


def test_malformed_csv(admin_client, app_context):
    """
    Unclosed quoted field must be rejected as malformed CSV.
    """
    csv = (
        "department_code,department_name\n"
        'ABC,"Broken Department\n'
    )

    r = _post_validate(
        admin_client,
        "departments",
        csv,
    )

    assert r.status_code == 400
    body = r.get_json()
    assert body["success"] is False
    assert "csv" in body["message"].lower()

# ============================================================
# 11. Missing required columns
# ============================================================

def test_missing_required_columns(admin_client, app_context):
    csv = "department_code\nABC\n"
    r = _post_validate(admin_client, "departments", csv)
    assert r.status_code == 400


# ============================================================
# 12. Extra columns are tolerated
# ============================================================

def test_extra_columns_are_ignored(admin_client, app_context):
    code = _unique_dept_code()
    csv = (
        "department_code,department_name,extra_col\n"
        f"{code},Extra {code},anything\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    assert r.status_code == 200
    assert r.get_json()["valid"] is True


# ============================================================
# 13. Multiple errors in one CSV
# ============================================================

def test_multiple_errors(admin_client, app_context):
    csv = (
        "department_code,department_name\n"
        ",,\n"
        "B," + ("X" * 200) + "\n"
    )
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["valid"] is False
    assert body["summary"]["error_count"] >= 2


# ============================================================
# 14. Warnings
# ============================================================

def test_warning_possible_duplicate_name(
    admin_client, app_context
):
    course = Course.query.first()
    shared_name = f"DupName-{uuid.uuid4().hex[:6]}"
    csv = (
        "student_id,name,course_id,email,password,batch,semester\n"
        f"ST-{uuid.uuid4().hex[:6]},{shared_name},{course.id},"
        f"{uuid.uuid4().hex[:6]}@t.com,pw,2024,1\n"
        f"ST-{uuid.uuid4().hex[:6]},{shared_name},{course.id},"
        f"{uuid.uuid4().hex[:6]}@t.com,pw,2024,1\n"
    )
    r = _post_validate(admin_client, "students", csv)
    body = r.get_json()
    assert body["summary"]["warning_count"] >= 2
    codes = {w["code"] for w in body["warnings"]}
    assert "POSSIBLE_DUPLICATE_NAME" in codes


# ============================================================
# 15. Error report contains row + field
# ============================================================

def test_error_has_row_and_field(admin_client, app_context):
    csv = "department_code,department_name\nABCD,\n"
    r = _post_validate(admin_client, "departments", csv)
    body = r.get_json()
    assert body["errors"]
    e = body["errors"][0]
    assert "row" in e
    assert "field" in e
    assert "code" in e
    assert "message" in e


# ============================================================
# 16. Invalid CSV does not mutate database
# ============================================================

def test_invalid_csv_does_not_import(
    admin_client,
    app_context,
):
    before = Department.query.count()

    csv = (
        "department_code,department_name\n"
        "XYZ,\n"
    )

    r = _post_import(
        admin_client,
        "departments",
        csv,
    )

    after = Department.query.count()

    assert r.status_code == 400
    assert after == before

    body = r.get_json()

    assert body["success"] is False
    assert body["validation"]["valid_rows"] == 0
    
def test_valid_but_conflicting_csv_does_not_import(
    admin_client,
    app_context,
):
    code = _unique_dept_code()

    db.session.add(
        Department(
            department_code=code,
            department_name=f"Existing {code}",
            is_active=True,
        )
    )
    db.session.commit()

    before = Department.query.count()

    csv = (
        "department_code,department_name\n"
        f"{code},New {code}\n"
    )

    r = _post_import(
        admin_client,
        "departments",
        csv,
    )

    after = Department.query.count()

    print(r.get_json())
 
    assert r.status_code == 400

    body = r.get_json()

    assert body["success"] is False
    assert body["message"] == "There are no valid rows available for import."
    assert body["validation"]["valid_rows"] == 0
    assert body["validation"]["duplicate_rows"] == 1
    assert body["validation"]["invalid_rows"] == 0
    
    assert after == before

# ============================================================
# 17. Valid CSV still imports
# ============================================================

def test_valid_csv_imports(admin_client, app_context):
    code = _unique_dept_code()
    csv = (
        "department_code,department_name\n"
        f"{code},Imported {code}\n"
    )
    r = _post_import(admin_client, "departments", csv)
    assert r.status_code == 200, r.get_json()
    assert Department.query.filter_by(
        department_code=code
    ).first() is not None


# ============================================================
# 18. Existing behavior: partial import still works
# ============================================================

def test_partial_import_is_preserved(admin_client, app_context):
    """
    The existing importer intentionally imports valid rows
    even when some rows are invalid. Preserve that
    behavior (single valid + single invalid).
    """
    code = _unique_dept_code()
    csv = (
        "department_code,department_name\n"
        f"{code},Valid {code}\n"
        ",\n"
    )
    r = _post_import(admin_client, "departments", csv)
    assert r.status_code == 200, r.get_json()
    assert Department.query.filter_by(
        department_code=code
    ).first() is not None


# ============================================================
# 19. Phase 2 master data unaffected
# ============================================================

def test_department_lookup_still_works(app_context):
    assert Department.query.count() > 0


# ============================================================
# 20–23. Regression hooks for other features
# ============================================================

def test_feature18_parser_still_works():
    from app.services.requirement_parser import parse_requirements
    result = parse_requirements("Use minimum halls.")
    assert result["success"] is True
    assert result["requirements"]["minimize_halls"] is True


def test_feature20_explanation_still_works(app_context):
    from app.services.explanation import REASON_CODES
    assert "REJECTED_TRANSIENTLY_EXCLUDED" in REASON_CODES
    assert "SELECTED_BY_ALLOCATOR_STRATEGY" in REASON_CODES


def test_feature21_reallocation_module_still_imports():
    from app.services.reallocation import (
        simulate_reallocation,
        apply_reallocation,
    )
    assert callable(simulate_reallocation)
    assert callable(apply_reallocation)


# ============================================================
# RBAC
# ============================================================

def test_validate_requires_admin(client, app_context):
    r = client.post(
        "/api/import/departments/validate",
        data={"file": (_csv_bytes("a,b\nx,y\n"), "d.csv")},
        content_type="multipart/form-data",
    )
    assert r.status_code in (401, 403)


def test_import_requires_admin(client, app_context):
    r = client.post(
        "/api/import/departments/import",
        data={"file": (_csv_bytes("a,b\nx,y\n"), "d.csv")},
        content_type="multipart/form-data",
    )
    assert r.status_code in (401, 403)

# ============================================================
# Foreign-key validation coverage
# ============================================================

def test_unknown_department_reference_for_course(
    admin_client,
    app_context,
):
    csv = (
        "course_code,course_name,course_abbreviation,"
        "program_level,study_shift,session,department_id,total_semesters\n"
        "COURSE-TEST,Test Course,TC,UG,MORNING,2026,999999,8\n"
    )

    r = _post_validate(
        admin_client,
        "courses",
        csv,
    )

    body = r.get_json()

    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "UNKNOWN_REFERENCE" in codes

def test_unknown_course_reference_for_student(
    admin_client,
    app_context,
):
    csv = (
        "student_id,name,course_id,email,password,batch,semester\n"
        f"ST-{uuid.uuid4().hex[:6]},Test Student,"
        f"999999,student@example.com,password,2024,1\n"
    )

    r = _post_validate(
        admin_client,
        "students",
        csv,
    )

    body = r.get_json()

    assert body["valid"] is False
    codes = {e["code"] for e in body["errors"]}
    assert "UNKNOWN_REFERENCE" in codes

# ============================================================
# Capacity boundary validation
# ============================================================

@pytest.mark.parametrize(
    "capacity,examination_capacity",
    [
        ("0", "0"),
        ("-1", "10"),
        ("10", "0"),
        ("10", "-1"),
    ],
)
def test_invalid_hall_capacity_values(
    admin_client,
    app_context,
    capacity,
    examination_capacity,
):
    csv = (
        "name,building_name,floor_no,capacity,"
        "examination_capacity,room_type\n"
        f"Room-{uuid.uuid4().hex[:6]},Building A,0,"
        f"{capacity},{examination_capacity},LECTURE\n"
    )

    r = _post_validate(
        admin_client,
        "halls",
        csv,
    )

    body = r.get_json()

    assert body["valid"] is False

    codes = {e["code"] for e in body["errors"]}

    assert "VALUE_OUT_OF_RANGE" in codes