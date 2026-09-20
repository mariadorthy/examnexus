from flask import Blueprint, request
from app import db
from app.models.staff import Staff
from app.auth.decorators import roles_required

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_staff():

    staff_members = Staff.query.all()

    return [
        {
            "id": staff.id,
            "name": staff.name,
            "department_id": staff.department_id,
            "email": staff.email,
            "contact_no": staff.contact_no,
            "designation": staff.designation,
            "dob": staff.dob.isoformat() if staff.dob else None,
            "assigned_courses": staff.assigned_courses,
            "gender": staff.gender,
            "availability": staff.availability,
            "assigned_batch": staff.assigned_batch,
            "image": staff.image,
            "is_active": staff.is_active
        }
        for staff in staff_members
    ]

@staff_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_staff():

    data = request.get_json()

    staff = Staff(
        name=data["name"],
        department_id=data["department_id"],
        email=data["email"],
        contact_no=data.get("contact_no"),
        designation=data["designation"],
        assigned_courses=data.get("assigned_courses"),
        gender=data.get("gender"),
        availability=data.get("availability", True),
        assigned_batch=data.get("assigned_batch"),
        password_hash=data["password_hash"],
        image=data.get("image")
    )

    db.session.add(staff)
    db.session.commit()

    return {
        "message": "Staff created successfully",
        "id": staff.id
    }, 201