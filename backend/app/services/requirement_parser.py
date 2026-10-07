"""
Natural-language examination requirement parser.

Feature 18 / Phase 8 enhancement:
Converts administrator natural-language requirements into a
safe, deterministic structured representation.

IMPORTANT:
- This module does NOT access the database.
- This module does NOT modify examination data.
- This module does NOT allocate halls, seats, or invigilators.
- This module does NOT approve or publish examinations.
- Existing deterministic allocation and validation services remain
  the source of truth.

This is intentionally implemented without an external AI dependency.
It is an NLP-style deterministic requirement-understanding layer.
"""

import re
from typing import Any, Dict, List


SUPPORTED_REQUIREMENTS = {
    "minimize_halls": {
        "type": bool,
        "description": "Prefer using the minimum number of halls.",
    },
    "accessibility_required": {
        "type": bool,
        "description": "Accessibility support is required for students who need it.",
    },
    "exclude_maintenance_halls": {
        "type": bool,
        "description": "Do not use halls that are under maintenance.",
    },
    "exclude_unavailable_halls": {
        "type": bool,
        "description": "Do not use halls that are unavailable.",
    },
    "avoid_timetable_conflicts": {
        "type": bool,
        "description": "Avoid timetable/hall scheduling conflicts.",
    },
}


# These are explicit examples of requirements that ExamNexus does not
# currently support as configurable natural-language requirements.
UNSUPPORTED_PATTERNS = [
    (
        r"\bblue[- ]colou?red\s+seats?\b",
        "Colored seat assignment is not currently supported.",
    ),
    (
        r"\b(red|green|yellow|pink|black|white)[- ]colou?red\s+seats?\b",
        "Colored seat assignment is not currently supported.",
    ),
    (
        r"\bseat\s+colou?r\b",
        "Seat color requirements are not currently supported.",
    ),
    (
        r"\bseat\s+colou?r(s)?\b",
        "Seat color requirements are not currently supported.",
    ),
    (
        r"\bhostel\b",
        "Hostel-based allocation is not currently supported.",
    ),
    (
        r"\bfee\s+(paid|payment|status)\b",
        "Fee-status requirements are not currently configurable through Feature 18.",
    ),
    (
        r"\battendance\b",
        "Attendance-based eligibility is not currently configurable through Feature 18.",
    ),
    (
        r"\bpreference\s+for\s+(a\s+)?specific\s+student\b",
        "Student-specific allocation preferences are not supported.",
    ),
]


def _normalise_text(text: str) -> str:
    """Normalize user input for deterministic matching."""
    text = text.strip().lower()

    # Normalize common punctuation while keeping sentence boundaries useful.
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = re.sub(r"\s+", " ", text)

    return text


def _detect_unsupported(text: str) -> List[Dict[str, str]]:
    """
    Detect explicitly known unsupported requirements.

    The parser never silently converts an unsupported requirement into
    a supported one.
    """
    unsupported = []

    for pattern, reason in UNSUPPORTED_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            phrase = match.group(0).strip()

            item = {
                "requirement": phrase,
                "reason": reason,
            }

            # Avoid duplicate entries when multiple patterns match.
            if item not in unsupported:
                unsupported.append(item)

    return unsupported


def _detect_supported(text: str) -> Dict[str, bool]:
    """
    Detect supported requirements using deterministic keyword/phrase rules.
    """

    requirements = {
        "minimize_halls": False,
        "accessibility_required": False,
        "exclude_maintenance_halls": False,
        "exclude_unavailable_halls": False,
        "avoid_timetable_conflicts": False,
    }

    # ---------------------------------------------------------
    # Minimum number of halls / fewer halls
    # ---------------------------------------------------------
    minimize_patterns = [
        r"\bminimum\s+(number\s+of\s+)?halls?\b",
        r"\bminimize\s+(the\s+)?number\s+of\s+halls?\b",
        r"\bminimise\s+(the\s+)?number\s+of\s+halls?\b",
        r"\bminimum\s+halls?\b",
        r"\bfewer\s+halls?\b",
        r"\bleast\s+(number\s+of\s+)?halls?\b",
        r"\buse\s+(the\s+)?least\s+(number\s+of\s+)?halls?\b",
        r"\bprefer\s+fewer\s+halls?\b",
        r"\bprefer\s+minimum\s+halls?\b",
    ]

    if any(re.search(pattern, text) for pattern in minimize_patterns):
        requirements["minimize_halls"] = True

    # ---------------------------------------------------------
    # Accessibility
    # ---------------------------------------------------------
    accessibility_patterns = [
        r"\baccessib(le|ility)\b",
        r"\baccessibility\s+support\b",
        r"\bstudents?\s+requiring\s+accessibility\s+support\b",
        r"\bstudents?\s+requiring\s+accessible\s+halls?\b",
        r"\bspecial\s+accessibility\s+needs?\b",
        r"\baccessible\s+halls?\b",
    ]

    if any(re.search(pattern, text) for pattern in accessibility_patterns):
        requirements["accessibility_required"] = True

    # ---------------------------------------------------------
    # Maintenance halls
    # ---------------------------------------------------------
    maintenance_patterns = [
        r"\bhalls?\s+under\s+maintenance\b",
        r"\bmaintenance\s+halls?\b",
        r"\bexclude\s+maintenance\b",
        r"\bavoid\s+maintenance\s+halls?\b",
        r"\bdo\s+not\s+use\s+maintenance\s+halls?\b",
        r"\bdon'?t\s+use\s+maintenance\s+halls?\b",
    ]

    if any(re.search(pattern, text) for pattern in maintenance_patterns):
        requirements["exclude_maintenance_halls"] = True

    # ---------------------------------------------------------
    # Unavailable halls
    # ---------------------------------------------------------
    unavailable_patterns = [
        r"\bunavailable\s+halls?\b",
        r"\bhalls?\s+that\s+are\s+unavailable\b",
        r"\bexclude\s+unavailable\s+halls?\b",
        r"\bavoid\s+unavailable\s+halls?\b",
        r"\bdo\s+not\s+use\s+unavailable\s+halls?\b",
        r"\bdon'?t\s+use\s+unavailable\s+halls?\b",
    ]

    if any(re.search(pattern, text) for pattern in unavailable_patterns):
        requirements["exclude_unavailable_halls"] = True

    # ---------------------------------------------------------
    # Timetable conflicts
    # ---------------------------------------------------------
    timetable_patterns = [
        r"\btimetable\s+conflicts?\b",
        r"\btimetable\s+overlaps?\b",
        r"\btime\s+conflicts?\b",
        r"\bscheduling\s+conflicts?\b",
        r"\bavoid\s+(hall\s+)?conflicts?\b",
        r"\bavoid\s+overlapping\s+hall\b",
        r"\bno\s+timetable\s+conflicts?\b",
        r"\bno\s+overlapping\s+exams?\b",
    ]

    if any(re.search(pattern, text) for pattern in timetable_patterns):
        requirements["avoid_timetable_conflicts"] = True

    return requirements


def _find_unrecognized_requirement(text: str, supported: Dict[str, bool]) -> List[Dict[str, str]]:
    """
    Identify input that contains no recognized requirement.

    We intentionally do not attempt to guess what an unknown instruction means.
    """
    if any(supported.values()):
        return []

    if not text:
        return []

    return [
        {
            "requirement": text,
            "reason": (
                "The requirement could not be mapped to a supported "
                "ExamNexus requirement."
            ),
        }
    ]


def validate_structured_requirements(requirements: Any) -> Dict[str, Any]:
    """
    Validate structured parser output.

    This validation is deliberately independent from parsing so that
    route-level/API validation can reject malformed structured data.
    """

    if not isinstance(requirements, dict):
        return {
            "valid": False,
            "errors": ["Structured requirements must be an object."],
        }

    errors = []

    unknown_keys = set(requirements.keys()) - set(SUPPORTED_REQUIREMENTS.keys())

    if unknown_keys:
        errors.append(
            "Unsupported structured requirement keys: "
            + ", ".join(sorted(unknown_keys))
        )

    for key, value in requirements.items():
        if key not in SUPPORTED_REQUIREMENTS:
            continue

        expected_type = SUPPORTED_REQUIREMENTS[key]["type"]

        # bool is a subclass of int in Python, so type(...) is intentional.
        if type(value) is not expected_type:
            errors.append(
                f"Requirement '{key}' must be of type "
                f"{expected_type.__name__}."
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def parse_requirements(text: str) -> Dict[str, Any]:
    """
    Parse a natural-language requirement into a safe structured response.

    Returns:
        {
            "success": bool,
            "input": str,
            "requirements": {...},
            "unsupported_requirements": [...],
            "validation": {...},
            "message": str
        }
    """

    if not isinstance(text, str):
        return {
            "success": False,
            "input": "",
            "requirements": {},
            "unsupported_requirements": [],
            "validation": {
                "valid": False,
                "errors": ["Requirement input must be a string."],
            },
            "message": "Invalid requirement input.",
        }

    normalized_text = _normalise_text(text)

    if not normalized_text:
        return {
            "success": False,
            "input": "",
            "requirements": {},
            "unsupported_requirements": [],
            "validation": {
                "valid": False,
                "errors": ["Requirement input cannot be empty."],
            },
            "message": "Please provide a natural-language requirement.",
        }

    requirements = _detect_supported(normalized_text)

    unsupported = _detect_unsupported(normalized_text)

    # If nothing supported was recognized, explicitly report the
    # entire requirement as unsupported instead of guessing.
    if not any(requirements.values()) and not unsupported:
        unsupported.extend(
            _find_unrecognized_requirement(
                normalized_text,
                requirements,
            )
        )

    validation = validate_structured_requirements(requirements)

    success = validation["valid"] and (
        any(requirements.values()) or bool(unsupported)
    )

    recognized_names = [
        key
        for key, value in requirements.items()
        if value
    ]

    if recognized_names and unsupported:
        message = (
            "Requirements understood successfully, with some "
            "unsupported requirements identified."
        )
    elif recognized_names:
        message = "Requirements understood successfully."
    else:
        message = "No supported requirement was identified."

    return {
        "success": success,
        "input": text,
        "requirements": requirements,
        "unsupported_requirements": unsupported,
        "recognized_requirements": recognized_names,
        "validation": validation,
        "message": message,
    }