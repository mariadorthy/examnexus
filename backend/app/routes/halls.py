from flask import Blueprint, request
from app import db
from app.models.hall import Hall

halls_bp = Blueprint("halls", __name__)


@halls_bp.route("/", methods=["GET"])
def get_halls():
    halls = Hall.query.all()

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
            "is_active": hall.is_active
        }
        for hall in halls
    ]


@halls_bp.route("/", methods=["POST"])
def create_hall():
    data = request.get_json()

    hall = Hall(
        name=data["name"],
        building_name=data["building_name"],
        floor_no=data["floor_no"],
        capacity=data["capacity"],
        examination_capacity=data["examination_capacity"],
        room_type=data["room_type"],
        amenities=data.get("amenities"),
        assigned_course_id=data.get("assigned_course_id"),
        assigned_batch=data.get("assigned_batch")
    )

    db.session.add(hall)
    db.session.commit()

    return {
        "message": "Hall created successfully",
        "id": hall.id
    }, 201