"""
Phase 7 — Hall + accessibility + seat allocation.
"""

import pytest

from app import db
from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.student import Student
from app.services.eligibility import get_eligible_students
from app.services.allocation import generate_allocation
from app.services.validation import (
    validate_allocation,
    validate_invigilator_allocation
)


# ============================================================
# 7.0 — Generation
# ============================================================

def test_complete_allocation_generation_succeeds(
    app_context, examination_id
):
    result = generate_allocation(examination_id, force=True)
    assert result.get("success") is True, result


def test_no_students_remain_unallocated(
    app_context, examination_id
):
    result = generate_allocation(examination_id, force=True)
    assert result.get("unallocated_students") == 0


# ============================================================
# 7A — Hall allocation
# ============================================================

def _hall_allocations(examination_id):
    return HallAllocation.query.filter_by(
        examination_id=examination_id
    ).all()


def test_hall_allocations_created(app_context, examination_id):
    generate_allocation(examination_id, force=True)
    assert len(_hall_allocations(examination_id)) > 0


def test_allocated_capacity_covers_all_students(
    app_context, examination_id
):
    students = get_eligible_students(examination_id)
    timetables = Timetable.query.filter_by(
        examination_id=examination_id
    ).all()
    required = len(students) * len(timetables)

    allocations = _hall_allocations(examination_id)
    allocated = sum(a.allocated_capacity for a in allocations)

    assert allocated >= required


def test_all_hall_allocations_belong_to_examination(
    app_context, examination_id
):
    for a in _hall_allocations(examination_id):
        assert a.examination_id == examination_id


def test_no_hall_allocation_exceeds_hall_capacity(
    app_context, examination_id
):
    for a in _hall_allocations(examination_id):
        assert a.allocated_capacity > 0
        assert a.allocated_capacity <= a.hall.examination_capacity


def test_allocated_halls_are_active_and_available(
    app_context, examination_id
):
    for a in _hall_allocations(examination_id):
        assert a.hall.is_active
        assert a.hall.is_available
        assert not a.hall.is_under_maintenance


def test_no_duplicate_hall_for_same_timetable(
    app_context, examination_id
):
    keys = [
        (a.timetable_id, a.hall_id)
        for a in _hall_allocations(examination_id)
    ]
    assert len(keys) == len(set(keys))

def test_mixed_course_seating_has_no_avoidable_large_blocks(
    app_context, examination_id
):
    generate_allocation(
        examination_id,
        force=True
    )

    seats = _seats(examination_id)

    tested = False

    for timetable in Timetable.query.filter_by(
        examination_id=examination_id
    ).all():

        timetable_seats = [
            seat
            for seat in seats
            if seat.timetable_id == timetable.id
        ]

        for hall_id in {
            seat.hall_id
            for seat in timetable_seats
        }:

            hall_seats = sorted(
                [
                    seat
                    for seat in timetable_seats
                    if seat.hall_id == hall_id
                ],
                key=lambda seat: (
                    seat.seat_index,
                    seat.id,
                )
            )

            sequence = [
                seat.student.course_id
                for seat in hall_seats
                if seat.student and seat.student.course_id
            ]

            if len(set(sequence)) != 2:
                continue

            tested = True

            counts = {}

            for course_id in sequence:
                counts[course_id] = (
                    counts.get(course_id, 0) + 1
                )

            smaller = min(counts.values())
            larger = max(counts.values())

            allowed_max_run = (
                (larger + smaller - 1)
                // smaller
            )

            max_run = 1
            current_run = 1

            for index in range(1, len(sequence)):
                if sequence[index] == sequence[index - 1]:
                    current_run += 1
                    max_run = max(
                        max_run,
                        current_run
                    )
                else:
                    current_run = 1

            assert max_run <= allowed_max_run

    if not tested:
        pytest.skip(
            "No two-course hall was available for the "
            "mixed-course distribution test"
        )

# ============================================================
# 7B — Accessibility
# ============================================================

def test_accessibility_allocation(app_context, examination_id):
    generate_allocation(examination_id, force=True)

    students = get_eligible_students(examination_id)
    accessibility_students = [
        s for s in students
        if s.disability and str(s.disability).strip()
    ]

    if not accessibility_students:
        pytest.skip(
            "No accessibility students are present in the current dataset"
        )
    
    allocations = _hall_allocations(examination_id)
    accessible_hall_ids = {
        a.hall.id
        for a in allocations
        if a.hall.is_accessible and a.hall.floor_no == 0
    }
    assert accessible_hall_ids

    seats = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).all()

    for student in accessibility_students:
        student_hall_ids = {
            seat.hall_id for seat in seats
            if seat.student_id == student.id
        }
        assert student_hall_ids.issubset(accessible_hall_ids), (
            f"Accessibility student {student.student_id} "
            "not placed only in accessible halls"
        )

