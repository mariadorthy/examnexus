"""
Hall incident records.

Distinct from the legacy boolean flags on Hall (is_available,
is_under_maintenance). A HallIncident captures the reason,
description, scope, timestamps, and audit trail for a
temporary or long-running unavailability of a hall or lab.

Scopes:
  GLOBAL         — affects every examination planning operation
                   for this hall until resolved.
  EXAM_SPECIFIC  — affects only the examination referenced by
                   examination_id.
"""

from datetime import datetime

from app import db


# Closed set of categories. Stored as a string column so future
# additions do not require a DB-level enum migration.
CATEGORIES = frozenset({
    "MAINTENANCE",
    "EQUIPMENT_FAILURE",
    "FACILITY_DAMAGE",
    "TEMPORARY_UNAVAILABLE",
    "OTHER",
})

SCOPES = frozenset({"GLOBAL", "EXAM_SPECIFIC"})

STATUSES = frozenset({"OPEN", "RESOLVED"})


class HallIncident(db.Model):
    __tablename__ = "hall_incidents"

    id = db.Column(db.Integer, primary_key=True)

    hall_id = db.Column(
        db.Integer,
        db.ForeignKey("halls.id"),
        nullable=False,
        index=True,
    )

    category = db.Column(
        db.String(30),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    scope = db.Column(
        db.String(20),
        nullable=False,
        default="GLOBAL",
    )

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey("examinations.id"),
        nullable=True,
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )

    reported_by_admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id"),
        nullable=False,
    )

    reported_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    resolved_by_admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id"),
        nullable=True,
    )

    resolution_notes = db.Column(
        db.Text,
        nullable=True,
    )

    # Relationships
    hall = db.relationship(
        "Hall",
        backref="incidents",
    )

    examination = db.relationship(
        "Examination",
        backref="hall_incidents",
    )

    reported_by = db.relationship(
        "Admin",
        foreign_keys=[reported_by_admin_id],
    )

    resolved_by = db.relationship(
        "Admin",
        foreign_keys=[resolved_by_admin_id],
    )

    def __repr__(self):
        return (
            f"<HallIncident hall={self.hall_id} "
            f"scope={self.scope} status={self.status}>"
        )