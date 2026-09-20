from flask import Blueprint, request
from app import db
from app.models.student import Student
from app.auth.decorators import roles_required

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
            "is_active": student.is_active
        }
        for student in students
    ]


@students_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_student():

    data = request.get_json()

    student = Student(
        student_id=data["student_id"],
        name=data["name"],
        course_id=data["course_id"],
        email=data["email"],
        password_hash=data["password_hash"],
        batch=data["batch"],
        semester=data["semester"]
    )

    db.session.add(student)
    db.session.commit()

    return {
        "message": "Student created successfully",
        "id": student.id
    }, 201