def test_accessibility_tamper_is_detected(
    app_context, examination_id
):
    from app.models.hall import Hall

    generate_allocation(examination_id, force=True)

    students = get_eligible_students(examination_id)

    accessibility_student = next(
        (
            s for s in students
            if s.disability and str(s.disability).strip()
        ),
        None,
    )

    if accessibility_student is None:
        pytest.skip(
            "No accessibility student is present in the current dataset"
        )

    seat = (
        SeatAllocation.query
        .filter_by(
            examination_id=examination_id,
            student_id=accessibility_student.id,
        )
        .first()
    )
    assert seat is not None

    # Find a usable hall that is not accessible.
    # This creates a controlled tamper scenario even when
    # the normal generated allocation contains only accessible
    # halls for the accessibility student.
    non_accessible_hall = (
        Hall.query
        .filter(
            Hall.is_active.is_(True),
            Hall.is_available.is_(True),
            Hall.is_under_maintenance.is_(False),
            Hall.is_accessible.is_(False),
        )
        .order_by(Hall.id.asc())
        .first()
    )

    if non_accessible_hall is None:
        pytest.skip(
            "No non-accessible hall is available to construct "
            "the accessibility tamper scenario"
        )

    timetable_id = seat.timetable_id
    original_hall_id = seat.hall_id
    created_allocation = None

    try:
        # Move the accessibility student's seat to the
        # non-accessible hall.
        seat.hall_id = non_accessible_hall.id

        # Ensure the target hall is allocated to this
        # examination/timetable so the validator evaluates
        # the accessibility rule rather than only reporting
        # an unallocated-hall error.
        allocation = (
            HallAllocation.query
            .filter_by(
                examination_id=examination_id,
                timetable_id=timetable_id,
                hall_id=non_accessible_hall.id,
            )
            .first()
        )

        if allocation is None:
            allocation = HallAllocation(
                examination_id=examination_id,
                timetable_id=timetable_id,
                hall_id=non_accessible_hall.id,
                allocated_capacity=1,
                purpose="NORMAL",
                status="GENERATED",
            )
            db.session.add(allocation)
            created_allocation = allocation

        db.session.commit()

        result = validate_allocation(examination_id)

        assert result.get("status") == "INVALID", (
            "Accessibility student placed in a non-accessible "
            "hall must be rejected by the validator"
        )

    finally:
        seat.hall_id = original_hall_id

        if created_allocation is not None:
            db.session.delete(created_allocation)

        db.session.commit()

    assert validate_allocation(
        examination_id
    ).get("status") == "VALID"

# ============================================================
# 7C — Seat allocation
# ============================================================

def _seats(examination_id):
    return SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).all()


def test_seat_count_matches_expected(app_context, examination_id):
    generate_allocation(examination_id, force=True)

    students = get_eligible_students(examination_id)
    timetables = Timetable.query.filter_by(
        examination_id=examination_id
    ).all()

    expected = len(students) * len(timetables)
    actual = len(_seats(examination_id))

    assert actual == expected


def test_no_duplicate_student_seat_per_timetable(
    app_context, examination_id
):
    keys = [
        (s.timetable_id, s.student_id)
        for s in _seats(examination_id)
    ]
    assert len(keys) == len(set(keys))


def test_no_seat_assigned_to_multiple_students(
    app_context, examination_id
):
    keys = [
        (s.timetable_id, s.hall_id, s.seat_number)
        for s in _seats(examination_id)
    ]
    assert len(keys) == len(set(keys))


def test_every_seat_belongs_to_valid_hall_allocation(
    app_context, examination_id
):
    allocation_keys = {
        (a.timetable_id, a.hall_id)
        for a in _hall_allocations(examination_id)
    }
    for seat in _seats(examination_id):
        assert (
            seat.timetable_id,
            seat.hall_id,
        ) in allocation_keys


