from datetime import datetime

from sqlalchemy import UniqueConstraint

from app import db


class HallTicket(db.Model):
    __tablename__ = "hall_tickets"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "examination_id",
            "version",
            name="uq_hall_ticket_student_exam_version"
        ),
        UniqueConstraint(
            "verification_token",
            name="uq_hall_ticket_token"
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

    verification_token = db.Column(
        db.String(64),
        nullable=False
    )

    # Version starts at 1 for the first issuance of a ticket
    # for (student, examination). Emergency reallocation after
    # publication creates version N+1 and marks N as SUPERSEDED.
    version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="ISSUED"
    )

    issued_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
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
        backref="hall_tickets"
    )

    examination = db.relationship(
        "Examination",
        backref="hall_tickets"
    )

    def __repr__(self):
        return (
            f"<HallTicket student={self.student_id} "
            f"exam={self.examination_id}>"
        )