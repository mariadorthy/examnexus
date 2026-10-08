"""
Hall ticket generation service.

Rules:
  - Only examinations with status == "PUBLISHED" may issue tickets.
  - One ticket per (student_id, examination_id).
  - verification_token is a uuid4 hex string; deterministic per ticket,
    not per request.
  - QR payload = {"t": "<verification_token>"} only.
"""

import uuid
import os
from app import db

from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.student import Student
from app.models.seat_allocation import SeatAllocation
from app.models.hall_ticket import HallTicket

from app.services.qr import make_qr_base64


def _build_ticket_payload(student, examination, seat_rows):
    """
    Build the full hall-ticket payload for a single student.
    """

    entries = []

    for row in seat_rows:
        timetable = row.timetable
        hall = row.hall

        if not timetable or not hall:
            continue

        entries.append({
            "timetable_id": timetable.id,
            "subject_id": timetable.subject_id,
            "subject_name": (
                timetable.subject.subject_name
                if timetable.subject else None
            ),
            "subject_code": (
                timetable.subject.subject_code
                if timetable.subject else None
            ),
            "exam_date": timetable.exam_date.isoformat(),
            "session": timetable.session,
            "start_time": timetable.start_time.strftime("%H:%M"),
            "end_time": timetable.end_time.strftime("%H:%M"),
            "hall_id": hall.id,
            "hall_name": hall.name,
            "building_name": hall.building_name,
            "floor_no": hall.floor_no,
            "seat_number": row.seat_number,
            "row_label": row.row_label,
            "seat_index": row.seat_index
        })

    entries.sort(
        key=lambda entry: (
            entry["exam_date"],
            entry["start_time"]
        )
    )

    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "course_id": student.course_id,
            "batch": student.batch,
            "semester": student.semester
        },
        "examination": {
            "id": examination.id,
            "name": examination.name,
            "exam_type": examination.exam_type,
            "course_id": examination.course_id,
            "semester": examination.semester,
            "start_date": examination.start_date.isoformat(),
            "end_date": examination.end_date.isoformat()
        },
        "entries": entries
    }

