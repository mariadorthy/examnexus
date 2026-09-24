from flask import Blueprint, request
from app import db
from app.models.hall import Hall
from app.auth.decorators import roles_required
halls_bp = Blueprint("halls", __name__)

@halls_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_halls():
    halls = Hall.query.order_by(Hall.name.asc()).all()

    return [
        {
            "id": hall.id,
            "name": hall.name,
            "building_name": hall.building_name,
            "floor_no": hall.floor_no,
            "capacity": hall.capacity,
            "examination_capacity": hall.examination_capacity,
            "room_type": hall.room_type,
            "amenities": hall.amenities,
            "assigned_course_id": hall.assigned_course_id,
            "assigned_batch": hall.assigned_batch,
            "is_available": hall.is_available,
            "is_under_maintenance": hall.is_under_maintenance,
            "is_accessible": hall.is_accessible,
            "is_active": hall.is_active,
        }
        for hall in halls
    ]


@halls_bp.route("/<int:hall_id>", methods=["GET"])
@roles_required("admin")
def get_hall_detail(hall_id):
    hall = db.session.get(Hall, hall_id)

    if not hall:
        return {
            "success": False,
            "message": "Hall not found."
        }, 404

    return {
        "success": True,
        "hall": {
            "id": hall.id,
            "name": hall.name,
            "building_name": hall.building_name,
            "floor_no": hall.floor_no,
            "capacity": hall.capacity,
            "examination_capacity": hall.examination_capacity,
            "room_type": hall.room_type,
            "amenities": hall.amenities,
            "assigned_course_id": hall.assigned_course_id,
            "assigned_batch": hall.assigned_batch,
            "is_available": hall.is_available,
            "is_under_maintenance": hall.is_under_maintenance,
            "is_accessible": hall.is_accessible,
            "is_active": hall.is_active,
            "created_at": (
                hall.created_at.isoformat()
                if hall.created_at
                else None
            ),
            "updated_at": (
                hall.updated_at.isoformat()
                if hall.updated_at
                else None
            ),
        }
    }, 200


@halls_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_hall():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "name",
        "building_name",
        "floor_no",
        "capacity",
        "examination_capacity",
        "room_type",
    ]

    missing_fields = [
        field
        for field in required_fields
        if data.get(field) is None or data.get(field) == ""
    ]

    if missing_fields:
        return {
            "success": False,
            "message": (
                f"Missing required fields: "
                f"{', '.join(missing_fields)}"
            )
        }, 400

    name = str(data["name"]).strip()
    building_name = str(data["building_name"]).strip()
    room_type = str(data["room_type"]).strip()

    if not name:
        return {
            "success": False,
            "message": "Hall name is required."
        }, 400

    if not building_name:
        return {
            "success": False,
            "message": "Building name is required."
        }, 400

    if not room_type:
        return {
            "success": False,
            "message": "Room type is required."
        }, 400

    try:
        floor_no = int(data["floor_no"])
        capacity = int(data["capacity"])
        examination_capacity = int(
            data["examination_capacity"]
        )
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": (
                "Floor number, capacity and "
                "examination capacity must be valid numbers."
            )
        }, 400

    if floor_no < 0:
        return {
            "success": False,
            "message": "Floor number cannot be negative."
        }, 400

    if capacity <= 0:
        return {
            "success": False,
            "message": "Capacity must be greater than zero."
        }, 400

    if examination_capacity <= 0:
        return {
            "success": False,
            "message": (
                "Examination capacity must be greater than zero."
            )
        }, 400

    if examination_capacity > capacity:
        return {
            "success": False,
            "message": (
                "Examination capacity cannot be "
                "greater than total capacity."
            )
        }, 400

    assigned_course_id = data.get("assigned_course_id")

    if assigned_course_id in ("", None):
        assigned_course_id = None
    else:
        try:
            assigned_course_id = int(assigned_course_id)
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "assigned_course_id must be a valid number."
            }, 400

    existing_hall = Hall.query.filter(
        db.func.lower(Hall.name) == name.lower(),
        db.func.lower(Hall.building_name)
        == building_name.lower()
    ).first()

    if existing_hall:
        return {
            "success": False,
            "message": (
                "A hall with this name already exists "
                "in this building."
            )
        }, 409

    hall = Hall(
        name=name,
        building_name=building_name,
        floor_no=floor_no,
        capacity=capacity,
        examination_capacity=examination_capacity,
        room_type=room_type,
        amenities=data.get("amenities"),
        assigned_course_id=assigned_course_id,
        assigned_batch=data.get("assigned_batch"),
        is_available=data.get("is_available", True),
        is_under_maintenance=data.get(
            "is_under_maintenance",
            False
        ),
        is_accessible=data.get(
            "is_accessible",
            True
        ),
        is_active=True,
    )

    db.session.add(hall)
    db.session.commit()

    return {
        "success": True,
        "message": "Hall created successfully",
        "id": hall.id,
    }, 201


