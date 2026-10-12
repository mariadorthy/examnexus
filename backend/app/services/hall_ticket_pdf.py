"""
Hall-ticket PDF renderer.

Pure function: takes the payload dict produced by
app.services.hall_ticket._build_ticket_payload plus the QR
base64 string, returns PDF bytes.

No DB access. No auth. No PII beyond what the payload already
contains (name, student_id, exam, timetable, allotment).
DOB / email / avatar are NEVER read here.
"""

import base64
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BRAND = colors.HexColor("#1f2937")
ACCENT = colors.HexColor("#4f46e5")
LIGHT = colors.HexColor("#f3f4f6")
BORDER = colors.HexColor("#d1d5db")


def _fmt_date(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y")
    except (TypeError, ValueError):
        return str(value)

def _safe(value, fallback="—"):
    if value is None or value == "":
        return fallback
    return str(value)

def build_hall_ticket_pdf(payload, qr_base64):
    """
    Return PDF bytes for one student's hall ticket.
    """
    student = payload.get("student", {}) or {}
    examination = payload.get("examination", {}) or {}
    entries = payload.get("entries", []) or []

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="ExamNexus Hall Ticket",
        author="ExamNexus",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ENTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=BRAND,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ENSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
    )
    section_style = ParagraphStyle(
        "ENSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=ACCENT,
        spaceBefore=8,
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "ENCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
    )
    cell_bold = ParagraphStyle(
        "ENCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )
    caption_style = ParagraphStyle(
        "ENCaption",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#6b7280"),
        alignment=1,
    )

    flow = []

    # -------- Header --------
    flow.append(Paragraph("ExamNexus", title_style))
    flow.append(
        Paragraph(
            "UNIVERSITY EXAMINATION HALL TICKET",
            ParagraphStyle(
                "ENHead2",
                parent=subtitle_style,
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=BRAND,
            ),
        )
    )

    exam_line_parts = [examination.get("name")]
    if examination.get("exam_type"):
        exam_line_parts.append(examination["exam_type"])
    if examination.get("start_date") or examination.get("end_date"):
        exam_line_parts.append(
            f"{_fmt_date(examination.get('start_date'))} – "
            f"{_fmt_date(examination.get('end_date'))}"
        )

    flow.append(
        Paragraph(
            " · ".join(p for p in exam_line_parts if p),
            subtitle_style,
        )
    )
    flow.append(Spacer(1, 6 * mm))

    # -------- Candidate + QR row --------
    candidate_rows = [
        ["Candidate Name", _safe(student.get("name"))],
        ["Student ID", _safe(student.get("student_id"))],
        ["Examination", _safe(examination.get("name"))],
        [
            "Examination Session",
            f"{_safe(examination.get('start_date') and _fmt_date(examination.get('start_date')))}"
            f" – "
            f"{_safe(examination.get('end_date') and _fmt_date(examination.get('end_date')))}",
        ],
        ["Semester", _safe(student.get("semester"))],
        ["Batch", _safe(student.get("batch"))],
    ]

    candidate_table = Table(
        [[Paragraph(k, cell_bold), Paragraph(v, cell_style)] for k, v in candidate_rows],
        colWidths=[42 * mm, 80 * mm],
    )
    candidate_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, BORDER),
            ]
        )
    )

    qr_image = None
    if qr_base64:
        try:
            qr_bytes = base64.b64decode(qr_base64)
            qr_image = Image(io.BytesIO(qr_bytes), width=38 * mm, height=38 * mm)
        except Exception:
            qr_image = None

    qr_stack = []
    if qr_image is not None:
        qr_stack.append(qr_image)
        qr_stack.append(Spacer(1, 2 * mm))
        qr_stack.append(Paragraph("Scan to verify hall ticket", caption_style))

    top_table = Table(
        [[candidate_table, qr_stack or ""]],
        colWidths=[130 * mm, 45 * mm],
    )
    top_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    flow.append(top_table)
    flow.append(Spacer(1, 6 * mm))

    # -------- Timetable / Allotment --------
    flow.append(Paragraph("Examination Timetable & Seat Allotment", section_style))

    header = [
        "Subject",
        "Code",
        "Date",
        "Session",
        "Start",
        "End",
        "Hall",
        "Building",
        "Floor",
        "Seat",
    ]

    data = [[Paragraph(h, cell_bold) for h in header]]

    if entries:
        for e in entries:
            data.append(
                [
                    Paragraph(_safe(e.get("subject_name")), cell_style),
                    Paragraph(_safe(e.get("subject_code")), cell_style),
                    Paragraph(_fmt_date(e.get("exam_date")), cell_style),
                    Paragraph(_safe(e.get("session")), cell_style),
                    Paragraph(_safe(e.get("start_time")), cell_style),
                    Paragraph(_safe(e.get("end_time")), cell_style),
                    Paragraph(_safe(e.get("hall_name")), cell_style),
                    Paragraph(_safe(e.get("building_name")), cell_style),
                    Paragraph(_safe(e.get("floor_no")), cell_style),
                    Paragraph(_safe(e.get("seat_number")), cell_style),
                ]
            )
    else:
        data.append(
            [
                Paragraph("No timetable / allotment entries available.", cell_style),
                "", "", "", "", "", "", "", "", "",
            ]
        )

    col_widths = [
        40 * mm, 16 * mm, 20 * mm, 18 * mm, 14 * mm,
        14 * mm, 30 * mm, 28 * mm, 12 * mm, 14 * mm,
    ]

    tt_table = Table(data, colWidths=col_widths, repeatRows=1)
    tt_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, 0), BRAND),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    flow.append(tt_table)

    # -------- Footer --------
    flow.append(Spacer(1, 6 * mm))
    flow.append(
        Paragraph(
            "This hall ticket is valid only with a government-issued photo ID. "
            "Report to the examination hall 30 minutes before the scheduled start time. "
            "Electronic devices are not permitted inside the examination hall.",
            subtitle_style,
        )
    )

    doc.build(flow)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes