import csv
import io
import re
from datetime import datetime

from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash

from app import db
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject
from app.models.student import Student
from app.models.staff import Staff
from app.models.hall import Hall


# =========================================================
# Structured issue model (Feature — Intelligent CSV)
# =========================================================
#
# Every validator emits issues as dicts instead of plain
# strings. The import path (import_valid_rows) still
# receives a flat list of messages, built from these
# issues, so its behaviour is unchanged.

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"


def _issue(code, field, message, severity=SEVERITY_ERROR):
    return {
        "code": code,
        "field": field,
        "message": message,
        "severity": severity,
    }


def _messages(issues):
    """
    Backward-compatible helper: convert structured issues
    into the flat list of strings the import path expects.
    """
    return [issue["message"] for issue in issues]

def is_valid_email(value):
    """
    Deterministic basic email validation for CSV imports.
    """
    if not value:
        return False

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            value.strip(),
        )
    )

ENTITY_CONFIG = {
    "departments": {
        "model": Department,
        "required_columns": [
            "department_code",
            "department_name",
        ],
        "unique_fields": [
            "department_code",
            "department_name",
        ],
    },
    "courses": {
        "model": Course,
        "required_columns": [
            "course_code",
            "course_name",
            "course_abbreviation",
            "program_level",
            "study_shift",
            "session",
            "department_id",
            "total_semesters",
        ],
        "unique_fields": [
            "course_code",
            "course_abbreviation",
        ],
    },
    "subjects": {
        "model": Subject,
        "required_columns": [
            "subject_code",
            "subject_name",
            "course_id",
            "semester",
            "subject_type",
        ],
        "unique_fields": [
            "subject_code",
        ],
    },
    "students": {
        "model": Student,
        "required_columns": [
            "student_id",
            "name",
            "course_id",
            "email",
            "password",
            "batch",
            "semester",
        ],
        "unique_fields": [
            "student_id",
            "email",
        ],
    },
    "staff": {
        "model": Staff,
        "required_columns": [
            "name",
            "department_id",
            "email",
            "designation",
            "password",
        ],
        "unique_fields": [
            "email",
        ],
    },
    "halls": {
        "model": Hall,
        "required_columns": [
            "name",
            "building_name",
            "floor_no",
            "capacity",
            "examination_capacity",
            "room_type",
        ],
        "unique_fields": [],
    },
}


BOOLEAN_FIELDS = {
    "students": [],
    "staff": [
        "availability",
    ],
    "halls": [
        "is_available",
        "is_under_maintenance",
        "is_accessible",
    ],
}


DATE_FIELDS = {
    "students": [
        "dob",
    ],
    "staff": [
        "dob",
    ],
    "halls": [],
}


INTEGER_FIELDS = {
    "courses": [
        "department_id",
        "total_semesters",
    ],
    "subjects": [
        "course_id",
        "semester",
    ],
    "students": [
        "course_id",
        "semester",
    ],
    "staff": [
        "department_id",
    ],
    "halls": [
        "floor_no",
        "capacity",
        "examination_capacity",
        "assigned_course_id",
    ],
}


def validate_csv_file(file: FileStorage):
    """
    Validate the uploaded CSV file and return decoded text.

    Returns:
        {
            "success": True,
            "content": "...",
        }

    or:

        {
            "success": False,
            "message": "...",
        }
    """

    if not file:
        return {
            "success": False,
            "message": "CSV file is required.",
        }

    if not file.filename:
        return {
            "success": False,
            "message": "CSV file name is required.",
        }

    if not file.filename.lower().endswith(".csv"):
        return {
            "success": False,
            "message": "Only CSV files are allowed.",
        }

    try:
        raw_content = file.read()

        if not raw_content:
            return {
                "success": False,
                "message": "The uploaded CSV file is empty.",
            }

        try:
            content = raw_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return {
                "success": False,
                "message": "CSV file must use UTF-8 encoding.",
            }

        if not content.strip():
            return {
                "success": False,
                "message": "The uploaded CSV file is empty.",
            }

        return {
            "success": True,
            "content": content,
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Unable to read CSV file: {str(exc)}",
        }