def test_every_eligible_student_receives_a_seat(
    app_context, examination_id
):
    students = get_eligible_students(examination_id)
    student_ids = {s.id for s in students}

    seated_ids = {s.student_id for s in _seats(examination_id)}

    assert student_ids.issubset(seated_ids)

# ============================================================
# 7C.1 — Mixed-course seating
# ============================================================

def test_mixed_course_hall_seating_is_distributed(
    app_context, examination_id
):
    generate_allocation(
        examination_id,
        force=True
    )

    students = get_eligible_students(examination_id)

    courses = {
        student.course_id
        for student in students
        if student.course_id is not None
    }

    if len(courses) < 2:
        pytest.skip(
            "Current examination does not contain eligible "
            "students from at least two courses"
        )

    seats = _seats(examination_id)

    found_mixed_hall = False

    for timetable in Timetable.query.filter_by(
        examination_id=examination_id
    ).all():

        timetable_seats = [
            seat
            for seat in seats
            if seat.timetable_id == timetable.id
        ]

        halls = {
            seat.hall_id
            for seat in timetable_seats
        }

        for hall_id in halls:
            hall_seats = sorted(
                [
                    seat
                    for seat in timetable_seats
                    if seat.hall_id == hall_id
                ],
                key=lambda seat: (
                    seat.seat_index,
                    seat.id,
                )
            )

            hall_courses = [
                seat.student.course_id
                for seat in hall_seats
                if seat.student and seat.student.course_id
            ]

            if len(set(hall_courses)) < 2:
                continue

            found_mixed_hall = True

            # Confirm that the courses are not stored as one
            # contiguous block where avoidable.
            transitions = sum(
                1
                for index in range(1, len(hall_courses))
                if hall_courses[index] != hall_courses[index - 1]
            )

            assert transitions > 0

    if not found_mixed_hall:
        pytest.skip(
            "Current allocation did not place multiple courses "
            "in the same hall, so mixed-course seating could "
            "not be exercised"
        )

# ============================================================
# 7D — Allocation validation
# ============================================================

def test_allocation_validation_returns_valid(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("status") == "VALID", result


def test_allocation_validation_reports_no_errors(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("errors") == []


def test_allocation_validation_zero_unallocated(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("unallocated_students") == 0


# ============================================================
# 7D.1 — Per-hall capacity tamper
# ============================================================

def test_validation_detects_seat_capacity_overrun(
    app_context, examination_id
):
    allocation = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).first()
    assert allocation is not None

    seats_in_hall = SeatAllocation.query.filter_by(
        examination_id=examination_id,
        timetable_id=allocation.timetable_id,
        hall_id=allocation.hall_id,
    ).all()

    if not seats_in_hall:
        pytest.skip(
            "Selected hall allocation has no seats to perform capacity tamper test"
        )

    original_capacity = allocation.allocated_capacity
    try:
        allocation.allocated_capacity = max(
            0, len(seats_in_hall) - 1
        )
        db.session.commit()

        result = validate_allocation(examination_id)
        assert result.get("status") == "INVALID"
        assert any(
            "capacity" in str(e).lower()
            for e in result.get("errors", [])
        )
    finally:
        allocation.allocated_capacity = original_capacity
        db.session.commit()

    assert validate_allocation(examination_id).get("status") == "VALID"

# ============================================================
# 7D.2 — Hall allocation lifecycle mutation guards
# ============================================================

def test_approved_hall_allocation_mutation_is_rejected(
    app_context, examination_id
):
    from app.services.allocation import update_hall_allocation

    examination = db.session.get(Examination, examination_id)
    allocation = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).first()

    assert examination is not None
    assert allocation is not None

    original_status = examination.status

    try:
        examination.status = "APPROVED"
        db.session.commit()

        result = update_hall_allocation(
            allocation.id,
            allocation.hall_id,
            allocation.allocated_capacity,
            allocation.purpose,
        )

        assert result.get("success") is False
    finally:
        examination.status = original_status
        db.session.commit()


def test_published_hall_allocation_mutation_is_rejected(
    app_context, examination_id
):
    from app.services.allocation import update_hall_allocation

    examination = db.session.get(Examination, examination_id)
    allocation = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).first()

    assert examination is not None
    assert allocation is not None

    original_status = examination.status

    try:
        examination.status = "PUBLISHED"
        db.session.commit()

        result = update_hall_allocation(
            allocation.id,
            allocation.hall_id,
            allocation.allocated_capacity,
            allocation.purpose,
        )

        assert result.get("success") is False
    finally:
        examination.status = original_status
        db.session.commit()

