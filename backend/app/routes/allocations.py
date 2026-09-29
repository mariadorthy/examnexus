from flask import Blueprint

from app.models.hall_allocation import HallAllocation
from app.models.timetable import Timetable

from app.services.allocation import generate_allocation
from app.services.validation import validate_allocation

from app.auth.decorators import roles_required


allocations_bp = Blueprint("allocations", __name__)


@allocations_bp.route(
    "/generate/<int:examination_id>",
    methods=["POST"]
)
@roles_required("admin")
def generate(examination_id):

    result = generate_allocation(examination_id)

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