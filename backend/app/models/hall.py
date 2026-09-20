from datetime import datetime

from app import db


class Hall(db.Model):
    __tablename__ = "halls"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    building_name = db.Column(
        db.String(100),
        nullable=False
    )

    floor_no = db.Column(
        db.Integer,
        nullable=False
    )

    capacity = db.Column(
        db.Integer,
        nullable=False
    )

    examination_capacity = db.Column(
        db.Integer,
        nullable=False
    )

    room_type = db.Column(
        db.String(30),
        nullable=False
    )

    amenities = db.Column(
        db.Text,
        nullable=True
    )

    is_available = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    is_under_maintenance = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    is_accessible = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    assigned_course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=True
    )

    assigned_batch = db.Column(
        db.String(20),
        nullable=True
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

    assigned_course = db.relationship(
        "Course",
        backref="assigned_halls"
    )

    def __repr__(self):
        return f"<Hall {self.name}>"