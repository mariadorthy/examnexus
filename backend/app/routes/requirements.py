"""
Natural-language requirement understanding API.

Feature 18 / Phase 8 enhancement.

Only authenticated administrators can use this endpoint.

The endpoint:
1. Accepts natural-language requirements.
2. Sends them to the deterministic parser.
3. Validates the structured output.
4. Returns recognized and unsupported requirements.

It does NOT:
- modify the database
- create/update examinations
- allocate halls
- allocate seats
- allocate invigilators
- approve examinations
- publish examinations
"""

from flask import Blueprint, jsonify, request

from app.auth.decorators import roles_required
from app.services.requirement_parser import parse_requirements


requirements_bp = Blueprint(
    "requirements",
    __name__,
    url_prefix="/api/requirements",
)


@requirements_bp.route("/understand", methods=["POST"])
@roles_required("admin")
def understand_requirements():
    """
    Understand an administrator's natural-language requirements.

    Expected JSON:
    {
        "requirement": "Use minimum halls and keep accessibility students in accessible halls."
    }
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    requirement = data.get("requirement")

    if not isinstance(requirement, str):
        return jsonify({
            "success": False,
            "message": "The 'requirement' field must be a string.",
        }), 400

    result = parse_requirements(requirement)

    if not result["validation"]["valid"]:
        return jsonify(result), 400

    return jsonify(result), 200


@requirements_bp.route(
    "/apply/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def apply_requirements_to_allocation(examination_id):
    """
    Feature 18 → Allocation integration.

    Accepts either:
      { "requirement": "Use the minimum number of halls..." }
    or:
      { "requirements": { "minimize_halls": true, ... } }

    Dry-run by default. Only when the client sends
    {"confirm": true} together with a validated request is
    the allocator allowed to write.

    The natural-language layer never touches the DB directly;
    the deterministic allocation service remains authoritative.
    """
    from app.services.allocation_options import (
        build_allocation_options,
        describe_options,
    )
    from app.services.allocation import (
        generate_allocation,
        plan_allocation,
    )
    from app.services.validation import (
        validate_allocation,
        validate_proposed_plan,
    )
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )
    from app.models.examination import Examination
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    # ---------------------------------------------------------
    # LIFECYCLE GATE
    #
    # The deterministic allocator does not consult lifecycle
    # state on its own. This route must, because regenerating
    # from a validated / approved snapshot would silently
    # discard it, and regenerating a PUBLISHED examination
    # would bypass the existing emergency reallocation
    # workflow.
    #
    # Allowed:   DRAFT, GENERATED
    # Refused:   VALIDATED, REVIEW, APPROVED, PUBLISHED
    # ---------------------------------------------------------

    examination = Examination.query.get(examination_id)

    if not examination:
        return jsonify({
            "success": False,
            "message": "Examination not found",
        }), 404

    current_status = (examination.status or "DRAFT").upper()

    if current_status == "PUBLISHED":
        return jsonify({
            "success": False,
            "message": (
                "This examination is PUBLISHED. Allocation changes "
                "for a published examination must go through the "
                "existing emergency reallocation workflow, which "
                "requires a recorded hall incident and its own "
                "authorization and approval steps."
            ),
            "status": current_status,
        }), 409

    if current_status in {"VALIDATED", "REVIEW", "APPROVED"}:
        return jsonify({
            "success": False,
            "message": (
                f"Allocation cannot be regenerated while the "
                f"examination is in status {current_status}. "
                f"Reverting the lifecycle is not supported; "
                f"start a fresh examination cycle instead."
            ),
            "status": current_status,
        }), 409

    confirm = bool(data.get("confirm", False))

    # ---------------------------------------------------------
    # 1. OBTAIN STRUCTURED REQUIREMENTS
    # ---------------------------------------------------------

    structured = None


    if "requirement" in data:
        raw = data.get("requirement")
        if not isinstance(raw, str):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirement' field must be a string."
                ),
            }), 400

        parsed = parse_requirements(raw)
        if not parsed["validation"]["valid"]:
            return jsonify(parsed), 400

        # ---------------------------------------------------------
        # HARD-REFUSE GATE
        #
        # Lifecycle instructions (validate / review / approve /
        # publish) belong to the administrator in the Review &
        # Approve tab. They are refused outright for both preview
        # and apply.
        # ---------------------------------------------------------
        blocking = parsed.get("blocking_requirements") or []
        if blocking:
            return jsonify({
                "success": False,
                "message": (
                    "The requirement contains administrator-only "
                    "lifecycle instructions. Use the Review & "
                    "Approve tab for these actions."
                ),
                "blocking_requirements": blocking,
                "examination_id": examination_id,
            }), 400

        structured = parsed["requirements"]
        parsed_payload = parsed

    elif "requirements" in data:
        structured = data.get("requirements")
        if not isinstance(structured, dict):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirements' field must be an object."
                ),
            }), 400
        parsed_payload = None

    else:
        return jsonify({
            "success": False,
            "message": (
                "Provide either 'requirement' (natural language) "
                "or 'requirements' (structured object)."
            ),
        }), 400

    # ---------------------------------------------------------
    # 2. CONVERT TO TYPED ALLOCATION OPTIONS
    # ---------------------------------------------------------

    options_result = build_allocation_options(structured)

    if not options_result["success"]:
        return jsonify({
            "success": False,
            "message": "Invalid structured requirements.",
            "errors": options_result["errors"],
        }), 400

    options = options_result["options"]

    # ---------------------------------------------------------
    # READINESS GATE
    #
    # Reuse the existing readiness helpers; do not invent a
    # second readiness engine. This mirrors the computation
    # performed by routes/readiness.py.
    # ---------------------------------------------------------

    from app.services.eligibility import get_eligible_students
    from app.services.hall_availability import get_hall_readiness
    from app.services.allocation import get_available_halls
    from app.models.timetable import Timetable

    timetable_entries = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
            Timetable.id,
        )
        .all()
    )

    eligible_students = get_eligible_students(examination_id)
    eligible_count = len(eligible_students)

    hall_readiness = get_hall_readiness()

    per_timetable = []
    per_timetable_all_sufficient = True
    worst_shortage = 0

    for entry in timetable_entries:
        usable_halls = get_available_halls(entry)
        entry_capacity = sum(
            hall.examination_capacity for hall in usable_halls
        )
        entry_sufficient = entry_capacity >= eligible_count
        entry_shortage = max(0, eligible_count - entry_capacity)

        if not entry_sufficient:
            per_timetable_all_sufficient = False

        if entry_shortage > worst_shortage:
            worst_shortage = entry_shortage

        per_timetable.append({
            "timetable_id": entry.id,
            "exam_date": entry.exam_date.isoformat(),
            "session": entry.session,
            "required_capacity": eligible_count,
            "available_capacity": entry_capacity,
            "available_hall_count": len(usable_halls),
            "sufficient": entry_sufficient,
            "shortage": entry_shortage,
        })

    global_sufficient = (
        hall_readiness["total_available_capacity"] >= eligible_count
    )

    if timetable_entries:
        capacity_sufficient = per_timetable_all_sufficient
    else:
        capacity_sufficient = global_sufficient

    ready_for_allocation = (
        bool(timetable_entries)
        and eligible_count > 0
        and capacity_sufficient
    )

    readiness_payload = {
        "ready_for_allocation": ready_for_allocation,
        "student_eligibility": {
            "eligible_student_count": eligible_count,
        },
        "hall_readiness": {
            "available_hall_count": hall_readiness["available_hall_count"],
            "total_available_capacity":
                hall_readiness["total_available_capacity"],
            "accessible_hall_count":
                hall_readiness["accessible_hall_count"],
            "accessible_capacity": hall_readiness["accessible_capacity"],
        },
        "capacity_check": {
            "required_capacity": eligible_count,
            "sufficient": capacity_sufficient,
            "shortage": (
                worst_shortage
                if timetable_entries
                else max(0, eligible_count -
                         hall_readiness["total_available_capacity"])
            ),
            "global": {
                "required_capacity": eligible_count,
                "available_capacity":
                    hall_readiness["total_available_capacity"],
                "sufficient": global_sufficient,
                "shortage": max(
                    0,
                    eligible_count -
                    hall_readiness["total_available_capacity"],
                ),
            },
            "per_timetable": per_timetable,
        },
        "timetable_entry_count": len(timetable_entries),
    }

    if not ready_for_allocation:
        return jsonify({
            "success": False,
            "message": (
                "Examination is not ready for allocation. "
                "Resolve the blockers listed in 'readiness' and try again."
            ),
            "examination_id": examination_id,
            "status": current_status,
            "parsed": parsed_payload,
            "allocation_options": options,
            "readiness": readiness_payload,
        }), 400

    # Refuse to regenerate the whole allocation when the
    # requirement parsed to nothing supported. This prevents
    # a no-op or a fully-unsupported input from silently
    # replacing an existing allocation.
    if not any(options.values()):
        return jsonify({
            "success": False,
            "message": (
                "No supported requirements were identified. "
                "Nothing to apply."
            ),
            "parsed": parsed_payload,
            "allocation_options": options,
        }), 400
    # ---------------------------------------------------------
    # 3. DRY RUN (no writes)
    #
    # Uses the pure planner directly. Nothing is added to
    # db.session and nothing is committed. The proposal is
    # validated by the existing pure proposed-plan validator.
    # ---------------------------------------------------------

    if not confirm:

        plan_result = plan_allocation(
            examination_id,
            allocation_options=options,
        )

        if not plan_result.get("success"):
            # The planner itself rejected the plan (no eligible
            # students, insufficient capacity, insufficient
            # accessible capacity, no usable halls, etc.).
            # This is not a server error — it is an honest
            # "cannot propose" result.
            return jsonify({
                "success": False,
                "mode": "preview",
                "examination_id": examination_id,
                "parsed": parsed_payload,
                "allocation_options": options,
                "applied_options": describe_options(options),
                "readiness": readiness_payload,
                "message": plan_result.get(
                    "message",
                    "Unable to propose an allocation.",
                ),
                "planner": plan_result,
            }), 400

        proposed_allocations = [
            {
                "timetable_id": hall_allocation.timetable_id,
                "hall_id": hall_allocation.hall_id,
                "allocated_capacity":
                    hall_allocation.allocated_capacity,
                "purpose": hall_allocation.purpose,
            }
            for hall_allocation in plan_result["allocations"]
        ]

        proposed_validation = validate_proposed_plan(
            examination_id,
            proposed_allocations,
            eligible_students=plan_result.get("total_students"),
            accessibility_students=len(
                plan_result.get("accessibility_students") or []
            ),
        )

        proposed_capacity = sum(
            row["allocated_capacity"]
            for row in proposed_allocations
        )

        proposed_hall_ids = {
            row["hall_id"] for row in proposed_allocations
        }

        return jsonify({
            "success": True,
            "mode": "preview",
            "examination_id": examination_id,
            "examination": {
                "id": examination.id,
                "name": examination.name,
                "status": examination.status,
                "updated_at": (
                    examination.updated_at.isoformat()
                    if examination.updated_at
                    else None
                ),
            },
            "parsed": parsed_payload,
            "allocation_options": options,
            "applied_options": describe_options(options),
            "proposed_allocations": proposed_allocations,
            "proposed_counts": {
                "students": plan_result.get("total_students", 0),
                "halls": len(proposed_hall_ids),
                "allocated_capacity": proposed_capacity,
                "accessibility_students": len(
                    plan_result.get("accessibility_students") or []
                ),
            },
            "validation": proposed_validation,
            "readiness": readiness_payload,
            "message": (
                "Preview only. This proposal has NOT been applied. "
                "Send confirm=true together with the echoed "
                "'expected_updated_at' to apply it."
            ),
        }), 200
    # ---------------------------------------------------------
    # 4. APPLY (deterministic allocator performs the write)
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # 4a. UNSUPPORTED-REQUIREMENT GATE
    #
    # If any unsupported requirement was detected at parse time,
    # refuse unless the client has explicitly acknowledged it.
    # This prevents a mixed prompt from silently applying only
    # its supported subset.
    # ---------------------------------------------------------

    unsupported = []

    if parsed_payload is not None:
        unsupported = parsed_payload.get(
            "unsupported_requirements", []
        ) or []

    acknowledge_unsupported = bool(
        data.get("acknowledge_unsupported", False)
    )

    if unsupported and not acknowledge_unsupported:
        return jsonify({
            "success": False,
            "message": (
                "The request contains unsupported requirements. "
                "Resubmit with acknowledge_unsupported=true to "
                "proceed with only the supported requirements, or "
                "rewrite the request."
            ),
            "unsupported_requirements": unsupported,
            "examination_id": examination_id,
        }), 400
    # ---------------------------------------------------------
    # 4b. STALE-PROPOSAL GATE
    #
    # If the client sends expected_updated_at (as the Feature 18
    # proposal UI does), we compare it to the examination's
    # current updated_at and refuse on mismatch.
    #
    # If the client omits it (existing direct API callers, and
    # the pre-existing phase-12 integration tests), we do NOT
    # refuse. Omitting the field is treated as "apply against
    # whatever the examination state is right now", which is
    # the exact behavior this route had before Issue 5. The
    # stricter echo-based guard is an opt-in safety net for
    # callers that preview first.
    #
    # This is deliberately backward-compatible: we do not
    # weaken any guard that previously existed, and we do not
    # force every caller to adopt the new preview workflow.
    # ---------------------------------------------------------

    expected_updated_at = data.get("expected_updated_at")

    current_updated_at = (
        examination.updated_at.isoformat()
        if examination.updated_at
        else None
    )

    if expected_updated_at is not None:
        # Caller opted into the strict path. Require the value
        # to be a real, non-empty string.
        if (
            not isinstance(expected_updated_at, str)
            or not expected_updated_at
        ):
            return jsonify({
                "success": False,
                "message": (
                    "expected_updated_at must be a non-empty "
                    "ISO-8601 string when provided. Omit it "
                    "entirely to skip the stale-proposal check."
                ),
            }), 400

        if current_updated_at != expected_updated_at:
            return jsonify({
                "success": False,
                "message": (
                    "The examination changed since the preview "
                    "was generated. Please re-run the preview."
                ),
                "expected_updated_at": expected_updated_at,
                "current_updated_at": current_updated_at,
                "parsed": parsed_payload,
                "unsupported_requirements": unsupported,
            }), 409
    # ---------------------------------------------------------
    # 4c. APPLY — HALL + SEAT
    # ---------------------------------------------------------

    result = generate_allocation(
        examination_id,
        force=True,
        allocation_options=options,
    )

    if not result.get("success"):
        return jsonify(result), 400

    validation = validate_allocation(examination_id)

    # ---------------------------------------------------------
    # 4d. APPLY — INVIGILATORS (only if the prompt asked)
    #
    # generate_allocation does not touch invigilators. When the
    # interpreted options request them, call the existing
    # deterministic invigilator allocator in a separate
    # transaction. If it fails, hall + seat remain applied
    # (already committed) and we report the partial outcome
    # honestly. This is option D4a.
    # ---------------------------------------------------------

    invigilator_result = None
    invigilator_validation = None
    partial_failure = None

    if options.get("generate_invigilators"):

        invigilator_result = generate_invigilator_allocation(
            examination_id,
            force=True,
        )

        if not invigilator_result.get("success"):
            partial_failure = {
                "stage": "invigilators",
                "message": invigilator_result.get(
                    "message",
                    "Invigilator generation failed.",
                ),
                "detail": invigilator_result,
            }
        else:
            from app.services.validation import (
                validate_invigilator_allocation,
            )
            invigilator_validation = (
                validate_invigilator_allocation(examination_id)
            )

    response_body = {
        "success": True,
        "mode": "applied",
        "examination_id": examination_id,
        "examination": {
            "id": examination.id,
            "name": examination.name,
            "status": examination.status,
            "updated_at": (
                examination.updated_at.isoformat()
                if examination.updated_at
                else None
            ),
        },
        "allocation_options": options,
        "applied_options": describe_options(options),
        "allocation": result,
        "validation": validation,
        "invigilator_allocation": invigilator_result,
        "invigilator_validation": invigilator_validation,
        "partial_failure": partial_failure,
    }

    if validation.get("status") != "VALID":
        response_body["message"] = (
            "Allocation was applied, but post-apply validation "
            "reported a problem. Review it in the "
            "Review & Approve tab before continuing."
        )
    elif partial_failure:
        response_body["message"] = (
            "Hall and seat allocation applied. Invigilator "
            "generation failed — see partial_failure. You can "
            "retry from the Invigilator Allocation tab."
        )
    else:
        response_body["message"] = (
            "Allocation applied successfully."
        )

    return jsonify(response_body), 200

@requirements_bp.route(
    "/apply-bulk",
    methods=["POST"],
)
@roles_required("admin")
def apply_requirements_to_allocation_bulk():
    """
    Feature 18 -> allocation workflow, bulk variant (Issue 5).

    Accepts:
      {
        "examination_ids": [1, 2, 3],
        "requirement": "...",          # or "requirements": {...}
        "confirm": false,
        "acknowledge_unsupported": false,
        "expected_updated_at_map": { "1": "iso", "2": "iso" }
      }

    Preview (confirm false): returns a per-examination preview.
    Apply (confirm true): applies per examination. Never aborts
    the whole batch because one examination fails; the caller
    inspects each row's status.

    Lifecycle instructions (validate / review / approve / publish)
    refuse the whole request with 400 — these are the
    administrator's actions in the Review & Approve tab.
    """

    from app.services.allocation_options import (
        build_allocation_options,
        describe_options,
    )
    from app.services.allocation import (
        generate_allocation,
        plan_allocation,
    )
    from app.services.validation import (
        validate_allocation,
        validate_proposed_plan,
        validate_invigilator_allocation,
    )
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )
    from app.services.eligibility import get_eligible_students
    from app.services.hall_availability import get_hall_readiness
    from app.services.allocation import get_available_halls
    from app.models.examination import Examination
    from app.models.timetable import Timetable

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
        }), 400

    raw_ids = data.get("examination_ids")

    if not isinstance(raw_ids, list) or not raw_ids:
        return jsonify({
            "success": False,
            "message": (
                "examination_ids must be a non-empty list."
            ),
        }), 400

    examination_ids = []
    for raw_id in raw_ids:
        if str(raw_id).isdigit():
            candidate = int(raw_id)
            if candidate > 0:
                examination_ids.append(candidate)

    if not examination_ids:
        return jsonify({
            "success": False,
            "message": (
                "examination_ids must contain at least one "
                "positive integer."
            ),
        }), 400

    confirm = bool(data.get("confirm", False))
    acknowledge_unsupported = bool(
        data.get("acknowledge_unsupported", False)
    )
    expected_updated_at_map = data.get(
        "expected_updated_at_map", {}
    ) or {}

    # ---------------------------------------------------------
    # Obtain structured requirements (once, shared across exams)
    # ---------------------------------------------------------

    structured = None
    parsed_payload = None

    if "requirement" in data:
        raw = data.get("requirement")
        if not isinstance(raw, str):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirement' field must be a string."
                ),
            }), 400

        parsed = parse_requirements(raw)

        if not parsed["validation"]["valid"]:
            return jsonify(parsed), 400

        blocking = parsed.get("blocking_requirements") or []
        if blocking:
            return jsonify({
                "success": False,
                "message": (
                    "The requirement contains administrator-only "
                    "lifecycle instructions. Use the Review & "
                    "Approve tab for these actions."
                ),
                "blocking_requirements": blocking,
            }), 400

        structured = parsed["requirements"]
        parsed_payload = parsed

    elif "requirements" in data:
        structured = data.get("requirements")
        if not isinstance(structured, dict):
            return jsonify({
                "success": False,
                "message": (
                    "The 'requirements' field must be an object."
                ),
            }), 400
    else:
        return jsonify({
            "success": False,
            "message": (
                "Provide either 'requirement' or 'requirements'."
            ),
        }), 400

    options_result = build_allocation_options(structured)
    if not options_result["success"]:
        return jsonify({
            "success": False,
            "message": "Invalid structured requirements.",
            "errors": options_result["errors"],
        }), 400

    options = options_result["options"]

    if not any(options.values()):
        return jsonify({
            "success": False,
            "message": (
                "No supported requirements were identified. "
                "Nothing to apply."
            ),
            "parsed": parsed_payload,
            "allocation_options": options,
        }), 400

    # ---------------------------------------------------------
    # Unsupported gate (soft)
    # ---------------------------------------------------------

    unsupported = []
    if parsed_payload is not None:
        unsupported = (
            parsed_payload.get("unsupported_requirements") or []
        )

    if confirm and unsupported and not acknowledge_unsupported:
        return jsonify({
            "success": False,
            "message": (
                "The request contains unsupported requirements. "
                "Resubmit with acknowledge_unsupported=true to "
                "proceed with only the supported requirements."
            ),
            "unsupported_requirements": unsupported,
        }), 400

    # ---------------------------------------------------------
    # Loop per examination
    # ---------------------------------------------------------

    results = []

    for examination_id in examination_ids:

        examination = Examination.query.get(examination_id)

        if not examination:
            results.append({
                "examination_id": examination_id,
                "status": "NOT FOUND",
                "message": "Examination not found.",
            })
            continue

        current_status = (examination.status or "DRAFT").upper()

        # Lifecycle gate
        if current_status == "PUBLISHED":
            results.append({
                "examination_id": examination_id,
                "status": "REFUSED",
                "reason": "PUBLISHED",
                "message": (
                    "Examination is PUBLISHED. Use the emergency "
                    "reallocation workflow with a recorded incident."
                ),
            })
            continue

        if current_status in {"VALIDATED", "REVIEW", "APPROVED"}:
            results.append({
                "examination_id": examination_id,
                "status": "REFUSED",
                "reason": current_status,
                "message": (
                    f"Allocation cannot be regenerated while the "
                    f"examination is {current_status}."
                ),
            })
            continue

        # Stale check per exam (opt-in)
        expected_updated_at = expected_updated_at_map.get(
            str(examination_id)
        )
        current_updated_at = (
            examination.updated_at.isoformat()
            if examination.updated_at
            else None
        )

        if (
            confirm
            and isinstance(expected_updated_at, str)
            and expected_updated_at
            and expected_updated_at != current_updated_at
        ):
            results.append({
                "examination_id": examination_id,
                "status": "STALE",
                "message": (
                    "Examination changed since preview. "
                    "Re-run preview."
                ),
                "expected_updated_at": expected_updated_at,
                "current_updated_at": current_updated_at,
            })
            continue

        # Readiness
        timetable_entries = (
            Timetable.query
            .filter_by(examination_id=examination_id)
            .order_by(
                Timetable.exam_date,
                Timetable.start_time,
                Timetable.id,
            )
            .all()
        )

        eligible_students = get_eligible_students(examination_id)
        eligible_count = len(eligible_students)
        hall_readiness = get_hall_readiness()

        per_timetable = []
        all_sufficient = True
        worst_shortage = 0

        for entry in timetable_entries:
            usable = get_available_halls(entry)
            cap = sum(h.examination_capacity for h in usable)
            suff = cap >= eligible_count
            short = max(0, eligible_count - cap)
            if not suff:
                all_sufficient = False
            worst_shortage = max(worst_shortage, short)
            per_timetable.append({
                "timetable_id": entry.id,
                "exam_date": entry.exam_date.isoformat(),
                "session": entry.session,
                "required_capacity": eligible_count,
                "available_capacity": cap,
                "sufficient": suff,
                "shortage": short,
            })

        global_suff = (
            hall_readiness["total_available_capacity"]
            >= eligible_count
        )
        capacity_sufficient = (
            all_sufficient if timetable_entries else global_suff
        )
        ready = (
            bool(timetable_entries)
            and eligible_count > 0
            and capacity_sufficient
        )

        readiness = {
            "ready_for_allocation": ready,
            "student_eligibility": {
                "eligible_student_count": eligible_count,
            },
            "hall_readiness": {
                "available_hall_count":
                    hall_readiness["available_hall_count"],
                "total_available_capacity":
                    hall_readiness["total_available_capacity"],
                "accessible_hall_count":
                    hall_readiness["accessible_hall_count"],
                "accessible_capacity":
                    hall_readiness["accessible_capacity"],
            },
            "capacity_check": {
                "required_capacity": eligible_count,
                "sufficient": capacity_sufficient,
                "shortage": (
                    worst_shortage if timetable_entries
                    else max(0, eligible_count -
                             hall_readiness["total_available_capacity"])
                ),
                "global": {
                    "required_capacity": eligible_count,
                    "available_capacity":
                        hall_readiness["total_available_capacity"],
                    "sufficient": global_suff,
                    "shortage": max(
                        0,
                        eligible_count -
                        hall_readiness["total_available_capacity"],
                    ),
                },
                "per_timetable": per_timetable,
            },
            "timetable_entry_count": len(timetable_entries),
        }

        if not ready:
            results.append({
                "examination_id": examination_id,
                "status": "NOT READY",
                "message":
                    "Examination is not ready for allocation.",
                "readiness": readiness,
            })
            continue

        # Preview path
        if not confirm:
            plan_result = plan_allocation(
                examination_id,
                allocation_options=options,
            )
            if not plan_result.get("success"):
                results.append({
                    "examination_id": examination_id,
                    "status": "PLAN FAILED",
                    "message": plan_result.get(
                        "message",
                        "Planner refused the plan.",
                    ),
                    "planner": plan_result,
                    "readiness": readiness,
                })
                continue

            proposed = [
                {
                    "timetable_id": a.timetable_id,
                    "hall_id": a.hall_id,
                    "allocated_capacity": a.allocated_capacity,
                    "purpose": a.purpose,
                }
                for a in plan_result["allocations"]
            ]

            proposed_validation = validate_proposed_plan(
                examination_id,
                proposed,
                eligible_students=plan_result.get(
                    "total_students"
                ),
                accessibility_students=len(
                    plan_result.get("accessibility_students") or []
                ),
            )

            results.append({
                "examination_id": examination_id,
                "status": "PREVIEW",
                "examination": {
                    "id": examination.id,
                    "name": examination.name,
                    "status": examination.status,
                    "updated_at": current_updated_at,
                },
                "proposed_allocations": proposed,
                "proposed_counts": {
                    "students": plan_result.get(
                        "total_students", 0
                    ),
                    "halls": len({
                        a.hall_id for a in plan_result["allocations"]
                    }),
                    "allocated_capacity": sum(
                        a.allocated_capacity
                        for a in plan_result["allocations"]
                    ),
                    "accessibility_students": len(
                        plan_result.get("accessibility_students") or []
                    ),
                },
                "validation": proposed_validation,
                "readiness": readiness,
            })
            continue

        # Apply path
        apply_result = generate_allocation(
            examination_id,
            force=True,
            allocation_options=options,
        )

        if not apply_result.get("success"):
            results.append({
                "examination_id": examination_id,
                "status": "APPLY FAILED",
                "message": apply_result.get(
                    "message",
                    "generate_allocation failed.",
                ),
                "detail": apply_result,
            })
            continue

        post_validation = validate_allocation(examination_id)

        invig_result = None
        invig_validation = None
        partial_failure = None

        if options.get("generate_invigilators"):
            invig_result = generate_invigilator_allocation(
                examination_id, force=True
            )
            if not invig_result.get("success"):
                partial_failure = {
                    "stage": "invigilators",
                    "message": invig_result.get(
                        "message",
                        "Invigilator generation failed.",
                    ),
                    "detail": invig_result,
                }
            else:
                invig_validation = (
                    validate_invigilator_allocation(examination_id)
                )

        results.append({
            "examination_id": examination_id,
            "status": "APPLIED",
            "examination": {
                "id": examination.id,
                "name": examination.name,
                "status": examination.status,
                "updated_at": (
                    examination.updated_at.isoformat()
                    if examination.updated_at
                    else None
                ),
            },
            "allocation": apply_result,
            "validation": post_validation,
            "invigilator_allocation": invig_result,
            "invigilator_validation": invig_validation,
            "partial_failure": partial_failure,
        })

    any_failed = any(
        row["status"] not in {"PREVIEW", "APPLIED"}
        for row in results
    )

    return jsonify({
        "success": not any_failed,
        "mode": "applied" if confirm else "preview",
        "examination_ids": examination_ids,
        "allocation_options": options,
        "applied_options": describe_options(options),
        "parsed": parsed_payload,
        "unsupported_requirements": unsupported,
        "results": results,
    }), 200