"""
Post-Phase 7 — Invigilator allocation + workload + conflicts.
"""

import pytest

from app import db
from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall_allocation import HallAllocation
from app.models.staff import Staff
from app.models.invigilator_allocation import InvigilatorAllocation

from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
    invigilator_workload,
)
from app.services.allocation import generate_allocation
from app.services.validation import validate_invigilator_allocation


def _invigilators(examination_id):
    return InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).all()


def _ensure_hall_allocation(examination_id):
    if not HallAllocation.query.filter_by(
        examination_id=examination_id
    ).first():
        generate_allocation(examination_id, force=True)


# ============================================================
# 8A.1 — First generation
# ============================================================

def test_invigilator_generation_succeeds(
    app_context, examination_id
):
    _ensure_hall_allocation(examination_id)
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert result.get("success") is True, result


def test_invigilator_assignments_created(
    app_context, examination_id
):
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert result.get("invigilator_assignments", 0) > 0


def test_invigilator_coverage_spans_all_hall_slots(
    app_context, examination_id
):
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert result.get("hall_slots", 0) > 0


def test_distinct_staff_used(app_context, examination_id):
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    assert result.get("distinct_staff_used", 0) > 0


# ============================================================
# 8A.2 — Row-level structure
# ============================================================

def test_persisted_invigilator_rows_match_generation(
    app_context, examination_id
):
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    count = result.get("invigilator_assignments", 0)
    assert len(_invigilators(examination_id)) == count


# ============================================================
# 8A.3 — Coverage
# ============================================================

def test_every_hall_allocation_has_at_least_one_invigilator(
    app_context, examination_id
):
    generate_invigilator_allocation(examination_id, force=True)

    hall_keys = {
        (a.timetable_id, a.hall_id)
        for a in HallAllocation.query.filter_by(
            examination_id=examination_id
        ).all()
    }

    covered = {
        (row.timetable_id, row.hall_id)
        for row in _invigilators(examination_id)
    }

    assert hall_keys.issubset(covered)


# ============================================================
# 8A.4 — Staff validity
# ============================================================

def test_all_invigilators_are_active(
    app_context, examination_id
):
    rows = _invigilators(examination_id)
    staff_ids = {r.staff_id for r in rows}
    for staff in Staff.query.filter(Staff.id.in_(staff_ids)).all():
        assert staff.is_active


def test_all_invigilators_are_available(
    app_context, examination_id
):
    rows = _invigilators(examination_id)
    staff_ids = {r.staff_id for r in rows}
    for staff in Staff.query.filter(Staff.id.in_(staff_ids)).all():
        assert staff.availability


# ============================================================
# 8A.5 — Duplicate prevention
# ============================================================

def test_no_duplicate_timetable_hall_staff_assignments(
    app_context, examination_id
):
    keys = [
        (r.timetable_id, r.hall_id, r.staff_id)
        for r in _invigilators(examination_id)
    ]
    assert len(keys) == len(set(keys))


# ============================================================
# 8A.6 — Overlap conflicts
# ============================================================

def test_no_staff_member_scheduled_in_overlapping_sessions(
    app_context, examination_id
):
    rows = _invigilators(examination_id)

    by_staff = {}
    for row in rows:
        by_staff.setdefault(row.staff_id, []).append(row)

    for rows_for_staff in by_staff.values():
        for i, a in enumerate(rows_for_staff):
            for b in rows_for_staff[i + 1:]:
                ta, tb = a.timetable, b.timetable
                if not ta or not tb:
                    continue
                if a.timetable_id == b.timetable_id:
                    continue
                if ta.exam_date != tb.exam_date:
                    continue
                overlap = (
                    ta.start_time < tb.end_time
                    and ta.end_time > tb.start_time
                )
                assert not overlap


# ============================================================
# 8A.7 — Independent validation
# ============================================================

def test_independent_invigilator_validation_is_valid(
    app_context, examination_id
):
    result = validate_invigilator_allocation(examination_id)
    assert result.get("status") == "VALID", result


def test_independent_invigilator_validation_no_errors(
    app_context, examination_id
):
    result = validate_invigilator_allocation(examination_id)
    assert result.get("errors") == []


# ============================================================
# 8A.8 — Duplicate generation protection
# ============================================================

def test_duplicate_invigilator_generation_rejected(
    app_context, examination_id
):
    result = generate_invigilator_allocation(
        examination_id, force=False
    )
    assert result.get("success") is False


# ============================================================
# 8A.9 — Determinism
# ============================================================

def _signature(examination_id):
    return sorted(
        (
            r.timetable_id,
            r.hall_id,
            r.staff_id,
            r.role,
        )
        for r in _invigilators(examination_id)
    )


def test_force_regeneration_is_deterministic(
    app_context, examination_id
):
    generate_invigilator_allocation(examination_id, force=True)
    before = _signature(examination_id)

    generate_invigilator_allocation(examination_id, force=True)
    after = _signature(examination_id)

    assert before == after


# ============================================================
# 8A.10 — No duplicate accumulation
# ============================================================

def test_regeneration_does_not_accumulate_invigilators(
    app_context, examination_id
):
    result = generate_invigilator_allocation(
        examination_id, force=True
    )
    expected = result.get("invigilator_assignments")
    assert len(_invigilators(examination_id)) == expected

