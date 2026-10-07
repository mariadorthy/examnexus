"""
Natural-language database query parser.

Feature 19 / Phase 9.

Converts an administrator's natural-language data question into a safe,
closed-vocabulary structured intent + parameters.

CRITICAL SAFETY:
- This module is READ-ONLY by design.
- It does NOT access the database.
- It does NOT emit SQL strings.
- It does NOT accept mutation verbs.
- It does NOT accept SQL fragments.
- It only maps input to one of a small, fixed set of supported intents.

Unknown questions are explicitly rejected — never guessed.
"""

import re
from typing import Any, Dict, List


# =========================================================
# SUPPORTED INTENTS
#
# Each intent is a named, read-only question shape.
# The parser only assigns these — nothing dynamic.
# =========================================================

SUPPORTED_INTENTS = {
    "LIST_EXAMINATIONS": {
        "description": "List examinations (optionally filtered).",
        "params": {"course": "str|null", "status": "str|null"},
    },
    "EXAMINATION_STATUS": {
        "description": "Return the status of a named examination.",
        "params": {"name": "str"},
    },
    "ELIGIBLE_STUDENT_COUNT": {
        "description": "Count eligible students for an examination.",
        "params": {"examination_id": "int|null"},
    },
    "REGISTERED_STUDENT_COUNT": {
        "description": "Count registered students for an examination.",
        "params": {"examination_id": "int|null"},
    },
    "HALLS_BY_STATUS": {
        "description": "List halls filtered by availability status.",
        "params": {"status": "str"},  # available | unavailable | maintenance
    },
    "STUDENTS_IN_HALL": {
        "description": "Count students allocated to a named hall.",
        "params": {"hall": "str"},
    },
    "HALL_ALLOCATION_SUMMARY": {
        "description": "Students assigned per hall (allocation summary).",
        "params": {},
    },
    "UNALLOCATED_STUDENT_COUNT": {
    "description": "Return the number of registered students who are not allocated for an examination.",
    "params": {"examination_id": "int"},
},
    "EXAMINATION_TIMETABLE": {
        "description": "Show the timetable for an examination / course.",
        "params": {"course": "str|null", "examination_id": "int|null"},
    },
    "HALL_CAPACITY": {
    "description": "Return the capacity of a named hall.",
    "params": {"hall": "str"},
},
}


# =========================================================
# MUTATION VERBS — always rejected (READ-ONLY feature)
# =========================================================

MUTATION_PATTERNS = [
    (r"\bdelete\b", "delete"),
    (r"\bdrop\b", "drop"),
    (r"\btruncate\b", "truncate"),
    (r"\binsert\b", "insert"),
    (r"\bupdate\b", "update"),
    (r"\balter\b", "alter"),
    (r"\bcreate\s+(a\s+)?(new\s+)?(student|hall|exam|examination|user|record)\b",
     "create"),
    (r"\bmodify\b", "modify"),
    (r"\bremove\b", "remove"),
    (r"\bclear\b", "clear"),
    (r"\bassign\s+(a\s+)?(student|seat|hall)\b", "assign"),
    (r"\ballocate\s+(a\s+)?(student|seat|hall)\b", "allocate"),
    (r"\bgenerate\s+(allocation|seat|hall)\b", "generate_allocation"),
    (r"\bapprove\b", "approve"),
    (r"\bpublish\b", "publish"),
    (r"\brollback\b", "rollback"),
    (r"\bcommit\b", "commit"),
]


# =========================================================
# SQL-INJECTION STYLE PAYLOADS — always rejected
# =========================================================

SQL_INJECTION_PATTERNS = [
    r";\s*(select|insert|update|delete|drop|alter|truncate)\b",
    r"\bunion\s+select\b",
    r"\bor\s+1\s*=\s*1\b",
    r"\band\s+1\s*=\s*1\b",
    r"--\s",
    r"/\*",
    r"\*/",
    r"\bxp_cmdshell\b",
    r"\bsleep\s*\(",
    r"\bbenchmark\s*\(",
    r"`",
]


# =========================================================
# HALL STATUS INTENT HELPERS
# =========================================================

_HALL_STATUS_KEYWORDS = {
    "maintenance": [
        r"\bunder\s+maintenance\b",
        r"\bmaintenance\s+halls?\b",
        r"\bhalls?\s+(that\s+are\s+)?under\s+maintenance\b",
    ],
    "unavailable": [
        r"\bunavailable\s+halls?\b",
        r"\bhalls?\s+(that\s+are\s+)?unavailable\b",
        r"\bnot\s+available\s+halls?\b",
    ],
    "available": [
        r"\bavailable\s+halls?\b",
        r"\bhalls?\s+(that\s+are\s+)?available\b",
    ],
}


# =========================================================
# INTERNAL HELPERS
# =========================================================

