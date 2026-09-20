from sqlalchemy import UniqueConstraint

from datetime import datetime

from app import db


class ExamRegistration(db.Model):
    __tablename__ = "exam_registrations"

    __table_args__ = (
    UniqueConstraint(
        "student_id",
        "examination_id",
        name="unique_student_examination"
    ),
)
    
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="REGISTERED",
        nullable=False
    )

    registered_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    student = db.relationship(
        "Student",
        backref="exam_registrations"
    )

    examination = db.relationship(
        "Examination",
        backref="registrations"
    )

    def __repr__(self):
        return f"<ExamRegistration {self.id}>"