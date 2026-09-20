from datetime import datetime

from app import db


class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)

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

    exam_type = db.Column(
        db.String(30),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="SCHEDULED",
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

    subject = db.relationship(
        "Subject",
        backref="examinations"
    )

    def __repr__(self):
        return f"<Examination {self.id}>"