def test_invigilator_shortage_force_failure_is_non_destructive(
    app_context, examination_id
):
    _ensure_hall_allocation(examination_id)

    generate_invigilator_allocation(
        examination_id,
        force=True,
    )

    existing_rows = InvigilatorAllocation.query.filter_by(
        examination_id=examination_id
    ).all()

    existing_count = len(existing_rows)

    available_staff = Staff.query.filter_by(
        is_active=True,
        availability=True,
    ).all()

    assert available_staff, (
        "Expected active and available staff before shortage test"
    )

    original_availability = {
        staff.id: staff.availability
        for staff in available_staff
    }

    try:
        for staff in available_staff:
            staff.availability = False

        db.session.commit()

        result = generate_invigilator_allocation(
            examination_id,
            force=True,
        )

        assert result.get("success") is False, result

        remaining_count = InvigilatorAllocation.query.filter_by(
            examination_id=examination_id
        ).count()

        assert remaining_count == existing_count
    finally:
        for staff in available_staff:
            staff.availability = original_availability[staff.id]

        db.session.commit()

# ============================================================
# 8A.11 — Workload summary
# ============================================================

def test_workload_summary_matches_assignment_count(
    app_context, examination_id
):
    rows = _invigilators(examination_id)
    workload = invigilator_workload(examination_id)

    assert len(workload) > 0
    assert sum(e["duties"] for e in workload) == len(rows)


# ============================================================
# 8A.12 — Cross-examination conflict
# ============================================================

def test_cross_examination_staff_conflict_is_detected(
    app_context, examination_id
):
    conflict_staff = (
        Staff.query
        .filter_by(is_active=True, availability=True)
        .order_by(Staff.id)
        .first()
    )
    source_timetable = (
        Timetable.query
        .filter_by(examination_id=examination_id)
        .order_by(Timetable.id)
        .first()
    )
    
    if not conflict_staff or not source_timetable:
        pytest.skip(
            "Insufficient data to construct a cross-examination staff conflict"
        )

    other_timetable = (
        Timetable.query
        .join(
            Examination,
            Timetable.examination_id == Examination.id,
        )
        .filter(
            Timetable.examination_id != examination_id,
            Timetable.exam_date == source_timetable.exam_date,
            Timetable.start_time < source_timetable.end_time,
            Timetable.end_time > source_timetable.start_time,
        )
        .first()
    )
    
    if not other_timetable:
        pytest.skip(
            "No overlapping timetable exists in another examination"
        )

    other_allocation = (
        HallAllocation.query
        .filter_by(
            examination_id=other_timetable.examination_id,
            timetable_id=other_timetable.id,
        )
        .first()
    )
    
    if not other_allocation:
        pytest.skip(
            "No hall allocation exists for the overlapping timetable"
        )

    current_row = _invigilators(examination_id)[0]

    conflict_row = InvigilatorAllocation(
        examination_id=other_timetable.examination_id,
        timetable_id=other_timetable.id,
        hall_allocation_id=other_allocation.id,
        hall_id=other_allocation.hall_id,
        staff_id=conflict_staff.id,
        role="INVIGILATOR",
        status="GENERATED",
    )

    original_staff_id = current_row.staff_id

    try:
        db.session.add(conflict_row)
        db.session.commit()

        current_row.staff_id = conflict_staff.id
        db.session.commit()

        result = validate_invigilator_allocation(examination_id)
        assert result.get("status") == "INVALID"
    finally:
        current_row.staff_id = original_staff_id

        refreshed = db.session.get(
            InvigilatorAllocation,
            conflict_row.id,
        )

        if refreshed is not None:
            db.session.delete(refreshed)

        db.session.commit()

    assert (
        validate_invigilator_allocation(examination_id).get("status")
        == "VALID"
    )


# ============================================================
# 8A.14 — Relationship integrity
# ============================================================

def test_invigilator_relationship_integrity(
    app_context, examination_id
):
    for row in _invigilators(examination_id):
        assert row.examination_id == examination_id
        assert row.timetable is not None
        assert row.timetable.examination_id == examination_id
        assert row.hall_allocation is not None
        assert (
            row.hall_allocation.examination_id == examination_id
        )
        assert (
            row.hall_allocation.timetable_id == row.timetable_id
        )
        assert row.hall_allocation.hall_id == row.hall_id
        assert row.staff is not None


# ============================================================
# 8A.15 — Staff readiness
# ============================================================

def test_validation_rejects_inactive_invigilator(
    app_context, examination_id
):
    row = _invigilators(examination_id)[0]
    original_active = row.staff.is_active

    try:
        row.staff.is_active = False
        db.session.commit()
        assert (
            validate_invigilator_allocation(examination_id).get(
                "status"
            )
            == "INVALID"
        )
    finally:
        row.staff.is_active = original_active
        db.session.commit()


def test_validation_rejects_unavailable_invigilator(
    app_context, examination_id
):
    row = _invigilators(examination_id)[0]
    original_available = row.staff.availability

    try:
        row.staff.availability = False
        db.session.commit()
        assert (
            validate_invigilator_allocation(examination_id).get(
                "status"
            )
            == "INVALID"
        )
    finally:
        row.staff.availability = original_available
        db.session.commit()

    assert (
        validate_invigilator_allocation(examination_id).get("status")
        == "VALID"
    )