def normalize_entity(entity):
    """
    Normalize the entity name received from the API.
    """

    if not entity:
        return None

    entity = entity.strip().lower()

    aliases = {
        "department": "departments",
        "departments": "departments",
        "course": "courses",
        "courses": "courses",
        "subject": "subjects",
        "subjects": "subjects",
        "student": "students",
        "students": "students",
        "staff": "staff",
        "hall": "halls",
        "halls": "halls",
    }

    return aliases.get(entity)


def normalize_value(value):
    """
    Normalize a CSV cell value.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_headers(headers):
    """
    Normalize CSV headers by trimming whitespace and
    converting them to lowercase.
    """

    normalized = []

    for header in headers or []:
        normalized.append(
            normalize_value(header).lower()
        )

    return normalized


def validate_headers(entity, headers):
    """
    Validate the CSV header structure for an entity.
    """

    entity = normalize_entity(entity)

    if not entity:
        return {
            "success": False,
            "message": "Unsupported import entity.",
        }

    config = ENTITY_CONFIG[entity]

    normalized_headers = normalize_headers(headers)

    if not normalized_headers:
        return {
            "success": False,
            "message": "CSV header row is missing.",
        }

    if "" in normalized_headers:
        return {
            "success": False,
            "message": "CSV contains an empty column name.",
        }

    if len(normalized_headers) != len(set(normalized_headers)):
        return {
            "success": False,
            "message": "CSV contains duplicate column names.",
        }

    missing_columns = [
        column
        for column in config["required_columns"]
        if column not in normalized_headers
    ]

    if missing_columns:
        return {
            "success": False,
            "message": "Required CSV columns are missing.",
            "missing_columns": missing_columns,
        }

    return {
        "success": True,
        "headers": normalized_headers,
    }


def parse_csv(entity, content):
    """
    Parse CSV content into normalized dictionaries.
    """

    entity = normalize_entity(entity)

    if not entity:
        return {
            "success": False,
            "message": "Unsupported import entity.",
        }

    try:
        reader = csv.DictReader(
            io.StringIO(content),
            strict=True,
        )

        headers_result = validate_headers(
            entity,
            reader.fieldnames or [],
        )

        if not headers_result["success"]:
            return headers_result

        normalized_headers = headers_result["headers"]

        header_map = {
            original: normalized
            for original, normalized in zip(
                reader.fieldnames or [],
                normalized_headers,
            )
        }

        rows = []

        for row_number, raw_row in enumerate(reader, start=2):
            normalized_row = {}

            for original_header, normalized_header in header_map.items():
                normalized_row[normalized_header] = normalize_value(
                    raw_row.get(original_header, "")
                )

            rows.append(
                {
                    "row_number": row_number,
                    "data": normalized_row,
                }
            )

        if not rows:
            return {
                "success": False,
                "message": "CSV contains no data rows.",
            }

        return {
            "success": True,
            "headers": normalized_headers,
            "rows": rows,
        }

    except csv.Error as exc:
        return {
            "success": False,
            "message": f"Invalid CSV format: {str(exc)}",
        }

    except Exception as exc:
        return {
            "success": False,
            "message": f"Unable to parse CSV: {str(exc)}",
        }


def parse_integer(value, field_name):
    """
    Convert a CSV value to integer.
    """

    if value == "":
        raise ValueError(
            f"{field_name} is required."
        )

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be an integer."
        )


def parse_boolean(value, field_name):
    """
    Convert common CSV boolean values to bool.
    """

    if value == "":
        raise ValueError(
            f"{field_name} must be true or false."
        )

    normalized = value.strip().lower()

    true_values = {
        "true",
        "1",
        "yes",
        "y",
    }

    false_values = {
        "false",
        "0",
        "no",
        "n",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise ValueError(
        f"{field_name} must be true or false."
    )


def parse_date(value, field_name):
    """
    Parse an ISO date value.
    """

    if value == "":
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        raise ValueError(
            f"{field_name} must use YYYY-MM-DD format."
        )

def validate_required_fields(entity, data):
    """
    Validate all required fields for an entity.
    """

    config = ENTITY_CONFIG[entity]

    issues = []

    for field in config["required_columns"]:
        if not normalize_value(data.get(field)):
            issues.append(
                _issue(
                    "REQUIRED_FIELD_MISSING",
                    field,
                    f"{field} is required.",
                )
            )

    return issues

def validate_integer_fields(entity, data):
    """
    Validate integer fields.
    """

    issues = []

    for field in INTEGER_FIELDS.get(entity, []):
        value = data.get(field, "")

        if value == "":
            continue

        try:
            int(value)
        except (TypeError, ValueError):
            issues.append(
                _issue(
                    "INVALID_INTEGER",
                    field,
                    f"{field} must be an integer.",
                )
            )

    return issues


def validate_boolean_fields(entity, data):
    """
    Validate boolean fields.
    """

    issues = []

    for field in BOOLEAN_FIELDS.get(entity, []):
        value = data.get(field, "")

        if value == "":
            continue

        try:
            parse_boolean(value, field)
        except ValueError as exc:
            issues.append(
                _issue(
                    "INVALID_BOOLEAN",
                    field,
                    str(exc),
                )
            )

    return issues

def validate_date_fields(entity, data):
    """
    Validate date fields.
    """

    issues = []

    for field in DATE_FIELDS.get(entity, []):
        value = data.get(field, "")

        if value == "":
            continue

        try:
            parse_date(value, field)
        except ValueError as exc:
            issues.append(
                _issue(
                    "INVALID_DATE",
                    field,
                    str(exc),
                )
            )

    return issues

def validate_foreign_keys(entity, data):
    """
    Validate foreign-key references.
    """

    issues = []

    if entity == "courses":
        department_id = data.get("department_id")

        if department_id:
            try:
                department_id = int(department_id)

                department = db.session.get(
                    Department,
                    department_id,
                )

                if not department:
                    issues.append(
                        _issue(
                            "UNKNOWN_REFERENCE",
                            "department_id",
                            f"Department ID {department_id} does not exist.",
                        )
                    )

            except ValueError:
                pass

    elif entity == "subjects":
        course_id = data.get("course_id")

        if course_id:
            try:
                course_id = int(course_id)

                course = db.session.get(
                    Course,
                    course_id,
                )

                if not course:
                    issues.append(
                        _issue(
                            "UNKNOWN_REFERENCE",
                            "course_id",
                            f"Course ID {course_id} does not exist.",
                        )
                    )

            except ValueError:
                pass

    elif entity == "students":
        course_id = data.get("course_id")

        if course_id:
            try:
                course_id = int(course_id)

                course = db.session.get(
                    Course,
                    course_id,
                )

                if not course:
                    issues.append(
                        _issue(
                            "UNKNOWN_REFERENCE",
                            "course_id",
                            f"Course ID {course_id} does not exist.",
                        )
                    )

            except ValueError:
                pass

    elif entity == "staff":
        department_id = data.get("department_id")

        if department_id:
            try:
                department_id = int(department_id)

                department = db.session.get(
                    Department,
                    department_id,
                )

                if not department:
                    issues.append(
                        _issue(
                            "UNKNOWN_REFERENCE",
                            "department_id",
                            f"Department ID {department_id} does not exist.",
                        )
                    )

            except ValueError:
                pass

    elif entity == "halls":
        assigned_course_id = data.get(
            "assigned_course_id"
        )

        if assigned_course_id:
            try:
                assigned_course_id = int(
                    assigned_course_id
                )

                course = db.session.get(
                    Course,
                    assigned_course_id,
                )

                if not course:
                    issues.append(
                        _issue(
                            "UNKNOWN_REFERENCE",
                            "assigned_course_id",
                            f"Assigned course ID {assigned_course_id} does not exist.",
                        )
                    )

            except ValueError:
                pass

    return issues

def validate_entity_rules(entity, data):
    """
    Validate entity-specific business rules.
    """

    issues = []

    if entity == "departments":
        code = data.get("department_code", "").strip()
        name = data.get("department_name", "").strip()

        if code and len(code) > 20:
            issues.append(
                _issue(
                    "VALUE_OUT_OF_RANGE",
                    "department_code",
                    "department_code cannot exceed 20 characters.",
                )
            )

        if name and len(name) > 100:
            issues.append(
                _issue(
                    "VALUE_OUT_OF_RANGE",
                    "department_name",
                    "department_name cannot exceed 100 characters.",
                )
            )

    elif entity == "courses":
        total_semesters = data.get(
            "total_semesters",
            "",
        )

        if total_semesters:
            try:
                if int(total_semesters) <= 0:
                    issues.append(
                        _issue(
                            "VALUE_OUT_OF_RANGE",
                            "total_semesters",
                            "total_semesters must be greater than 0.",
                        )
                    )
            except ValueError:
                pass

    elif entity == "subjects":
        course_id = data.get("course_id")
        semester = data.get("semester")

        if course_id and semester:
            try:
                course = db.session.get(
                    Course,
                    int(course_id),
                )

                if course:
                    semester_value = int(semester)

                    if semester_value < 1:
                        issues.append(
                            _issue(
                                "VALUE_OUT_OF_RANGE",
                                "semester",
                                "semester must be at least 1.",
                            )
                        )

                    elif semester_value > course.total_semesters:
                        issues.append(
                            _issue(
                                "VALUE_RELATION_INVALID",
                                "semester",
                                "semester cannot exceed the course total semesters.",
                            )
                        )

            except ValueError:
                pass

    elif entity == "students":
        semester = data.get("semester")
        course_id = data.get("course_id")

        if semester and course_id:
            try:
                course = db.session.get(
                    Course,
                    int(course_id),
                )

                if course:
                    semester_value = int(semester)

                    if semester_value < 1:
                        issues.append(
                            _issue(
                                "VALUE_OUT_OF_RANGE",
                                "semester",
                                "semester must be at least 1.",
                            )
                        )

                    elif semester_value > course.total_semesters:
                        issues.append(
                            _issue(
                                "VALUE_RELATION_INVALID",
                                "semester",
                                "semester cannot exceed the course total semesters.",
                            )
                        )

            except ValueError:
                pass

        email = data.get("email", "").strip()

        if email and not is_valid_email(email):
            issues.append(
                _issue(
                    "INVALID_EMAIL_FORMAT",
                    "email",
                    "email must be a valid email address.",
                )
            )

    elif entity == "staff":
        email = data.get("email", "").strip()

        if email and not is_valid_email(email):
            issues.append(
                _issue(
                    "INVALID_EMAIL_FORMAT",
                    "email",
                    "email must be a valid email address.",
                )
            )

    elif entity == "halls":
        capacity = data.get("capacity")
        examination_capacity = data.get(
            "examination_capacity"
        )
        floor_no = data.get("floor_no")

        if capacity:
            try:
                if int(capacity) <= 0:
                    issues.append(
                        _issue(
                            "VALUE_OUT_OF_RANGE",
                            "capacity",
                            "capacity must be greater than 0.",
                        )
                    )
            except ValueError:
                pass

        if examination_capacity:
            try:
                if int(examination_capacity) <= 0:
                    issues.append(
                        _issue(
                            "VALUE_OUT_OF_RANGE",
                            "examination_capacity",
                            "examination_capacity must be greater than 0.",
                        )
                    )
            except ValueError:
                pass

        if capacity and examination_capacity:
            try:
                if int(examination_capacity) > int(capacity):
                    issues.append(
                        _issue(
                            "VALUE_RELATION_INVALID",
                            "examination_capacity",
                            "examination_capacity cannot exceed capacity.",
                        )
                    )
            except ValueError:
                pass

        if floor_no:
            try:
                if int(floor_no) < 0:
                    issues.append(
                        _issue(
                            "VALUE_OUT_OF_RANGE",
                            "floor_no",
                            "floor_no cannot be negative.",
                        )
                    )
            except ValueError:
                pass

    return issues

def normalize_entity_data(entity, data):
    """
    Normalize entity-specific values before import.
    """

    normalized = dict(data)

    if entity == "departments":
        normalized["department_code"] = (
            normalized.get("department_code", "")
            .strip()
            .upper()
        )

        normalized["department_name"] = (
            normalized.get("department_name", "")
            .strip()
        )

    elif entity == "courses":
        normalized["course_code"] = (
            normalized.get("course_code", "")
            .strip()
            .upper()
        )

        normalized["course_name"] = (
            normalized.get("course_name", "")
            .strip()
        )

        normalized["course_abbreviation"] = (
            normalized.get("course_abbreviation", "")
            .strip()
            .upper()
        )

    elif entity == "subjects":
        normalized["subject_code"] = (
            normalized.get("subject_code", "")
            .strip()
            .upper()
        )

        normalized["subject_name"] = (
            normalized.get("subject_name", "")
            .strip()
        )

        normalized["subject_type"] = (
            normalized.get("subject_type", "")
            .strip()
            .upper()
        )

    elif entity == "students":
        normalized["student_id"] = (
            normalized.get("student_id", "")
            .strip()
        )

        normalized["name"] = (
            normalized.get("name", "")
            .strip()
        )

        normalized["email"] = (
            normalized.get("email", "")
            .strip()
            .lower()
        )

        normalized["batch"] = (
            normalized.get("batch", "")
            .strip()
        )

    elif entity == "staff":
        normalized["name"] = (
            normalized.get("name", "")
            .strip()
        )

        normalized["email"] = (
            normalized.get("email", "")
            .strip()
            .lower()
        )

        normalized["designation"] = (
            normalized.get("designation", "")
            .strip()
        )

    elif entity == "halls":
        normalized["name"] = (
            normalized.get("name", "")
            .strip()
        )

        normalized["building_name"] = (
            normalized.get("building_name", "")
            .strip()
        )

        normalized["room_type"] = (
            normalized.get("room_type", "")
            .strip()
        )

    return normalized


def get_duplicate_key(entity, data):
    """
    Build a normalized duplicate key for a CSV row.
    """

    config = ENTITY_CONFIG[entity]

    values = []

    for field in config["unique_fields"]:
        value = normalize_value(
            data.get(field)
        ).lower()

        values.append(value)

    return tuple(values)

def detect_csv_duplicates(entity, rows):
    """
    Detect duplicate records inside the uploaded CSV.

    Two rows are treated as duplicates when they share the
    same value on ANY field listed in the entity's
    unique_fields. This mirrors the model: each field with
    unique=True is enforced independently by the database.

    Returns a mapping of row_number -> list of field names
    that collided with an earlier row.
    """

    config = ENTITY_CONFIG[entity]

    # Per-field first-seen maps. Key is (field, value).
    seen = {}
    duplicate_fields_by_row = {}

    for row in rows:
        data = row["data"]

        for field in config["unique_fields"]:
            value = normalize_value(data.get(field)).lower()

            if not value:
                continue

            key = (field, value)

            if key in seen:
                duplicate_fields_by_row.setdefault(
                    row["row_number"], []
                ).append(field)
            else:
                seen[key] = row["row_number"]

    return duplicate_fields_by_row

def record_exists_in_database(entity, data):
    """
    Check whether a CSV record already exists in the database.
    """

    if entity == "departments":
        return (
            db.session.query(Department)
            .filter(
                db.or_(
                    db.func.lower(
                        Department.department_code
                    )
                    == data["department_code"].lower(),
                    db.func.lower(
                        Department.department_name
                    )
                    == data["department_name"].lower(),
                )
            )
            .first()
            is not None
        )

    if entity == "courses":
        return (
            db.session.query(Course)
            .filter(
                db.or_(
                    db.func.lower(
                        Course.course_code
                    )
                    == data["course_code"].lower(),
                    db.func.lower(
                        Course.course_abbreviation
                    )
                    == data["course_abbreviation"].lower(),
                )
            )
            .first()
            is not None
        )

    if entity == "subjects":
        return (
            db.session.query(Subject)
            .filter(
                db.func.lower(
                    Subject.subject_code
                )
                == data["subject_code"].lower()
            )
            .first()
            is not None
        )

    if entity == "students":
        return (
            db.session.query(Student)
            .filter(
                db.or_(
                    Student.student_id
                    == data["student_id"],
                    db.func.lower(
                        Student.email
                    )
                    == data["email"].lower(),
                )
            )
            .first()
            is not None
        )

    if entity == "staff":
        return (
            db.session.query(Staff)
            .filter(
                db.func.lower(
                    Staff.email
                )
                == data["email"].lower()
            )
            .first()
            is not None
        )

    if entity == "halls":
        return (
            db.session.query(Hall)
            .filter(
                db.func.lower(
                    Hall.name
                )
                == data["name"].lower(),
                db.func.lower(
                    Hall.building_name
                )
                == data["building_name"].lower(),
            )
            .first()
            is not None
        )

    return False


def detect_possible_duplicate_names(entity, rows):
    """
    Return a mapping of row_number -> warning issue when a
    row's primary name field exactly matches the same field
    in another row of the same CSV, but the row's unique
    identifier differs.

    Deterministic. No fuzzy matching, no edit distance.
    Only applies to entities whose model has a name field.
    """

    name_field_by_entity = {
        "students": "name",
        "staff": "name",
        "halls": "name",
    }

    name_field = name_field_by_entity.get(entity)

    if not name_field:
        return {}

    # Group rows by normalized name.
    by_name = {}

    for row in rows:
        raw = normalize_value(row["data"].get(name_field))
        if not raw:
            continue
        key = raw.lower()
        by_name.setdefault(key, []).append(row)

    warnings_by_row = {}

    for key, group in by_name.items():
        if len(group) < 2:
            continue

        # Distinguish by the entity's primary/unique identifier.
        if entity == "students":
            id_field = "student_id"
        elif entity == "staff":
            id_field = "email"
        else:
            id_field = "building_name"

        ids = set()
        for row in group:
            ids.add(
                normalize_value(row["data"].get(id_field)).lower()
            )

        if len(ids) < 2:
            # Identical names AND identical identifiers is a
            # duplicate, not a warning. Leave it to the
            # duplicate detectors.
            continue

        for row in group:
            warnings_by_row[row["row_number"]] = _issue(
                "POSSIBLE_DUPLICATE_NAME",
                name_field,
                (
                    f"{name_field} '{row['data'].get(name_field)}' "
                    "matches another row in this CSV; please "
                    "verify it is not a duplicate."
                ),
                severity=SEVERITY_WARNING,
            )

    return warnings_by_row
def validate_row(entity, data):
    """
    Run all validations for a single CSV row.

    Returns structured issues. The "errors" key is retained
    as a flat list of strings so existing callers that only
    read error messages keep working.
    """

    data = normalize_entity_data(
        entity,
        data,
    )

    issues = []

    issues.extend(
        validate_required_fields(
            entity,
            data,
        )
    )

    issues.extend(
        validate_integer_fields(
            entity,
            data,
        )
    )

    issues.extend(
        validate_boolean_fields(
            entity,
            data,
        )
    )

    issues.extend(
        validate_date_fields(
            entity,
            data,
        )
    )

    issues.extend(
        validate_foreign_keys(
            entity,
            data,
        )
    )

    issues.extend(
        validate_entity_rules(
            entity,
            data,
        )
    )

    error_issues = [
        i for i in issues
        if i["severity"] == SEVERITY_ERROR
    ]

    return {
        "data": data,
        "issues": issues,
        "errors": _messages(error_issues),
        "valid": len(error_issues) == 0,
    }
    
def validate_csv(entity, content):
    """
    Complete CSV validation pipeline.

    Emits a structured validation report:

        {
          "success": True,
          "valid": bool,
          "entity": str,
          "summary": {
            "rows_checked": int,
            "valid_rows": int,
            "error_count": int,
            "warning_count": int,
          },
          "errors": [issue, ...],     # severity == "error"
          "warnings": [issue, ...],   # severity == "warning"
          "total_rows": int,
          "valid_rows": int,
          "invalid_rows": int,
          "duplicate_rows": int,
          "rows": [ {row_number, status, data, issues, errors}, ... ],
        }

    The per-row "errors" list of strings is preserved so
    import_valid_rows() continues to work unchanged.
    """

    entity = normalize_entity(entity)

    if not entity:
        return {
            "success": False,
            "message": "Unsupported import entity.",
        }

    parsed = parse_csv(
        entity,
        content,
    )

    if not parsed["success"]:
        return parsed

    rows = parsed["rows"]

    csv_duplicate_fields_by_row = detect_csv_duplicates(
        entity,
        rows,
    )

    warning_by_row = detect_possible_duplicate_names(
        entity,
        rows,
    )

    validated_rows = []

    valid_count = 0
    invalid_count = 0
    duplicate_count = 0

    top_errors = []
    top_warnings = []

    for row in rows:
        row_number = row["row_number"]

        result = validate_row(
            entity,
            row["data"],
        )

        status = "valid"
        issues = list(result["issues"])

        if row_number in csv_duplicate_fields_by_row:
            status = "duplicate"
            colliding_fields = csv_duplicate_fields_by_row[
                row_number
            ]
            issues.append(
                _issue(
                    "DUPLICATE_IN_CSV",
                    ",".join(colliding_fields),
                    (
                        "Duplicate row found within uploaded CSV "
                        "(collides on: "
                        + ", ".join(colliding_fields) + ")."
                    ),
                )
            )

        elif result["valid"] and record_exists_in_database(
            entity,
            result["data"],
        ):
            status = "duplicate"
            issues.append(
                _issue(
                    "DUPLICATE_IN_DB",
                    ",".join(
                        ENTITY_CONFIG[entity]["unique_fields"]
                    ),
                    "Record already exists in database.",
                )
            )

        elif not result["valid"]:
            status = "invalid"

        # Add a per-row warning (if any).
        if (
            row_number in warning_by_row
            and status != "duplicate"
        ):
            warning = warning_by_row[row_number]
            issues.append(warning)

        if status == "valid":
            valid_count += 1

        elif status == "invalid":
            invalid_count += 1

        elif status == "duplicate":
            duplicate_count += 1

        # Split issues for the top-level arrays.
        row_error_issues = [
            i for i in issues
            if i["severity"] == SEVERITY_ERROR
        ]
        row_warning_issues = [
            i for i in issues
            if i["severity"] == SEVERITY_WARNING
        ]

        for issue in row_error_issues:
            top_errors.append({
                "row": row_number,
                **issue,
            })

        for issue in row_warning_issues:
            top_warnings.append({
                "row": row_number,
                **issue,
            })

        validated_rows.append(
            {
                "row_number": row_number,
                "status": status,
                "data": result["data"],
                "issues": issues,
                "errors": _messages(row_error_issues),
            }
        )

    is_valid = (
        len(top_errors) == 0
        and duplicate_count == 0
        and invalid_count == 0
    )

    return {
        "success": True,
        "valid": is_valid,
        "entity": entity,
        "summary": {
            "rows_checked": len(rows),
            "valid_rows": valid_count,
            "error_count": len(top_errors),
            "warning_count": len(top_warnings),
        },
        "errors": top_errors,
        "warnings": top_warnings,
        "total_rows": len(rows),
        "valid_rows": valid_count,
        "invalid_rows": invalid_count,
        "duplicate_rows": duplicate_count,
        "rows": validated_rows,
    }

def build_model_instance(entity, data):
    """
    Convert validated CSV data into a SQLAlchemy model instance.

    This function is intentionally kept separate from validation.
    """

    if entity == "departments":
        return Department(
            department_code=data["department_code"],
            department_name=data["department_name"],
            is_active=True,
        )

    if entity == "courses":
        return Course(
            course_code=data["course_code"],
            course_name=data["course_name"],
            course_abbreviation=data[
                "course_abbreviation"
            ],
            program_level=data["program_level"],
            department_id=int(
                data["department_id"]
            ),
            study_shift=data["study_shift"],
            session=data["session"],
            total_semesters=int(
                data["total_semesters"]
            ),
            is_active=True,
        )

    if entity == "subjects":
        return Subject(
            subject_code=data["subject_code"],
            subject_name=data["subject_name"],
            course_id=int(
                data["course_id"]
            ),
            semester=int(
                data["semester"]
            ),
            subject_type=data["subject_type"],
            is_active=True,
        )

    if entity == "students":
        return Student(
            student_id=data["student_id"],
            name=data["name"],
            course_id=int(
                data["course_id"]
            ),
            email=data["email"],
            password_hash=generate_password_hash(
                data["password"]
            ),
            contact_no=data.get("contact_no") or None,
            gender=data.get("gender") or None,
            disability=data.get("disability") or None,
            batch=data["batch"],
            semester=int(
                data["semester"]
            ),
            class_name=data.get("class_name") or None,
            session=data.get("session") or None,
            dob=parse_date(
                data.get("dob", ""),
                "dob",
            ),
            student_img=data.get("student_img") or None,
            is_active=True,
        )

    if entity == "staff":
        availability = True

        if data.get("availability"):
            availability = parse_boolean(
                data["availability"],
                "availability",
            )

        return Staff(
            name=data["name"],
            department_id=int(
                data["department_id"]
            ),
            email=data["email"],
            contact_no=data.get("contact_no") or None,
            designation=data["designation"],
            dob=parse_date(
                data.get("dob", ""),
                "dob",
            ),
            assigned_courses=data.get(
                "assigned_courses"
            ) or None,
            gender=data.get("gender") or None,
            availability=availability,
            assigned_batch=data.get(
                "assigned_batch"
            ) or None,
            password_hash=generate_password_hash(
                data["password"]
            ),
            image=data.get("image") or None,
            is_active=True,
        )

    if entity == "halls":
        def optional_boolean(field, default):
            value = data.get(field, "")

            if value == "":
                return default

            return parse_boolean(
                value,
                field,
            )

        assigned_course_id = None

        if data.get("assigned_course_id"):
            assigned_course_id = int(
                data["assigned_course_id"]
            )

        return Hall(
            name=data["name"],
            building_name=data["building_name"],
            floor_no=int(
                data["floor_no"]
            ),
            capacity=int(
                data["capacity"]
            ),
            examination_capacity=int(
                data["examination_capacity"]
            ),
            room_type=data["room_type"],
            amenities=data.get("amenities") or None,
            is_available=optional_boolean(
                "is_available",
                True,
            ),
            is_under_maintenance=optional_boolean(
                "is_under_maintenance",
                False,
            ),
            is_accessible=optional_boolean(
                "is_accessible",
                True,
            ),
            assigned_course_id=assigned_course_id,
            assigned_batch=data.get(
                "assigned_batch"
            ) or None,
            is_active=True,
        )

    raise ValueError(
        "Unsupported import entity."
    )


def import_valid_rows(entity, validation_result):
    """
    Import only rows that passed validation.

    Returns an import summary.
    """

    entity = normalize_entity(entity)

    if not entity:
        return {
            "success": False,
            "message": "Unsupported import entity.",
        }

    if not validation_result.get("success"):
        return {
            "success": False,
            "message": "CSV must be validated before import.",
        }

    rows = validation_result.get(
        "rows",
        [],
    )

    valid_rows = [
        row
        for row in rows
        if row.get("status") == "valid"
    ]

    imported_count = 0

    try:
        for row in valid_rows:
            instance = build_model_instance(
                entity,
                row["data"],
            )

            db.session.add(instance)
            imported_count += 1

        db.session.commit()

        return {
            "success": True,
            "entity": entity,
            "total_rows": validation_result.get(
                "total_rows",
                0,
            ),
            "imported_rows": imported_count,
            "invalid_rows": validation_result.get(
                "invalid_rows",
                0,
            ),
            "duplicate_rows": validation_result.get(
                "duplicate_rows",
                0,
            ),
            "skipped_rows": (
                validation_result.get(
                    "invalid_rows",
                    0,
                )
                + validation_result.get(
                    "duplicate_rows",
                    0,
                )
            ),
        }

    except Exception as exc:
        db.session.rollback()

        return {
            "success": False,
            "message": f"CSV import failed: {str(exc)}",
        }