def _normalise(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_mutation(text: str) -> List[str]:
    matched = []
    for pattern, verb in MUTATION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matched.append(verb)
    return matched


def _detect_sql_injection(text: str) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in SQL_INJECTION_PATTERNS
    )


def _extract_course(text: str) -> str | None:
    # "for computer science", "in computer science",
    # "of the computer science course"
    match = re.search(
        r"\b(?:for|in|of)\s+(?:the\s+)?"
        r"([a-z][a-z\s&\-]{2,60}?)"
        r"(?:\s+(?:course|department|stream|programme|program))?\b"
        r"(?=\s+(?:exam|examination|timetable|students?|hall)|[?.!,]|$)",
        text,
    )
    if match:
        return match.group(1).strip()
    return None


def _extract_status_filter(text: str) -> str | None:
    statuses = [
        "draft", "generated", "validated", "review",
        "approved", "published",
    ]
    for status in statuses:
        if re.search(rf"\b{status}\b", text):
            return status.upper()
    return None


def _extract_hall_name(text: str) -> str | None:
    # "Hall H204", "hall H-204", "hall 204"
    match = re.search(
        r"\bhall\s+([a-z]?-?\d{1,4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).lstrip("-").upper()

    # Bare code form: "H204", "h-204"
    match = re.search(r"\b([a-z]\d{2,4})\b", text)
    if match:
        return match.group(1).upper()

    return None

def _extract_examination_name(text):
    patterns = [
        r"(?:status of|status for)\s+(?:the\s+)?(?:examination|exam)\s+(.+?)(?:\?|$)",
        r"(?:what is|what's)\s+(?:the\s+)?status\s+of\s+(?:the\s+)?(?:examination|exam)\s+(.+?)(?:\?|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .?")

    return None

def _extract_examination_id(text: str) -> int | None:
    match = re.search(
    r"\b(?:examination|exam)\s+(?:id\s*)?(\d+)\b",
    text,
    flags=re.IGNORECASE,
)
    if match:
        return int(match.group(1))
    return None


# =========================================================
# INTENT DETECTION
# =========================================================

def _detect_intent(text: str) -> Dict[str, Any]:
    """
    Return {"intent": str|None, "params": dict, "unsupported": bool}.
    No guessing — if nothing matches cleanly, intent is None.
    """

    # --------------------------------------------------
    # Hall allocation summary — must be checked before
    # STUDENTS_IN_HALL to avoid false matches.
    # --------------------------------------------------
    if (
        re.search(r"\bhow\s+many\s+students?\s+(are\s+)?assigned\s+to\s+each\s+hall\b", text)
        or re.search(r"\ballocation\s+summary\b", text)
        or re.search(r"\bhall\s+allocation\s+summary\b", text)
    ):
        return {"intent": "HALL_ALLOCATION_SUMMARY", "params": {}}

    # --------------------------------------------------
    # Unallocated students
    # --------------------------------------------------
    if (
        re.search(r"\bunallocated\s+students?\b", text)
        or re.search(r"\bstudents?\s+not\s+allocated\b", text)
        or re.search(r"\bstudents?\s+without\s+(a\s+)?seat\b", text)
    ):
        examination_id = _extract_examination_id(text)

        if examination_id is None:
            return {
                "intent": None,
                "params": {},
                "unsupported": True,
                "reason": "Examination ID is required for an unallocated student query.",
            }

        return {
            "intent": "UNALLOCATED_STUDENT_COUNT",
            "params": {
                "examination_id": examination_id,
            },
        }

    # --------------------------------------------------
    # Students in a specific hall
    # --------------------------------------------------
    if (
        re.search(r"\bstudents?\s+(?:are\s+)?allocated\s+to\s+hall\b", text)
        or re.search(r"\bhow\s+many\s+students?\s+in\s+hall\b", text)
        or re.search(r"\bstudents?\s+in\s+hall\b", text)
    ):
        hall = _extract_hall_name(text)
        if hall:
            return {
                "intent": "STUDENTS_IN_HALL",
                "params": {"hall": hall},
            }
        return {
            "intent": None,
            "params": {},
            "unsupported": True,
            "reason": "Hall name or code was not specified.",
        }

    # --------------------------------------------------
    # Hall status queries
    # --------------------------------------------------
    for status, patterns in _HALL_STATUS_KEYWORDS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            return {
                "intent": "HALLS_BY_STATUS",
                "params": {"status": status},
            }

    # Hall capacity query
    if re.search(r"\bhall\s+capacit(y|ies)\b", text, re.IGNORECASE) or (
        re.search(r"\bhow\s+many\s+seats\b", text, re.IGNORECASE)
        and re.search(r"\bhall\b", text, re.IGNORECASE)
    ):
        return {
            "intent": "HALL_CAPACITY",
            "params": {
                "hall": _extract_hall_name(text)
            },
        }

    # --------------------------------------------------
    # Exam timetable
    # --------------------------------------------------
    if re.search(r"\btimetable\b", text):
        return {
            "intent": "EXAMINATION_TIMETABLE",
            "params": {
                "course": _extract_course(text),
                "examination_id": _extract_examination_id(text),
            },
        }

    # --------------------------------------------------
    # Eligible students
    # --------------------------------------------------
    if (
        re.search(r"\beligible\s+students?\b", text)
        or re.search(r"\bstudents?\s+eligible\b", text)
    ):
        return {
            "intent": "ELIGIBLE_STUDENT_COUNT",
            "params": {
                "examination_id": _extract_examination_id(text),
            },
        }

    # --------------------------------------------------
    # Registered students
    # --------------------------------------------------
    if (
        re.search(r"\bregistered\s+students?\b", text)
        or re.search(r"\bstudents?\s+registered\b", text)
    ):
        return {
            "intent": "REGISTERED_STUDENT_COUNT",
            "params": {
                "examination_id": _extract_examination_id(text),
            },
        }

    # --------------------------------------------------
    # Examination status
    # --------------------------------------------------
    exam_name = _extract_examination_name(text)

    if re.search(
        r"\b(status|state)\b.*\b(examination|exam)\b",
        text,
        re.IGNORECASE,
    ):
        return {
            "intent": "EXAMINATION_STATUS",
            "params": {
                "name": exam_name
            },
        }
    # --------------------------------------------------
    # Examination list
    # --------------------------------------------------
    if (
        re.search(r"\b(show|list|display)\b.*\bexaminations?\b", text)
        or re.search(r"\ball\s+examinations?\b", text)
        or re.search(r"\bupcoming\s+examinations?\b", text)
    ):
        return {
            "intent": "LIST_EXAMINATIONS",
            "params": {
                "course": _extract_course(text),
                "status": _extract_status_filter(text),
            },
        }

    # Nothing matched — explicit unsupported
    return {
        "intent": None,
        "params": {},
        "unsupported": True,
        "reason": "The question could not be mapped to a supported ExamNexus query.",
    }


# =========================================================
# PUBLIC API
# =========================================================

def parse_query(text: Any) -> Dict[str, Any]:
    """
    Parse a natural-language data question into a safe structured intent.

    Returns:
        {
            "success": bool,
            "input": str,
            "intent": str | None,
            "params": dict,
            "rejected_reason": str | None,
            "validation": {"valid": bool, "errors": [str]},
            "message": str,
        }
    """

    if not isinstance(text, str):
        return {
            "success": False,
            "input": "",
            "intent": None,
            "params": {},
            "rejected_reason": "INVALID_INPUT",
            "validation": {
                "valid": False,
                "errors": ["Question must be a string."],
            },
            "message": "Invalid question input.",
        }

    normalized = _normalise(text)

    if not normalized:
        return {
            "success": False,
            "input": "",
            "intent": None,
            "params": {},
            "rejected_reason": "EMPTY_INPUT",
            "validation": {
                "valid": False,
                "errors": ["Question cannot be empty."],
            },
            "message": "Please provide a question.",
        }

    # Safety: SQL-injection style payloads first
    if _detect_sql_injection(normalized):
        return {
            "success": False,
            "input": text,
            "intent": None,
            "params": {},
            "rejected_reason": "UNSAFE_INPUT",
            "validation": {
                "valid": False,
                "errors": ["Input contains unsafe SQL-like patterns."],
            },
            "message": "This query is not allowed (read-only, safe input only).",
        }

    # Safety: mutation verbs → hard reject (READ-ONLY feature)
    mutations = _detect_mutation(normalized)
    if mutations:
        return {
            "success": False,
            "input": text,
            "intent": None,
            "params": {},
            "rejected_reason": "READ_ONLY_VIOLATION",
            "validation": {
                "valid": False,
                "errors": [
                    "This feature is read-only. "
                    "Mutation commands are not permitted."
                ],
            },
            "message": (
                "This is a read-only query feature. "
                "Data-changing requests are rejected."
            ),
            "detected_mutations": mutations,
        }

    # Intent detection
    detection = _detect_intent(normalized)

    if detection.get("intent") is None:
        return {
            "success": False,
            "input": text,
            "intent": None,
            "params": {},
            "rejected_reason": "UNSUPPORTED_QUERY",
            "validation": {
                "valid": False,
                "errors": [
                    detection.get(
                        "reason",
                        "The question is not supported.",
                    )
                ],
            },
            "message": (
                "Unsupported query. This question does not map to a "
                "supported ExamNexus data query."
            ),
        }

    return {
        "success": True,
        "input": text,
        "intent": detection["intent"],
        "params": detection.get("params", {}),
        "rejected_reason": None,
        "validation": {"valid": True, "errors": []},
        "message": "Query understood.",
    }