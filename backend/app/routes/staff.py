from datetime import date

from flask import Blueprint, request
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app import db
from app.models.staff import Staff
from app.models.department import Department
from app.auth.decorators import roles_required

staff_bp = Blueprint("staff", __name__)
# =========================================================
# GET ALL STAFF
# =========================================================

@staff_bp.route("", methods=["GET"])
@roles_required("admin")
def get_staff():

    staff_members = Staff.query.order_by(
        Staff.name.asc()
    ).all()

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

@staff_bp.route("/<int:staff_id>", methods=["GET"])
@roles_required("admin")
def get_staff_detail(staff_id):
    staff = db.session.get(Staff, staff_id)

    if not staff:
        return {
            "success": False,
            "message": "Staff member not found."
        }, 404

    return {
        "success": True,
        "staff": {
            "id": staff.id,
            "name": staff.name,
            "department_id": staff.department_id,
            "email": staff.email,
            "contact_no": staff.contact_no,
            "designation": staff.designation,
            "dob": staff.dob.isoformat()
            if staff.dob else None,
            "assigned_courses": staff.assigned_courses,
            "gender": staff.gender,
            "availability": staff.availability,
            "assigned_batch": staff.assigned_batch,
            "image": staff.image,
            "is_active": staff.is_active,
            "created_at": staff.created_at.isoformat()
            if staff.created_at else None,
            "updated_at": staff.updated_at.isoformat()
            if staff.updated_at else None,
        }
    }, 200

@staff_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_staff():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "name",
        "department_id",
        "email",
        "designation",
        "password",
    ]

    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    designation = data["designation"].strip()

    if not name:
        return {
            "success": False,
            "message": "Staff name is required."
        }, 400

    if not email:
        return {
            "success": False,
            "message": "Email is required."
        }, 400

    if not designation:
        return {
            "success": False,
            "message": "Designation is required."
        }, 400

    try:
        department_id = int(data["department_id"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "department_id must be a valid number."
        }, 400

    department = db.session.get(Department, department_id)

    if not department:
        return {
            "success": False,
            "message": "Selected department does not exist."
        }, 400

    existing_staff = Staff.query.filter(
        func.lower(Staff.email) == email
    ).first()

    if existing_staff:
        return {
            "success": False,
            "message": "A staff member with this email already exists."
        }, 409

    availability = data.get("availability", True)

    if not isinstance(availability, bool):
        return {
            "success": False,
            "message": "availability must be a boolean."
        }, 400

    dob = None

    if data.get("dob"):
        try:
            dob = date.fromisoformat(data["dob"])
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "dob must be in YYYY-MM-DD format."
            }, 400

    staff = Staff(
        name=name,
        department_id=department_id,
        email=email,
        contact_no=data.get("contact_no"),
        designation=designation,
        dob=dob,
        assigned_courses=data.get("assigned_courses"),
        gender=data.get("gender"),
        availability=availability,
        assigned_batch=data.get("assigned_batch"),
        password_hash=generate_password_hash(data["password"]),
        image=data.get("image")
    )

    db.session.add(staff)
    db.session.commit()

    return {
        "success": True,
        "message": "Staff created successfully",
        "id": staff.id
    }, 201

@staff_bp.route("/<int:staff_id>", methods=["PUT"])
@roles_required("admin")
def update_staff(staff_id):
    staff = db.session.get(Staff, staff_id)

    if not staff:
        return {
            "success": False,
            "message": "Staff member not found."
        }, 404

    data = request.get_json(silent=True) or {}

    name = data.get("name", staff.name)
    email = data.get("email", staff.email)
    designation = data.get("designation", staff.designation)

    if not isinstance(name, str) or not name.strip():
        return {
            "success": False,
            "message": "Staff name is required."
        }, 400

    if not isinstance(email, str) or not email.strip():
        return {
            "success": False,
            "message": "Email is required."
        }, 400

    if not isinstance(designation, str) or not designation.strip():
        return {
            "success": False,
            "message": "Designation is required."
        }, 400

    email = email.strip().lower()

    duplicate_staff = Staff.query.filter(
        func.lower(Staff.email) == email,
        Staff.id != staff.id
    ).first()

    if duplicate_staff:
        return {
            "success": False,
            "message": "A staff member with this email already exists."
        }, 409

    department_id = data.get(
        "department_id",
        staff.department_id
    )

    try:
        department_id = int(department_id)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "department_id must be a valid number."
        }, 400

    department = db.session.get(Department, department_id)

    if not department:
        return {
            "success": False,
            "message": "Selected department does not exist."
        }, 400

    availability = data.get(
        "availability",
        staff.availability
    )

    if not isinstance(availability, bool):
        return {
            "success": False,
            "message": "availability must be a boolean."
        }, 400

    dob = staff.dob

    if "dob" in data:
        if data["dob"]:
            try:
                dob = date.fromisoformat(data["dob"])
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "message": "dob must be in YYYY-MM-DD format."
                }, 400
        else:
            dob = None

    staff.name = name.strip()
    staff.department_id = department_id
    staff.email = email
    staff.contact_no = data.get(
        "contact_no",
        staff.contact_no
    )
    staff.designation = designation.strip()
    staff.dob = dob
    staff.assigned_courses = data.get(
        "assigned_courses",
        staff.assigned_courses
    )
    staff.gender = data.get(
        "gender",
        staff.gender
    )
    staff.availability = availability
    staff.assigned_batch = data.get(
        "assigned_batch",
        staff.assigned_batch
    )
    staff.image = data.get(
        "image",
        staff.image
    )

    if data.get("password"):
        staff.password_hash = generate_password_hash(
            data["password"]
        )

    db.session.commit()

    return {
        "success": True,
        "message": "Staff updated successfully"
    }, 200

# =========================================================
# ACTIVATE / DEACTIVATE
# =========================================================

@staff_bp.route(
    "/<int:staff_id>/status",
    methods=["PATCH"]
)
@roles_required("admin")
def toggle_staff_status(staff_id):

    staff = Staff.query.get_or_404(staff_id)

    data = request.get_json() or {}

    if "is_active" not in data:
        return {
            "message": "is_active is required."
        }, 400

    staff.is_active = bool(
        data["is_active"]
    )

    db.session.commit()

    return {
        "message": (
            "Staff activated successfully"
            if staff.is_active
            else "Staff deactivated successfully"
        ),
        "is_active": staff.is_active
    }