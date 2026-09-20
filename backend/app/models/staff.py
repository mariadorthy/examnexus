from datetime import datetime

from app import db


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    contact_no = db.Column(
        db.String(20),
        nullable=True
    )

    designation = db.Column(
        db.String(100),
        nullable=False
    )

    dob = db.Column(
        db.Date,
        nullable=True
    )

    assigned_courses = db.Column(
        db.Text,
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
    )

    availability = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    assigned_batch = db.Column(
        db.String(20),
        nullable=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    image = db.Column(
        db.String(500),
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

    department = db.relationship(
        "Department",
        backref="staff_members"
    )

    def __repr__(self):
        return f"<Staff {self.name}>"