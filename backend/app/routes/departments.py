from flask import Blueprint, request
from app import db
from app.models.department import Department
from app.auth.decorators import roles_required

departments_bp = Blueprint(
    "departments",
    __name__
)


# =========================================================
# GET ALL DEPARTMENTS
# =========================================================

@departments_bp.route("", methods=["GET"])
@roles_required("admin")
def get_departments():

    departments = Department.query.order_by(
        Department.department_name.asc()
    ).all()

    return [
        {
            "id": department.id,
            "department_code": department.department_code,
            "department_name": department.department_name,
            "is_active": department.is_active,
            "course_count": len(department.courses)
        }
        for department in departments
    ]


# =========================================================
# CREATE DEPARTMENT
# =========================================================

@departments_bp.route("", methods=["POST"])
@roles_required("admin")
def create_department():

    data = request.get_json() or {}

    department_code = (
        data.get("department_code") or ""
    ).strip().upper()

    department_name = (
        data.get("department_name") or ""
    ).strip()


    if not department_code:

        return {
            "message": "Department code is required."
        }, 400


    if not department_name:

        return {
            "message": "Department name is required."
        }, 400


    existing_code = Department.query.filter_by(
        department_code=department_code
    ).first()

    if existing_code:

        return {
            "message": "Department code already exists."
        }, 409


    existing_name = Department.query.filter_by(
        department_name=department_name
    ).first()

    if existing_name:

        return {
            "message": "Department name already exists."
        }, 409


    department = Department(
        department_code=department_code,
        department_name=department_name,
        is_active=True
    )

    db.session.add(department)
    db.session.commit()


    return {
        "message": "Department created successfully",
        "id": department.id
    }, 201


# =========================================================
# GET SINGLE DEPARTMENT
# =========================================================

@departments_bp.route("/<int:department_id>", methods=["GET"])
@roles_required("admin")
def get_department(department_id):

    department = Department.query.get_or_404(
        department_id
    )


    return {
        "id": department.id,
        "department_code": department.department_code,
        "department_name": department.department_name,
        "is_active": department.is_active,
        "course_count": len(department.courses),
        "courses": [
            {
                "id": course.id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "course_abbreviation": course.course_abbreviation,
                "program_level": course.program_level,
                "study_shift": course.study_shift,
                "session": course.session,
                "total_semesters": course.total_semesters,
                "is_active": course.is_active
            }
            for course in department.courses
        ]
    }


# =========================================================
# UPDATE DEPARTMENT
# =========================================================

@departments_bp.route("/<int:department_id>", methods=["PUT"])
@roles_required("admin")
def update_department(department_id):

    department = Department.query.get_or_404(
        department_id
    )

    data = request.get_json() or {}


    department_code = (
        data.get("department_code") or ""
    ).strip().upper()

    department_name = (
        data.get("department_name") or ""
    ).strip()


    if not department_code:

        return {
            "message": "Department code is required."
        }, 400


    if not department_name:

        return {
            "message": "Department name is required."
        }, 400


    existing_code = Department.query.filter(
        Department.department_code == department_code,
        Department.id != department.id
    ).first()

    if existing_code:

        return {
            "message": "Department code already exists."
        }, 409


    existing_name = Department.query.filter(
        Department.department_name == department_name,
        Department.id != department.id
    ).first()

    if existing_name:

        return {
            "message": "Department name already exists."
        }, 409


    department.department_code = department_code
    department.department_name = department_name

    db.session.commit()


    return {
        "message": "Department updated successfully"
    }


# =========================================================
# ACTIVATE / DEACTIVATE
# =========================================================

@departments_bp.route(
    "/<int:department_id>/status",
    methods=["PATCH"]
)
@roles_required("admin")
def toggle_department_status(department_id):

    department = Department.query.get_or_404(
        department_id
    )


    data = request.get_json() or {}


    if "is_active" not in data:

        return {
            "message": "is_active is required."
        }, 400


    department.is_active = bool(
        data["is_active"]
    )

    db.session.commit()


    return {
        "message": (
            "Department activated successfully"
            if department.is_active
            else "Department deactivated successfully"
        ),
        "is_active": department.is_active
    }
