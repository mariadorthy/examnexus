from datetime import datetime

from sqlalchemy import UniqueConstraint

from app import db


class HallAllocation(db.Model):
    __tablename__ = "hall_allocations"

    __table_args__ = (
        UniqueConstraint(
            "timetable_id",
            "hall_id",
            name="uq_timetable_hall_allocation"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    timetable_id = db.Column(
        db.Integer,
        db.ForeignKey("timetables.id"),
        nullable=False
    )

    hall_id = db.Column(
        db.Integer,
        db.ForeignKey("halls.id"),
        nullable=False
    )

    allocated_capacity = db.Column(
        db.Integer,
        nullable=False
    )

    purpose = db.Column(
        db.String(30),
        nullable=False,
        default="NORMAL"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="GENERATED"
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

    examination = db.relationship(
        "Examination",
        backref="hall_allocations"
    )

    timetable = db.relationship(
        "Timetable",
        backref="hall_allocations"
    )

    hall = db.relationship(
        "Hall",
        backref="hall_allocations"
    )

    def __repr__(self):
        return f"<HallAllocation {self.id}>"