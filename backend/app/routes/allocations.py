from flask import Blueprint, request

from app.models.hall_allocation import HallAllocation
from app.models.timetable import Timetable

from app.services.allocation import (
    generate_allocation,
    update_hall_allocation
)
from app.services.reallocation import simulate_reallocation

from app.services.bulk_allocation import generate_bulk_allocation
from app.services.validation import validate_allocation

from app.auth.decorators import roles_required


allocations_bp = Blueprint("allocations", __name__)

@allocations_bp.route(
    "/generate/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def generate(examination_id):

    data = request.get_json(silent=True) or {}

    force = bool(data.get("force", False))

    result = generate_allocation(
        examination_id,
        force=force
    )

    if result["success"]:
        return result, 200

    return result, 400

@allocations_bp.route(
    "/bulk-generate",
    methods=["POST"]
)
@roles_required("admin")
def bulk_generate():

    data = request.get_json() or {}

    examination_ids = data.get(
        "examination_ids",
        []
    )

    if not isinstance(examination_ids, list):
        return {
            "success": False,
            "message": (
                "examination_ids must be a list."
            )
        }, 400

    examination_ids = [
        int(examination_id)
        for examination_id in examination_ids
        if str(examination_id).isdigit()
    ]

    if not examination_ids:
        return {
            "success": False,
            "message": (
                "At least one examination must be selected."
            )
        }, 400

    force = bool(data.get("force", False))

    result = generate_bulk_allocation(
        examination_ids,
        force=force
    )

    if result["success"]:
        return result, 200

    return result, 400

@allocations_bp.route(
    "/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def get_allocations(examination_id):

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .join(Timetable)
        .order_by(
            Timetable.exam_date,
            Timetable.start_time,
            HallAllocation.id
        )
        .all()
    )

    return [
        {
            "id": allocation.id,
            "examination_id": allocation.examination_id,
            "timetable_id": allocation.timetable_id,

            "exam_date": (
                allocation.timetable.exam_date.isoformat()
                if allocation.timetable
                else None
            ),

            "session": (
                allocation.timetable.session
                if allocation.timetable
                else None
            ),

            "start_time": (
                allocation.timetable.start_time.strftime("%H:%M")
                if allocation.timetable
                else None
            ),

            "end_time": (
                allocation.timetable.end_time.strftime("%H:%M")
                if allocation.timetable
                else None
            ),

            "hall_id": allocation.hall_id,

            "hall": (
                allocation.hall.name
                if allocation.hall
                else None
            ),

            "building_name": (
                allocation.hall.building_name
                if allocation.hall
                else None
            ),

            "floor_no": (
                allocation.hall.floor_no
                if allocation.hall
                else None
            ),

            "examination_capacity": (
                allocation.hall.examination_capacity
                if allocation.hall
                else 0
            ),

            "allocated_capacity": allocation.allocated_capacity,

            "purpose": allocation.purpose,
            "status": allocation.status
        }
        for allocation in allocations
    ]

@allocations_bp.route(
    "/<int:allocation_id>",
    methods=["PATCH"]
)
@roles_required("admin")
def update_allocation(allocation_id):

    data = request.get_json() or {}

    allowed_fields = {
        "hall_id",
        "allocated_capacity",
        "purpose"
    }

    invalid_fields = set(data.keys()) - allowed_fields

    if invalid_fields:
        return {
            "success": False,
            "message": "Invalid fields in request.",
            "invalid_fields": list(invalid_fields)
        }, 400

    if not data:
        return {
            "success": False,
            "message": "No fields provided to update."
        }, 400

    result = update_hall_allocation(
        allocation_id=allocation_id,
        hall_id=data.get("hall_id"),
        allocated_capacity=data.get("allocated_capacity"),
        purpose=data.get("purpose")
    )

    if result["success"]:
        return result, 200

    return result, 400

@allocations_bp.route(
    "/validate/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def validate(examination_id):

    result = validate_allocation(examination_id)

    status_code = (
        200
        if result["status"] in ["VALID", "NOT GENERATED"]
        else 400
    )

    return result, status_code


@allocations_bp.route(
    "/summary/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def summary(examination_id):

    allocations = (
        HallAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    validation = validate_allocation(examination_id)

    allocated_capacity = sum(
        allocation.allocated_capacity
        for allocation in allocations
    )

    hall_ids = {
        allocation.hall_id
        for allocation in allocations
    }

    timetable_ids = {
        allocation.timetable_id
        for allocation in allocations
    }

    return {
        "examination_id": examination_id,
        "allocated_capacity": allocated_capacity,
        "halls_used": len(hall_ids),
        "timetable_entries": len(timetable_ids),
        "unallocated_students": validation.get(
            "unallocated_students",
            0
        ),
        "status": validation["status"]
    }

@allocations_bp.route(
    "/seats/generate/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def generate_seats(examination_id):

    from app.services.seat_allocation import (
        generate_seat_allocation
    )

    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))

    result = generate_seat_allocation(
        examination_id,
        force=force
    )

    if result["success"]:
        return result, 200

    return result, 400


@allocations_bp.route(
    "/seats/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def list_seats(examination_id):

    from app.services.seat_allocation import (
        get_seat_allocations
    )

    return get_seat_allocations(examination_id), 200


@allocations_bp.route(
    "/hall-allocations/<int:hall_allocation_id>/seats",
    methods=["GET"]
)
@roles_required("admin")
def hall_seats(hall_allocation_id):

    from app.services.seat_allocation import (
        get_hall_seating
    )

    result = get_hall_seating(hall_allocation_id)

    if result["success"]:
        return result, 200

    return result, 404


@allocations_bp.route(
    "/seats/<int:examination_id>",
    methods=["DELETE"]
)
@roles_required("admin")
def clear_seats(examination_id):

    from app.services.seat_allocation import (
        clear_seat_allocation
    )

    result = clear_seat_allocation(examination_id)

    return result, 200

# =========================================================
# INVIGILATOR ALLOCATION
# =========================================================

@allocations_bp.route(
    "/invigilators/generate/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def generate_invigilators(examination_id):

    from app.services.invigilator_allocation import (
        generate_invigilator_allocation
    )

    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))

    result = generate_invigilator_allocation(
        examination_id,
        force=force
    )

    if result["success"]:
        return result, 200

    return result, 400


@allocations_bp.route(
    "/invigilators/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def list_invigilators(examination_id):

    from app.services.invigilator_allocation import (
        get_invigilator_allocations
    )

    return get_invigilator_allocations(examination_id), 200


@allocations_bp.route(
    "/invigilators/<int:examination_id>",
    methods=["DELETE"]
)
@roles_required("admin")
def clear_invigilators(examination_id):

    from app.services.invigilator_allocation import (
        clear_invigilator_allocations
    )

    result = clear_invigilator_allocations(examination_id)

    return result, 200


@allocations_bp.route(
    "/invigilators/validate/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def validate_invigilators(examination_id):

    from app.services.validation import (
        validate_invigilator_allocation
    )

    result = validate_invigilator_allocation(examination_id)

    status_code = (
        200 if result["status"] == "VALID" else 400
    )

    return result, status_code


@allocations_bp.route(
    "/invigilators/workload/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def invigilator_workload_route(examination_id):

    from app.services.invigilator_allocation import (
        invigilator_workload
    )

    return invigilator_workload(examination_id), 200

# =========================================================
# BULK OPERATIONS
# =========================================================


def _normalize_examination_ids(raw_ids):
    """
    Convert a raw list of examination ids into a clean list of
    integers, discarding anything that is not a positive number.
    """

    if not isinstance(raw_ids, list):
        return None

    cleaned = []

    for value in raw_ids:
        if str(value).isdigit():
            candidate = int(value)
            if candidate > 0:
                cleaned.append(candidate)

    return cleaned


@allocations_bp.route(
    "/seats/bulk-generate",
    methods=["POST"]
)
@roles_required("admin")
def bulk_generate_seats():

    from app.services.seat_allocation import (
        generate_bulk_seat_allocation
    )

    data = request.get_json(silent=True) or {}

    examination_ids = _normalize_examination_ids(
        data.get("examination_ids", [])
    )

    if examination_ids is None:
        return {
            "success": False,
            "message": "examination_ids must be a list."
        }, 400

    if not examination_ids:
        return {
            "success": False,
            "message": "At least one examination must be selected."
        }, 400

    force = bool(data.get("force", False))

    result = generate_bulk_seat_allocation(
        examination_ids,
        force=force
    )

    return result, (200 if result["success"] else 400)


@allocations_bp.route(
    "/invigilators/bulk-generate",
    methods=["POST"]
)
@roles_required("admin")
def bulk_generate_invigilators():

    from app.services.invigilator_allocation import (
        generate_bulk_invigilator_allocation
    )

    data = request.get_json(silent=True) or {}

    examination_ids = _normalize_examination_ids(
        data.get("examination_ids", [])
    )

    if examination_ids is None:
        return {
            "success": False,
            "message": "examination_ids must be a list."
        }, 400

    if not examination_ids:
        return {
            "success": False,
            "message": "At least one examination must be selected."
        }, 400

    force = bool(data.get("force", False))

    result = generate_bulk_invigilator_allocation(
        examination_ids,
        force=force
    )

    return result, (200 if result["success"] else 400)


@allocations_bp.route(
    "/validate/bulk",
    methods=["POST"]
)
@roles_required("admin")
def bulk_validate():

    from app.services.validation import (
        bulk_validate_examinations
    )

    data = request.get_json(silent=True) or {}

    examination_ids = _normalize_examination_ids(
        data.get("examination_ids", [])
    )

    if examination_ids is None:
        return {
            "success": False,
            "message": "examination_ids must be a list."
        }, 400

    if not examination_ids:
        return {
            "success": False,
            "message": "At least one examination must be selected."
        }, 400

    result = bulk_validate_examinations(examination_ids)

    return result, 200

# =========================================================
# FEATURE 21 — DYNAMIC REALLOCATION / WHAT-IF
# =========================================================

@allocations_bp.route(
    "/reallocate/what-if/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def reallocate_what_if(examination_id):

    data = request.get_json(silent=True) or {}

    excluded = data.get("excluded_hall_ids")

    if not isinstance(excluded, list) or not excluded:
        return {
            "success": False,
            "message": (
                "excluded_hall_ids must be a non-empty list."
            ),
        }, 400

    result = simulate_reallocation(
        examination_id,
        excluded_hall_ids=excluded,
    )

    status_code = 200 if result.get("success") else 400

    return result, status_code

from app.services.reallocation import apply_reallocation


@allocations_bp.route(
    "/reallocate/apply/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def reallocate_apply(examination_id):
    data = request.get_json(silent=True) or {}

    if not data.get("confirm"):
        return {
            "success": False,
            "message": "Reallocation requires confirm=true."
        }, 400

    excluded = data.get("excluded_hall_ids")

    if not isinstance(excluded, list) or not excluded:
        return {
            "success": False,
            "message": (
                "excluded_hall_ids must be a non-empty list."
            )
        }, 400

    result = apply_reallocation(
        examination_id,
        excluded_hall_ids=excluded
    )

    return result, (200 if result.get("success") else 400)