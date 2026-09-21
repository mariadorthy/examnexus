from flask import Blueprint
from app.models.allocation import Allocation
from app.services.allocation import generate_allocation
from app.services.validation import validate_allocation
from app.auth.decorators import roles_required
allocations_bp = Blueprint("allocations", __name__)


@allocations_bp.route("/generate/<int:examination_id>", methods=["POST"])
@roles_required("admin")
def generate(examination_id):

    existing = Allocation.query.filter_by(
        examination_id=examination_id
    ).first()

    if existing:
        return {
            "success": False,
            "message": "Allocation already exists for this examination"
        }, 409

    result = generate_allocation(examination_id)

    return result, 200 if result["success"] else 400


@allocations_bp.route("/<int:examination_id>", methods=["GET"])
@roles_required("admin")
def get_allocations(examination_id):

    allocations = Allocation.query.filter_by(
        examination_id=examination_id
    ).all()

    return [
        {
            "id": allocation.id,
            "student_id": allocation.student.student_id,
            "student_name": allocation.student.name,
            "hall": allocation.hall.name,
            "seat_number": allocation.seat_number,
            "status": allocation.status
        }
        for allocation in allocations
    ]


@allocations_bp.route("/validate/<int:examination_id>", methods=["GET"])
@roles_required("admin")
def validate(examination_id):

    result = validate_allocation(examination_id)

    status_code = 200 if result["status"] == "VALID" else 400

    return result, status_code


@allocations_bp.route("/summary/<int:examination_id>", methods=["GET"])
@roles_required("admin")
def summary(examination_id):

    allocations = Allocation.query.filter_by(
        examination_id=examination_id
    ).all()

    allocated_students = len(allocations)

    hall_ids = {
        allocation.hall_id
        for allocation in allocations
    }

    validation = validate_allocation(examination_id)

    return {
        "examination_id": examination_id,
        "allocated_students": allocated_students,
        "unallocated_students": 0,
        "halls_used": len(hall_ids),
        "status": validation["status"]
    }