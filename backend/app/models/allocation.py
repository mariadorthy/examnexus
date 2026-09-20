from datetime import datetime

from sqlalchemy import UniqueConstraint

from app import db


class Allocation(db.Model):
    __tablename__ = "allocations"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "examination_id",
            name="unique_student_examination_allocation"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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

    hall_id = db.Column(
        db.Integer,
        db.ForeignKey("halls.id"),
        nullable=False
    )

    seat_number = db.Column(
        db.String(20),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="GENERATED",
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

    student = db.relationship(
        "Student",
        backref="allocations"
    )

    examination = db.relationship(
        "Examination",
        backref="allocations"
    )

    hall = db.relationship(
        "Hall",
        backref="allocations"
    )

    def __repr__(self):
        return f"<Allocation {self.id}>"