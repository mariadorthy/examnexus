from datetime import date

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from app import db
from app.auth.decorators import roles_required
from app.models.course import Course
from app.models.student import Student

students_bp = Blueprint("students", __name__)


@students_bp.route("/", methods=["GET"])
@roles_required("admin")
def get_students():
    students = Student.query.all()

    return [
        {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "course_id": student.course_id,
            "email": student.email,
            "batch": student.batch,
            "semester": student.semester,
            "class_name": student.class_name,
            "session": student.session,
            "contact_no": student.contact_no,
            "gender": student.gender,
            "disability": student.disability,
            "dob": student.dob.isoformat() if student.dob else None,
            "student_img": student.student_img,
            "email_verified": student.email_verified,
            "two_factor_enabled": student.two_factor_enabled,
            "is_active": student.is_active
        }
        for student in students
    ]


@students_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_student():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "student_id",
        "name",
        "course_id",
        "email",
        "password",
        "batch",
        "semester"
    ]

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    try:
        course_id = int(data["course_id"])
        semester = int(data["semester"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "course_id and semester must be valid numbers."
        }, 400

    course = db.session.get(Course, course_id)

    if not course:
        return {
            "success": False,
            "message": "Selected course does not exist."
        }, 400

    if semester < 1 or semester > course.total_semesters:
        return {
            "success": False,
            "message": "Semester is outside the selected course's semester range."
        }, 400

    student_id = data["student_id"].strip()
    name = data["name"].strip()
    email = data["email"].strip().lower()
    batch = data["batch"].strip()
    password = data["password"]

    if not student_id or not name or not email or not batch or not password:
        return {
            "success": False,
            "message": "Required fields cannot be empty."
        }, 400

    if Student.query.filter_by(student_id=student_id).first():
        return {
            "success": False,
            "message": "Student ID already exists."
        }, 409

    if Student.query.filter_by(email=email).first():
        return {
            "success": False,
            "message": "Email already exists."
        }, 409

    dob = None

    if data.get("dob"):
        try:
            dob = date.fromisoformat(data["dob"])
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "DOB must be a valid date."
            }, 400

    student = Student(
        student_id=student_id,
        name=name,
        course_id=course_id,
        email=email,
        password_hash=generate_password_hash(password),
        contact_no=data.get("contact_no"),
        gender=data.get("gender"),
        disability=data.get("disability"),
        batch=batch,
        semester=semester,
        class_name=data.get("class_name"),
        session=data.get("session"),
        dob=dob
    )

    db.session.add(student)
    db.session.commit()

    return {
        "success": True,
        "message": "Student created successfully",
        "id": student.id
    }, 201


@students_bp.route("/<int:student_id>", methods=["GET"])
@roles_required("admin")
def get_student(student_id):
    student = db.session.get(Student, student_id)

    if not student:
        return {
            "success": False,
            "message": "Student not found."
        }, 404

    return {
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "course_id": student.course_id,
        "email": student.email,
        "batch": student.batch,
        "semester": student.semester,
        "class_name": student.class_name,
        "session": student.session,
        "contact_no": student.contact_no,
        "gender": student.gender,
        "disability": student.disability,
        "dob": student.dob.isoformat() if student.dob else None,
        "student_img": student.student_img,
        "email_verified": student.email_verified,
        "two_factor_enabled": student.two_factor_enabled,
        "is_active": student.is_active
    }


@students_bp.route("/<int:student_id>", methods=["PUT"])
@roles_required("admin")
def update_student(student_id):
    student = db.session.get(Student, student_id)

    if not student:
        return {
            "success": False,
            "message": "Student not found."
        }, 404

    data = request.get_json(silent=True) or {}

    required_fields = [
        "student_id",
        "name",
        "course_id",
        "email",
        "batch",
        "semester"
    ]

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    try:
        course_id = int(data["course_id"])
        semester = int(data["semester"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "course_id and semester must be valid numbers."
        }, 400

    course = db.session.get(Course, course_id)

    if not course:
        return {
            "success": False,
            "message": "Selected course does not exist."
        }, 400

    if semester < 1 or semester > course.total_semesters:
        return {
            "success": False,
            "message": "Semester is outside the selected course's semester range."
        }, 400

    new_student_id = data["student_id"].strip()
    new_name = data["name"].strip()
    new_email = data["email"].strip().lower()
    new_batch = data["batch"].strip()

    duplicate_student_id = Student.query.filter(
        Student.student_id == new_student_id,
        Student.id != student_id
    ).first()

    if duplicate_student_id:
        return {
            "success": False,
            "message": "Student ID already exists."
        }, 409

    duplicate_email = Student.query.filter(
        Student.email == new_email,
        Student.id != student_id
    ).first()

    if duplicate_email:
        return {
            "success": False,
        "message": "Email already exists."
        }, 409

    dob = None

    if data.get("dob"):
        try:
            dob = date.fromisoformat(data["dob"])
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "DOB must be a valid date."
            }, 400

    student.student_id = new_student_id
    student.name = new_name
    student.course_id = course_id
    student.email = new_email
    student.contact_no = data.get("contact_no")
    student.gender = data.get("gender")
    student.disability = data.get("disability")
    student.batch = new_batch
    student.semester = semester
    student.class_name = data.get("class_name")
    student.session = data.get("session")
    student.dob = dob

    if data.get("password"):
        student.password_hash = generate_password_hash(data["password"])

    db.session.commit()

    return {
        "success": True,
        "message": "Student updated successfully"
    }


@students_bp.route("/<int:student_id>/status", methods=["PATCH"])
@roles_required("admin")
def update_student_status(student_id):
    student = db.session.get(Student, student_id)

    if not student:
        return {
            "success": False,
            "message": "Student not found."
        }, 404

    data = request.get_json(silent=True) or {}

    if not isinstance(data.get("is_active"), bool):
        return {
            "success": False,
            "message": "is_active must be a boolean."
        }, 400

    student.is_active = data["is_active"]
    db.session.commit()

    return {
        "success": True,
        "message": "Student status updated successfully",
        "is_active": student.is_active
    }