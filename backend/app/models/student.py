from datetime import datetime

from app import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    course = db.relationship(
        "Course",
        backref="students"
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    contact_no = db.Column(
        db.String(20),
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
    )

    disability = db.Column(
        db.String(255),
        nullable=True
    )

    batch = db.Column(
        db.String(20),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    class_name = db.Column(
        db.String(50),
        nullable=True
    )

    session = db.Column(
        db.String(10),
        nullable=True
    )

    dob = db.Column(
        db.Date,
        nullable=True
    )

    student_img = db.Column(
        db.String(500),
        nullable=True
    )

    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    two_factor_enabled = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Student {self.student_id}>"