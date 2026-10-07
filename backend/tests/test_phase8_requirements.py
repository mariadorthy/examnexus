"""
Phase 8 — Natural-Language Requirement Understanding tests.

This test file covers the P1 Feature 18 requirement-understanding layer.

The parser must:
- understand supported requirements
- understand multiple requirements
- explicitly report unsupported requirements
- reject empty/invalid input
- produce deterministic output
- validate structured requirements
- never directly modify protected allocation data
- require admin RBAC at the API layer
"""

from app.services.requirement_parser import (
    parse_requirements,
    validate_structured_requirements,
)


# ============================================================
# Parser — Basic Understanding
# ============================================================

def test_understands_minimum_halls():
    result = parse_requirements(
        "Use the minimum number of halls."
    )

    assert result["success"] is True
    assert result["requirements"]["minimize_halls"] is True


def test_understands_accessibility_requirement():
    result = parse_requirements(
        "Keep students requiring accessibility support in accessible halls."
    )

    assert result["success"] is True
    assert result["requirements"]["accessibility_required"] is True


def test_understands_maintenance_exclusion():
    result = parse_requirements(
        "Avoid halls under maintenance."
    )

    assert result["success"] is True
    assert result["requirements"]["exclude_maintenance_halls"] is True


def test_understands_unavailable_hall_exclusion():
    result = parse_requirements(
        "Do not use unavailable halls."
    )

    assert result["success"] is True
    assert result["requirements"]["exclude_unavailable_halls"] is True


def test_understands_timetable_conflict_requirement():
    result = parse_requirements(
        "Avoid timetable conflicts."
    )

    assert result["success"] is True
    assert result["requirements"]["avoid_timetable_conflicts"] is True


# ============================================================
# Parser — Multiple Requirements
# ============================================================

def test_understands_multiple_requirements():
    result = parse_requirements(
        "Use the minimum number of halls, keep students requiring "
        "accessibility support in accessible halls, and avoid halls "
        "under maintenance."
    )

    assert result["success"] is True

    requirements = result["requirements"]

    assert requirements["minimize_halls"] is True
    assert requirements["accessibility_required"] is True
    assert requirements["exclude_maintenance_halls"] is True

    assert requirements["exclude_unavailable_halls"] is False
    assert requirements["avoid_timetable_conflicts"] is False


def test_understands_all_supported_requirements_together():
    result = parse_requirements(
        "Use fewer halls, use accessible halls for accessibility support, "
        "exclude maintenance halls, exclude unavailable halls, "
        "and avoid timetable conflicts."
    )

    assert result["success"] is True

    requirements = result["requirements"]

    assert requirements["minimize_halls"] is True
    assert requirements["accessibility_required"] is True
    assert requirements["exclude_maintenance_halls"] is True
    assert requirements["exclude_unavailable_halls"] is True
    assert requirements["avoid_timetable_conflicts"] is True


# ============================================================
# Unsupported Requirements
# ============================================================

def test_explicitly_reports_unsupported_seat_color_requirement():
    result = parse_requirements(
        "Use accessible halls and give students blue-colored seats."
    )

    assert result["success"] is True

    assert result["requirements"]["accessibility_required"] is True

    unsupported = result["unsupported_requirements"]

    assert len(unsupported) >= 1

    assert any(
        "color" in item["reason"].lower()
        or "colour" in item["reason"].lower()
        for item in unsupported
    )


def test_unknown_requirement_is_not_guessed():
    result = parse_requirements(
        "Arrange students according to their favorite food."
    )

    assert result["success"] is True
    assert result["requirements"]["minimize_halls"] is False
    assert result["requirements"]["accessibility_required"] is False
    assert result["requirements"]["exclude_maintenance_halls"] is False

    assert len(result["unsupported_requirements"]) >= 1


def test_mixed_supported_and_unsupported_requirements():
    result = parse_requirements(
        "Use minimum halls and give students blue-colored seats."
    )

    assert result["success"] is True

    assert result["requirements"]["minimize_halls"] is True

    assert len(result["unsupported_requirements"]) >= 1


# ============================================================
# Invalid / Empty Input
# ============================================================

def test_empty_requirement_is_rejected():
    result = parse_requirements("")

    assert result["success"] is False
    assert result["validation"]["valid"] is False


def test_whitespace_requirement_is_rejected():
    result = parse_requirements("     ")

    assert result["success"] is False
    assert result["validation"]["valid"] is False


def test_non_string_requirement_is_rejected():
    result = parse_requirements(None)

    assert result["success"] is False
    assert result["validation"]["valid"] is False


def test_numeric_requirement_is_rejected():
    result = parse_requirements(12345)

    assert result["success"] is False
    assert result["validation"]["valid"] is False


# ============================================================
# Structured Output Validation
# ============================================================

def test_valid_structured_requirements():
    result = validate_structured_requirements({
        "minimize_halls": True,
        "accessibility_required": True,
        "exclude_maintenance_halls": False,
        "exclude_unavailable_halls": True,
        "avoid_timetable_conflicts": False,
    })

    assert result["valid"] is True
    assert result["errors"] == []


def test_unknown_structured_requirement_is_rejected():
    result = validate_structured_requirements({
        "minimize_halls": True,
        "assign_blue_seats": True,
    })

    assert result["valid"] is False
    assert len(result["errors"]) >= 1


def test_wrong_structured_requirement_type_is_rejected():
    result = validate_structured_requirements({
        "minimize_halls": "yes",
    })

    assert result["valid"] is False
    assert len(result["errors"]) >= 1


def test_structured_requirements_must_be_object():
    result = validate_structured_requirements(
        ["minimize_halls"]
    )

    assert result["valid"] is False
    assert len(result["errors"]) >= 1


# ============================================================
# Determinism
# ============================================================

def test_parser_is_deterministic():
    text = (
        "Use the minimum number of halls, keep students requiring "
        "accessibility support in accessible halls, and avoid halls "
        "under maintenance."
    )

    first = parse_requirements(text)
    second = parse_requirements(text)

    assert first == second


def test_case_does_not_change_result():
    first = parse_requirements(
        "Use Minimum Halls and Accessible Halls."
    )

    second = parse_requirements(
        "use minimum halls and accessible halls."
    )

    assert first["requirements"] == second["requirements"]


# ============================================================
# Safety — Parser Has No Allocation Authority
# ============================================================

def test_parser_only_returns_structured_requirements():
    result = parse_requirements(
        "Assign all students to Hall 1 and approve the examination."
    )

    assert "requirements" in result
    assert "unsupported_requirements" in result

    # The parser must not expose an instruction that performs allocation
    # or approval.
    requirements = result["requirements"]

    assert "assign_students" not in requirements
    assert "assign_hall" not in requirements
    assert "approve_exam" not in requirements
    assert "publish_exam" not in requirements


# ============================================================
# API Tests
# ============================================================

def test_requirement_api_requires_admin(client):
    response = client.post(
        "/api/requirements/understand",
        json={
            "requirement": "Use minimum halls."
        },
    )

    # Existing authentication/RBAC middleware should reject
    # unauthenticated access.
    assert response.status_code in (401, 403)


def test_requirement_api_rejects_invalid_body(client, admin_token):
    response = client.post(
        "/api/requirements/understand",
        json={
            "requirement": 12345
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 400


def test_requirement_api_accepts_admin_requirement(client, admin_token):
    response = client.post(
        "/api/requirements/understand",
        json={
            "requirement": (
                "Use the minimum number of halls and "
                "keep accessibility students in accessible halls."
            )
        },
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["requirements"]["minimize_halls"] is True
    assert data["requirements"]["accessibility_required"] is True