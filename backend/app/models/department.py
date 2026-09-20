from datetime import datetime

from app import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)

    department_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    department_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
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
    
    courses = db.relationship(
        "Course",
        back_populates="department"
    )

    def __repr__(self):
        return f"<Department {self.department_code}>"