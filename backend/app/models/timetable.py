from datetime import datetime

from app import db


class Timetable(db.Model):
    __tablename__ = "timetables"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    exam_date = db.Column(
        db.Date,
        nullable=False
    )

    session = db.Column(
        db.String(20),
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False
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

    examination = db.relationship(
        "Examination",
        backref="timetable_entries"
    )

    subject = db.relationship(
        "Subject",
        backref="timetable_entries"
    )

    __table_args__ = (
    db.UniqueConstraint(
        "examination_id",
        "subject_id",
        name="uq_examination_subject_timetable"
    ),
)

    def __repr__(self):
        return f"<Timetable {self.id}>"