def generate_hall_tickets(examination_id, force=False):
    """
    Issue one HallTicket per eligible student for the examination.

    Requires:
      - examination.status == "PUBLISHED"
      - both persisted validators currently return VALID

    Publishing is a two-step guarantee: the lifecycle service
    already validated at PUBLISH time, but data can drift
    between publish and ticket issuance (manual edits, external
    processes, future bugs). We re-validate here so tickets are
    never issued for a broken plan.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
        }

    if examination.status != "PUBLISHED":
        return {
            "success": False,
            "message": (
                "Hall tickets can only be generated for a "
                "PUBLISHED examination"
            ),
            "current_status": examination.status
        }

    # ---------------------------------------------------------
    # FRESH VALIDATION
    # Reuse the existing independent validators. Do not create
    # a new validation engine.
    # ---------------------------------------------------------

    from app.services.validation import (
        validate_allocation,
        validate_invigilator_allocation,
    )

    hall_result = validate_allocation(examination_id)
    invig_result = validate_invigilator_allocation(examination_id)

    validation_errors = []

    if hall_result.get("status") != "VALID":
        validation_errors.append(
            "Hall/seat validation failed at ticket issuance: "
            + "; ".join(hall_result.get("errors", []) or [])
        )

    if invig_result.get("status") != "VALID":
        validation_errors.append(
            "Invigilator validation failed at ticket issuance: "
            + "; ".join(invig_result.get("errors", []) or [])
        )

    if validation_errors:
        return {
            "success": False,
            "message": (
                "Cannot issue hall tickets: persisted allocation "
                "is no longer valid"
            ),
            "status": examination.status,
            "errors": validation_errors
        }

    seat_rows = (
                SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    if not seat_rows:
        return {
            "success": False,
            "message": "No seat allocations exist for this examination"
        }

    # Group seats by student
    by_student = {}
    for row in seat_rows:
        by_student.setdefault(row.student_id, []).append(row)

    existing_tickets = {
        ticket.student_id: ticket
        for ticket in (
            HallTicket.query
            .filter_by(examination_id=examination_id)
            .all()
        )
    }

    if existing_tickets and not force:
        return {
            "success": False,
            "message": (
                "Hall tickets already exist for this examination. "
                "Use force=true to reissue."
            ),
            "existing_tickets": len(existing_tickets)
        }

    created = 0
    reused = 0

    try:
        if force and existing_tickets:
            (
                HallTicket.query
                .filter_by(examination_id=examination_id)
                .delete(synchronize_session=False)
            )
            existing_tickets = {}

        for student_id in sorted(by_student.keys()):
            if student_id in existing_tickets:
                reused += 1
                continue

            token = uuid.uuid4().hex

            ticket = HallTicket(
                student_id=student_id,
                examination_id=examination_id,
                verification_token=token,
                status="ISSUED"
            )

            db.session.add(ticket)
            created += 1

        db.session.commit()

    except Exception as error:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to generate hall tickets",
            "error": str(error)
        }

    return {
        "success": True,
        "message": "Hall tickets generated successfully",
        "examination_id": examination_id,
        "issued": created,
        "reused": reused,
        "students": len(by_student)
    }


def get_hall_ticket(student_id, examination_id):
    """
    Full hall-ticket data for a student, including QR base64 image.
    """

    ticket = (
        HallTicket.query
        .filter_by(
            student_id=student_id,
            examination_id=examination_id
        )
        .first()
    )

    if not ticket:
        return {
            "success": False,
            "message": "Hall ticket not found"
        }

    student = Student.query.get(student_id)
    examination = Examination.query.get(examination_id)

    if not student or not examination:
        return {
            "success": False,
            "message": "Missing student or examination record"
        }

    seat_rows = (
        SeatAllocation.query
        .filter_by(
            examination_id=examination_id,
            student_id=student_id
        )
        .order_by(SeatAllocation.timetable_id.asc())
        .all()
    )

    payload = _build_ticket_payload(
        student, examination, seat_rows
    )

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    ).rstrip("/")

    verification_url = (
        f"{frontend_url}/verify-hall-ticket/"
        f"{ticket.verification_token}"
    )

    qr_b64 = make_qr_base64(verification_url)

    return {
        "success": True,
        "ticket": {
            "id": ticket.id,
            "verification_token": ticket.verification_token,
            "status": ticket.status,
            "issued_at": ticket.issued_at.isoformat(),
            "qr_base64": qr_b64
        },
        "payload": payload
    }

# Ticket statuses that must never verify as valid.
TERMINAL_TICKET_STATUSES = frozenset({"INVALIDATED"})


def invalidate_hall_tickets(examination_id, commit=True):
    """
    Mark every existing hall ticket for the examination as
    INVALIDATED.

    Used when a reallocation changes the underlying seat /
    hall / invigilator plan and old tickets would otherwise
    represent a stale seating arrangement.

    Deterministic: only flips status; never deletes rows;
    preserves verification_token for audit.
    """

    rows = (
        HallTicket.query
        .filter_by(examination_id=examination_id)
        .all()
    )

    if not rows:
        return {
            "success": True,
            "examination_id": examination_id,
            "invalidated": 0,
        }

    changed = 0
    for ticket in rows:
        if ticket.status != "INVALIDATED":
            ticket.status = "INVALIDATED"
            changed += 1

    if not commit:
        return {
            "success": True,
            "examination_id": examination_id,
            "invalidated": changed,
            "committed": False,
        }

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return {
            "success": False,
            "message": "Failed to invalidate hall tickets",
            "error": str(error),
        }

    return {
        "success": True,
        "examination_id": examination_id,
        "invalidated": changed,
        "committed": True,
    }


def verify_hall_ticket(verification_token):
    """
    Public verification endpoint: returns safe identity info only.
    No password, no hash, no JWT, no internal DB ids beyond what is
    strictly needed for the examiner to check.

    Invalidated tickets verify as invalid but still return the
    safe identity fields so an examiner can see which ticket was
    presented.
    """

    ticket = (
        HallTicket.query
        .filter_by(verification_token=verification_token)
        .first()
    )

    if not ticket:
        return {
            "valid": False,
            "message": "Ticket not found"
        }
    student = ticket.student
    examination = ticket.examination

    if not student or not examination:
        return {
            "valid": False,
            "message": "Ticket references missing records"
        }

    seat_rows = (
        SeatAllocation.query
        .filter_by(
            examination_id=ticket.examination_id,
            student_id=ticket.student_id
        )
        .order_by(
            SeatAllocation.timetable_id.asc()
        )
        .all()
    )

    seat_by_timetable = {
        row.timetable_id: row
        for row in seat_rows
    }

    timetable_rows = (
        Timetable.query
        .filter_by(
            examination_id=ticket.examination_id
        )
        .order_by(
            Timetable.exam_date.asc(),
            Timetable.start_time.asc()
        )
        .all()
    )

    timetable = []

    for row in timetable_rows:

        seat = seat_by_timetable.get(row.id)

        timetable.append({
            "timetable_id": row.id,

            "subject_name": (
                row.subject.subject_name
                if row.subject
                else None
            ),

            "subject_code": (
                row.subject.subject_code
                if row.subject
                else None
            ),

            "exam_date": row.exam_date.isoformat(),

            "session": row.session,

            "start_time": (
                row.start_time.strftime("%H:%M")
                if row.start_time
                else None
            ),

            "end_time": (
                row.end_time.strftime("%H:%M")
                if row.end_time
                else None
            ),

            "hall_name": (
                seat.hall.name
                if seat and seat.hall
                else None
            ),

            "building_name": (
                seat.hall.building_name
                if seat and seat.hall
                else None
            ),

            "floor_no": (
                seat.hall.floor_no
                if seat and seat.hall
                else None
            ),

            "seat_number": (
                seat.seat_number
                if seat
                else None
            ),

            "row_label": (
                seat.row_label
                if seat
                else None
            ),
        })

    is_terminal = ticket.status in TERMINAL_TICKET_STATUSES

    return {
        "valid": not is_terminal,
        "status": ticket.status,
"student_code": student.student_id,
"student_name": student.name,
"student_batch": student.batch,
"student_semester": student.semester,

        "examination": examination.name,
        "exam_type": examination.exam_type,

        "timetable": timetable,

        "message": (
            "Ticket has been invalidated"
            if is_terminal
            else "Ticket is valid"
        ),
    }