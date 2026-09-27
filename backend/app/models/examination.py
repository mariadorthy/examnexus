from datetime import datetime

from app import db


class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(150),
        nullable=False
    )

    exam_type = db.Column(
        db.String(30),
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

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="DRAFT",
        nullable=False
    )

    session_config = db.Column(
        db.JSON,
        nullable=False,
        default=list
    )

    excluded_dates = db.Column(
        db.JSON,
        nullable=False,
        default=list
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
    backref="examinations"
)

    def __repr__(self):
        return f"<Examination {self.id}>"