# ============================================================
# 7E — Duplicate generation protection
# ============================================================

def test_duplicate_generation_without_force_is_rejected(
    app_context, examination_id
):
    result = generate_allocation(examination_id, force=False)
    assert result.get("success") is False


# ============================================================
# 7F — Force regeneration
# ============================================================

def test_force_regeneration_succeeds(
    app_context, examination_id
):
    result = generate_allocation(examination_id, force=True)
    assert result.get("success") is True


def test_force_regeneration_leaves_no_unallocated(
    app_context, examination_id
):
    result = generate_allocation(examination_id, force=True)
    assert result.get("unallocated_students") == 0


# ============================================================
# 7G — Regeneration integrity
# ============================================================

def test_regeneration_does_not_accumulate_hall_allocations(
    app_context, examination_id
):
    before = len(_hall_allocations(examination_id))
    generate_allocation(examination_id, force=True)
    after = len(_hall_allocations(examination_id))
    assert after == before


def test_regeneration_does_not_accumulate_seats(
    app_context, examination_id
):
    before = len(_seats(examination_id))
    generate_allocation(examination_id, force=True)
    after = len(_seats(examination_id))
    assert after == before


def test_regenerated_seats_have_no_duplicate_students(
    app_context, examination_id
):
    keys = [
        (s.timetable_id, s.student_id)
        for s in _seats(examination_id)
    ]
    assert len(keys) == len(set(keys))


def test_regenerated_seats_have_no_duplicate_seats(
    app_context, examination_id
):
    keys = [
        (s.timetable_id, s.hall_id, s.seat_number)
        for s in _seats(examination_id)
    ]
    assert len(keys) == len(set(keys))

def test_force_seat_regeneration_is_deterministic(
    app_context, examination_id
):
    generate_allocation(examination_id, force=True)

    original_seat_map = sorted(
        (
            seat.timetable_id,
            seat.student_id,
            seat.hall_id,
            seat.seat_number,
        )
        for seat in _seats(examination_id)
    )

    generate_allocation(examination_id, force=True)

    regenerated_seats = _seats(examination_id)

    regenerated_seat_map = sorted(
        (
            seat.timetable_id,
            seat.student_id,
            seat.hall_id,
            seat.seat_number,
        )
        for seat in regenerated_seats
    )

    assert regenerated_seat_map == original_seat_map  

def test_mixed_course_pattern_is_deterministic(
    app_context, examination_id
):
    generate_allocation(
        examination_id,
        force=True
    )

    def course_pattern():
        return sorted(
            (
                seat.timetable_id,
                seat.hall_id,
                seat.seat_number,
                (
                    seat.student.course_id
                    if seat.student
                    else None
                ),
            )
            for seat in _seats(examination_id)
        )

    before = course_pattern()

    generate_allocation(
        examination_id,
        force=True
    )

    after = course_pattern()

    assert after == before

def test_mixed_course_tamper_is_detected(
    app_context, examination_id
):
    generate_allocation(
        examination_id,
        force=True
    )

    seats = _seats(examination_id)

    target_hall = None
    hall_seats = []

    for timetable in Timetable.query.filter_by(
        examination_id=examination_id
    ).all():

        current = [
            seat
            for seat in seats
            if (
                seat.timetable_id == timetable.id
            )
        ]

        for hall_id in {
            seat.hall_id
            for seat in current
        }:

            candidate = sorted(
                [
                    seat
                    for seat in current
                    if seat.hall_id == hall_id
                ],
                key=lambda seat: (
                    seat.seat_index,
                    seat.id,
                )
            )
            course_counts = {}

            for seat in candidate:
                if seat.student and seat.student.course_id is not None:
                    course_id = seat.student.course_id
                    course_counts[course_id] = (
                        course_counts.get(course_id, 0) + 1
                    )

            if len(course_counts) == 2:
                values = sorted(course_counts.values())

                smaller_count = values[0]
                larger_count = values[1]

                allowed_max_run = (
                    (larger_count + smaller_count - 1)
                    // smaller_count
                )

                # Only select a hall where grouping the two courses
                # together will actually violate the mixed-course rule.
                if larger_count > allowed_max_run:
                    target_hall = hall_id
                    hall_seats = candidate
                    break
        if target_hall is not None:
            break

    if not hall_seats:
        pytest.skip(
            "No two-course hall available for mixed-course "
            "tamper test"
        )

    grouped = {}

    for seat in hall_seats:
        course_id = (
            seat.student.course_id
            if seat.student
            else None
        )

        grouped.setdefault(course_id, []).append(seat)

    groups = list(grouped.values())

    if len(groups) != 2 or not groups[0] or not groups[1]:
        pytest.skip(
            "Unable to construct a two-course tamper scenario"
        )

    original_students = [
        seat.student_id
        for seat in hall_seats
    ]

    try:
        # Deliberately create a contiguous course block.
        reordered_students = (
            [seat.student_id for seat in groups[0]]
            + [seat.student_id for seat in groups[1]]
        )

        for seat, student_id in zip(
            hall_seats,
            reordered_students
        ):
            seat.student_id = student_id

        db.session.commit()

        result = validate_allocation(
            examination_id
        )

        assert result.get("status") == "INVALID"

    finally:
        for seat, student_id in zip(
            hall_seats,
            original_students
        ):
            seat.student_id = student_id

        db.session.commit()

    assert (
        validate_allocation(
            examination_id
        ).get("status")
        == "VALID"
    )

