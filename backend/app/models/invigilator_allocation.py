from datetime import datetime

from sqlalchemy import UniqueConstraint

from app import db


class InvigilatorAllocation(db.Model):
    __tablename__ = "invigilator_allocations"

    __table_args__ = (
        UniqueConstraint(
            "timetable_id",
            "hall_id",
            "staff_id",
            name="uq_timetable_hall_invigilator"
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

    hall_allocation_id = db.Column(
        db.Integer,
        db.ForeignKey("hall_allocations.id"),
        nullable=False
    )

    hall_id = db.Column(
        db.Integer,
        db.ForeignKey("halls.id"),
        nullable=False
    )

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("staff.id"),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="INVIGILATOR"
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
        backref="invigilator_allocations"
    )

    timetable = db.relationship(
        "Timetable",
        backref="invigilator_allocations"
    )

    hall_allocation = db.relationship(
        "HallAllocation",
        backref="invigilator_allocations"
    )

    hall = db.relationship(
        "Hall",
        backref="invigilator_allocations"
    )

    staff = db.relationship(
        "Staff",
        backref="invigilator_allocations"
    )

    def __repr__(self):
        return (
            f"<InvigilatorAllocation "
            f"timetable={self.timetable_id} "
            f"hall={self.hall_id} "
            f"staff={self.staff_id}>"
        )