@halls_bp.route("/<int:hall_id>", methods=["PUT"])
@roles_required("admin")
def update_hall(hall_id):
    hall = db.session.get(Hall, hall_id)

    if not hall:
        return {
            "success": False,
            "message": "Hall not found."
        }, 404

    data = request.get_json(silent=True) or {}

    name = data.get("name", hall.name)
    building_name = data.get(
        "building_name",
        hall.building_name
    )
    room_type = data.get(
        "room_type",
        hall.room_type
    )

    if not isinstance(name, str) or not name.strip():
        return {
            "success": False,
            "message": "Hall name is required."
        }, 400

    if (
        not isinstance(building_name, str)
        or not building_name.strip()
    ):
        return {
            "success": False,
            "message": "Building name is required."
        }, 400

    if not isinstance(room_type, str) or not room_type.strip():
        return {
            "success": False,
            "message": "Room type is required."
        }, 400

    try:
        floor_no = int(
            data.get("floor_no", hall.floor_no)
        )
        capacity = int(
            data.get("capacity", hall.capacity)
        )
        examination_capacity = int(
            data.get(
                "examination_capacity",
                hall.examination_capacity
            )
        )
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": (
                "Floor number, capacity and "
                "examination capacity must be valid numbers."
            )
        }, 400

    if floor_no < 0:
        return {
            "success": False,
            "message": "Floor number cannot be negative."
        }, 400

    if capacity <= 0:
        return {
            "success": False,
            "message": "Capacity must be greater than zero."
        }, 400

    if examination_capacity <= 0:
        return {
            "success": False,
            "message": (
                "Examination capacity must be greater than zero."
            )
        }, 400

    if examination_capacity > capacity:
        return {
            "success": False,
            "message": (
                "Examination capacity cannot be "
                "greater than total capacity."
            )
        }, 400

    assigned_course_id = data.get(
        "assigned_course_id",
        hall.assigned_course_id
    )

    if assigned_course_id in ("", None):
        assigned_course_id = None
    else:
        try:
            assigned_course_id = int(assigned_course_id)
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "assigned_course_id must be a valid number."
            }, 400

    duplicate_hall = Hall.query.filter(
        db.func.lower(Hall.name) == name.strip().lower(),
        db.func.lower(Hall.building_name)
        == building_name.strip().lower(),
        Hall.id != hall.id
    ).first()

    if duplicate_hall:
        return {
            "success": False,
            "message": (
                "A hall with this name already exists "
                "in this building."
            )
        }, 409

    is_available = data.get(
        "is_available",
        hall.is_available
    )

    is_under_maintenance = data.get(
        "is_under_maintenance",
        hall.is_under_maintenance
    )

    is_accessible = data.get(
        "is_accessible",
        hall.is_accessible
    )

    if not isinstance(is_available, bool):
        return {
            "success": False,
            "message": "is_available must be a boolean."
        }, 400

    if not isinstance(is_under_maintenance, bool):
        return {
            "success": False,
            "message": (
                "is_under_maintenance must be a boolean."
            )
        }, 400

    if not isinstance(is_accessible, bool):
        return {
            "success": False,
            "message": "is_accessible must be a boolean."
        }, 400

    hall.name = name.strip()
    hall.building_name = building_name.strip()
    hall.floor_no = floor_no
    hall.capacity = capacity
    hall.examination_capacity = examination_capacity
    hall.room_type = room_type.strip()
    hall.amenities = data.get(
        "amenities",
        hall.amenities
    )
    hall.assigned_course_id = assigned_course_id
    hall.assigned_batch = data.get(
        "assigned_batch",
        hall.assigned_batch
    )
    hall.is_available = is_available
    hall.is_under_maintenance = is_under_maintenance
    hall.is_accessible = is_accessible

    db.session.commit()

    return {
        "success": True,
        "message": "Hall updated successfully"
    }, 200


@halls_bp.route(
    "/<int:hall_id>/status",
    methods=["PATCH"]
)
@roles_required("admin")
def toggle_hall_status(hall_id):
    hall = Hall.query.get_or_404(hall_id)

    data = request.get_json(silent=True) or {}

    if "is_active" not in data:
        return {
            "success": False,
            "message": "is_active is required."
        }, 400

    if not isinstance(data["is_active"], bool):
        return {
            "success": False,
            "message": "is_active must be a boolean."
        }, 400

    hall.is_active = data["is_active"]

    db.session.commit()

    return {
        "success": True,
        "message": (
            "Hall activated successfully"
            if hall.is_active
            else "Hall deactivated successfully"
        ),
        "is_active": hall.is_active,
    }, 200