# ============================================================
# 7H — Final end-to-end validation
# ============================================================

def test_final_validation_status_is_valid(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("status") == "VALID"


def test_final_validation_has_no_errors(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("errors") == []


def test_final_validation_zero_unallocated(
    app_context, examination_id
):
    result = validate_allocation(examination_id)
    assert result.get("unallocated_students") == 0

# ============================================================
# 7I — Optimization determinism + non-regression (Feature 17)
# ============================================================

def test_optimization_halls_used_is_deterministic(
    app_context, examination_id
):
    first = generate_allocation(examination_id, force=True)
    assert first.get("success") is True, first
    first_halls = first.get("halls_used")

    second = generate_allocation(examination_id, force=True)
    assert second.get("success") is True, second
    second_halls = second.get("halls_used")

    assert first_halls == second_halls
    assert first_halls > 0


def test_optimization_does_not_increase_halls_used(
    app_context, examination_id
):
    """
    Non-regression guard: the optimizer must never use more
    halls than the naive capacity-descending greedy would.

    The naive count is computed inline from the same inputs
    the optimizer sees (eligible students + available halls
    per timetable), so this test is self-contained.
    """
    from app.models.timetable import Timetable
    from app.services.eligibility import get_eligible_students
    from app.services.allocation import get_available_halls

    result = generate_allocation(examination_id, force=True)
    assert result.get("success") is True, result

    optimized_halls = result.get("halls_used")

    students = get_eligible_students(examination_id)
    total_students = len(students)

    naive_halls = 0

    for timetable in Timetable.query.filter_by(
        examination_id=examination_id
    ).all():
        available = get_available_halls(timetable)
        # Naive strategy: capacity-descending, one pass.
        available = sorted(
            available,
            key=lambda h: (-h.examination_capacity, h.id)
        )

        remaining = total_students
        for hall in available:
            if remaining <= 0:
                break
            remaining -= min(
                hall.examination_capacity, remaining
            )
            naive_halls += 1

    assert optimized_halls <= naive_halls, (
        f"Optimizer used {optimized_halls} halls, "
        f"naive would use {naive_halls}"
    )

# ============================================================
# 8 — Sample student → hall → seat
# ============================================================

def test_sample_seat_has_valid_student_hall_seat(
    app_context, examination_id
):
    sample = (
        SeatAllocation.query
        .filter_by(examination_id=examination_id)
        .first()
    )
    assert sample is not None
    assert sample.student is not None
    assert sample.hall is not None
    assert sample.seat_number

# ============================================================
# Coverage extension for app/services/allocation.py
#
# The Phase A coverage report flagged the failure paths in
# generate_allocation() and _plan_hall_allocations() (lines
# 758–952) as unexercised. These tests close the gap for the
# option-validation and excluded-hall_ids contracts, and prove
# that failures leave no partial state behind.
# ============================================================

from app.services.allocation import generate_allocation
from app.models.hall import Hall
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation
from app.models.examination import Examination


def test_generate_allocation_rejects_unknown_option_key(
    app_context, examination_id
):
    """
    An allocation_options dict with a key outside the closed
    schema must be rejected immediately — never silently
    ignored, never passed through to the planner.
    """
    result = generate_allocation(
        examination_id,
        force=True,
        allocation_options={"teleport_students": True},
    )

    assert result["success"] is False
    assert "unsupported allocation option" in result["message"].lower()
    assert "teleport_students" in result["message"]


def test_generate_allocation_rejects_non_boolean_option_value(
    app_context, examination_id
):
    """
    Every option value must be a bool. A string or int must be
    rejected with a message naming the offending key.
    """
    result = generate_allocation(
        examination_id,
        force=True,
        allocation_options={"minimize_halls": "yes"},
    )

    assert result["success"] is False
    assert "minimize_halls" in result["message"]
    assert "boolean" in result["message"].lower()


def test_generate_allocation_rejects_non_integer_excluded_hall_ids(
    app_context, examination_id
):
    """
    excluded_hall_ids must be integers; strings that don't parse
    must return a clean error instead of silently excluding nothing.
    """
    result = generate_allocation(
        examination_id,
        force=True,
        excluded_hall_ids=["not-a-number"],
    )

    assert result["success"] is False
    assert "excluded_hall_ids" in result["message"]


def test_generate_allocation_rejects_unknown_examination(
    app_context
):
    """A nonexistent examination id fails fast."""
    result = generate_allocation(999999999, force=True)

    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_excluded_hall_ids_does_not_touch_hall_row(
    app_context, examination_id
):
    """
    Passing a hall id via excluded_hall_ids must NOT change the
    Hall row. The exclusion is transient, in-memory only.

    The service docstring is explicit about this — the test
    holds it to that contract.
    """
    hall = (
        Hall.query
        .filter(Hall.is_active.is_(True))
        .first()
    )
    if hall is None:
        pytest.skip("no active hall to exclude")

    before = {
        "id": hall.id,
        "name": hall.name,
        "is_active": hall.is_active,
        "is_available": hall.is_available,
        "is_under_maintenance": hall.is_under_maintenance,
        "examination_capacity": hall.examination_capacity,
    }

    # Run the allocator with the hall transiently excluded.
    # Regardless of whether the plan succeeds, the Hall row must
    # be unchanged.
    generate_allocation(
        examination_id,
        force=True,
        excluded_hall_ids=[hall.id],
    )

    db.session.refresh(hall)
    after = {
        "id": hall.id,
        "name": hall.name,
        "is_active": hall.is_active,
        "is_available": hall.is_available,
        "is_under_maintenance": hall.is_under_maintenance,
        "examination_capacity": hall.examination_capacity,
    }

    assert before == after


def test_failed_plan_does_not_partially_mutate_allocation_tables(
    app_context, examination_id
):
    """
    Force a planner failure by excluding every active hall. The
    planner must fail before persisting; HallAllocation and
    SeatAllocation row counts for this examination must be
    unchanged from before the call.

    Uses force=True on purpose: even the cleanup path (which
    deletes prior rows) must roll back on planner failure.
    """
    active_hall_ids = [
        row.id
        for row in Hall.query.filter(Hall.is_active.is_(True)).all()
    ]
    if not active_hall_ids:
        pytest.skip("no active halls to exclude")

    before_hall = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    before_seat = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).count()

    result = generate_allocation(
        examination_id,
        force=True,
        excluded_hall_ids=active_hall_ids,
    )

    assert result["success"] is False, (
        "excluding every active hall must fail the plan"
    )

    after_hall = HallAllocation.query.filter_by(
        examination_id=examination_id
    ).count()
    after_seat = SeatAllocation.query.filter_by(
        examination_id=examination_id
    ).count()

    assert after_hall == before_hall, (
        f"HallAllocation count changed on failure: "
        f"{before_hall} → {after_hall}"
    )
    assert after_seat == before_seat, (
        f"SeatAllocation count changed on failure: "
        f"{before_seat} → {after_seat}"
    )


def test_allocation_options_none_is_equivalent_to_omitted(
    app_context, examination_id
):
    """
    Passing allocation_options=None must be byte-identical to
    passing no options at all — same success flag, same shape.
    """
    a = generate_allocation(
        examination_id, force=True, allocation_options=None
    )
    b = generate_allocation(examination_id, force=True)

    # Both must succeed (or both fail the same way) and agree on
    # the top-level keys that describe the outcome.
    assert a["success"] == b["success"]
    if a["success"]:
        assert a["eligible_students"] == b["eligible_students"]
        assert a["halls_used"] == b["halls_used"]
        assert a["allocated_capacity"] == b["allocated_capacity"]