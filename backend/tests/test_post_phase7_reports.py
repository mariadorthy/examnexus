"""
Post-Phase 7 — Reports.
"""

from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.reports import (
    allocation_report,
    student_allocation_report,
    hall_utilization_report,
    invigilator_workload_report,
)


def test_allocation_report_generated(app_context, examination_id):
    result = allocation_report(examination_id)
    assert result.get("success") is True


def test_allocation_report_has_rows(app_context, examination_id):
    result = allocation_report(examination_id)
    assert len(result.get("rows", [])) > 0


def test_student_allocation_report_generated(
    app_context, examination_id
):
    result = student_allocation_report(examination_id)
    assert result.get("success") is True


def test_student_allocation_report_row_count(
    app_context, examination_id
):
    result = student_allocation_report(examination_id)
    persisted = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    assert len(result.get("rows", [])) == persisted


def test_hall_utilization_report_generated(
    app_context, examination_id
):
    result = hall_utilization_report(examination_id)
    assert result.get("success") is True


def test_hall_utilization_percentages_are_bounded(
    app_context, examination_id
):
    result = hall_utilization_report(examination_id)
    for row in result.get("rows", []):
        assert 0 <= row["utilization_percent"] <= 100


def test_invigilator_workload_report_generated(
    app_context, examination_id
):
    result = invigilator_workload_report(examination_id)
    assert result.get("success") is True


def test_invigilator_workload_report_totals(
    app_context, examination_id
):
    result = invigilator_workload_report(examination_id)
    persisted = InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    assert sum(
        row["duties"] for row in result.get("rows", [])
    ) == persisted


def test_allocation_report_matches_persisted_count(
    app_context, examination_id
):
    result = allocation_report(examination_id)
    persisted = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    assert len(result.get("rows", [])) == persisted