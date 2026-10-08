"""
Feature 18 → Allocation integration.

Converts validated structured requirements (produced by
services/requirement_parser.py) into an explicit, typed
allocator options dict.

Hard rules:
  - Closed schema. Unknown keys are rejected.
  - Only bool values accepted.
  - Options may only STRENGTHEN safety constraints, never
    weaken them. The allocator already enforces all five
    constraints unconditionally; these options exist as a
    documented contract and as a forward-compatible hook.
  - No database access. No side effects.
"""

from app.services.requirement_parser import (
    SUPPORTED_REQUIREMENTS,
    validate_structured_requirements,
)


# The exact keys an allocator call accepts. Closed set.
ALLOCATION_OPTION_KEYS = frozenset({
    "minimize_halls",
    "accessibility_required",
    "exclude_maintenance_halls",
    "exclude_unavailable_halls",
    "avoid_timetable_conflicts",
})


def build_allocation_options(structured_requirements):
    """
    Convert a validated structured-requirements dict into a
    typed allocation options dict.

    Returns:
        {
            "success": bool,
            "options": {...},   # only when success
            "errors": [...],
        }
    """

    if structured_requirements is None:
        return {
            "success": True,
            "options": {},
            "errors": [],
        }

    validation = validate_structured_requirements(
        structured_requirements
    )
    if not validation["valid"]:
        return {
            "success": False,
            "options": {},
            "errors": validation["errors"],
        }

    options = {}
    for key in ALLOCATION_OPTION_KEYS:
        if key not in structured_requirements:
            continue
        value = structured_requirements[key]
        if not isinstance(value, bool):
            return {
                "success": False,
                "options": {},
                "errors": [
                    f"Allocation option '{key}' must be boolean."
                ],
            }
        options[key] = value

    # Reject any key that isn't in the closed set.
    extra = set(structured_requirements.keys()) - ALLOCATION_OPTION_KEYS
    if extra:
        return {
            "success": False,
            "options": {},
            "errors": [
                "Unsupported allocation option key(s): "
                + ", ".join(sorted(extra))
            ],
        }

    return {
        "success": True,
        "options": options,
        "errors": [],
    }


def describe_options(options):
    """
    Human-readable list of applied options, for the response
    payload and for the audit trail.
    """
    labels = {
        "minimize_halls": "Minimize number of halls",
        "accessibility_required": "Accessibility requirement",
        "exclude_maintenance_halls":
            "Exclude halls under maintenance",
        "exclude_unavailable_halls":
            "Exclude unavailable halls",
        "avoid_timetable_conflicts":
            "Avoid timetable conflicts",
    }
    return [
        labels[key]
        for key, value in sorted(options.items())
        if value
    ]