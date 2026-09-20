from datetime import datetime

from app import db


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)

    subject_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    subject_name = db.Column(
        db.String(150),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    subject_type = db.Column(
        db.String(30),
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

    course = db.relationship(
        "Course",
        backref="subjects"
    )

    def __repr__(self):
        return f"<Subject {self.subject_code}>"