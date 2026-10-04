from datetime import datetime

from sqlalchemy import UniqueConstraint

from app import db


class SeatAllocation(db.Model):
    __tablename__ = "seat_allocations"

    __table_args__ = (
        UniqueConstraint(
            "timetable_id",
            "hall_id",
            "seat_number",
            name="uq_timetable_hall_seat"
        ),
        UniqueConstraint(
            "timetable_id",
            "student_id",
            name="uq_timetable_student_seat"
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

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    seat_number = db.Column(
        db.String(10),
        nullable=False
    )

    row_label = db.Column(
        db.String(5),
        nullable=False
    )

    seat_index = db.Column(
        db.Integer,
        nullable=False
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
        backref="seat_allocations"
    )

    timetable = db.relationship(
        "Timetable",
        backref="seat_allocations"
    )

    hall_allocation = db.relationship(
        "HallAllocation",
        backref="seat_allocations"
    )

    hall = db.relationship(
        "Hall",
        backref="seat_allocations"
    )

    student = db.relationship(
        "Student",
        backref="seat_allocations"
    )

    def __repr__(self):
        return (
            f"<SeatAllocation "
            f"hall={self.hall_id} "
            f"seat={self.seat_number} "
            f"student={self.student_id}>"
        )