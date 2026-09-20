from datetime import datetime
from app import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    course_name = db.Column(
        db.String(150),
        nullable=False
    )

    course_abbreviation = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    program_level = db.Column(
        db.String(50),
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    department = db.relationship(
    "Department",
    back_populates="courses"
)

    study_shift = db.Column(
        db.String(20),
        nullable=False
    )

    session = db.Column(
        db.String(2),
        nullable=False
    )

    total_semesters = db.Column(
        db.Integer,
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
        return f"<Course {self.course_code}>"