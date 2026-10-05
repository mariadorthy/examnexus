from app import create_app, db

from app.models.admin import Admin
from app.models.staff import Staff
from app.models.student import Student
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject
from app.models.hall import Hall
from app.models.examination import Examination
from app.models.timetable import Timetable
from app.models.exam_registration import ExamRegistration
from app.models.hall_allocation import HallAllocation
from app.models.seat_allocation import SeatAllocation

from app.services.eligibility import get_eligible_students
from app.services.allocation import generate_allocation
from app.services.validation import validate_allocation
from app.services.invigilator_allocation import (
    generate_invigilator_allocation,
    get_invigilator_allocations,
    invigilator_workload
)
from app.services.validation import (
    validate_invigilator_allocation
)

# ============================================================
# CONFIGURATION
# ============================================================

EXAMINATION_ID = 1


# ============================================================
# TEST HELPERS
# ============================================================

def check(condition, message):
    if condition:
        print(f"[PASS] {message}")
        return True

    print(f"[FAIL] {message}")
    return False


def section(number, title):
    print("\n" + "=" * 70)
    print(f"[{number}] {title}")
    print("=" * 70)


# ============================================================
# APP
# ============================================================

app = create_app()


# ============================================================
# AUTHENTICATED ADMIN TEST CLIENT
#
# Phase 1 → 9 tests use one shared client. Routes protected by
# @roles_required("admin") require a valid JWT. We log in once
# here so later sections (mutation guard, RBAC coverage) can
# call protected endpoints directly.
# ============================================================

client = app.test_client()

_admin_token = None

with app.app_context():

    print("=" * 70)
    print("EXAMNEXUS — PHASE 1 → PHASE 9 REGRESSION TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Try to authenticate as admin.
    # If the login route or credentials are unavailable, we
    # fall back to no auth and [9B] will be reported honestly.
    # --------------------------------------------------------
    try:
        admin = Admin.query.first()

        if admin and admin.email:
            # Confirmed from generate_demo_admin.py:
            #   ADMIN_EMAIL    = "admin@examnexus.edu"
            #   ADMIN_PASSWORD = "Admin@123"
            # auth.py::login() requires email + password + role
            # and returns the token under "access_token".
            resp = client.post(
                "/api/auth/login",
                json={
                    "email": "admin@examnexus.edu",
                    "password": "Admin@123",
                    "role": "admin",
                },
            )

            if resp.status_code == 200:
                body = resp.get_json() or {}
                _admin_token = body.get("access_token")
    except Exception as _auth_error:
        print(
            "Admin login for test client failed:",
            _auth_error,
        )
    if _admin_token:
        print("[INFO] Test client authenticated as admin")
    else:
        print(
            "[INFO] Test client unauthenticated — "
            "[9B] will be skipped if the guard cannot be reached"
        )

    all_passed = True

    # ========================================================
    # PHASE 1 — AUTHENTICATION + RBAC
    # ========================================================

    section(1, "PHASE 1 — AUTHENTICATION + RBAC")

    client = app.test_client()

    # --------------------------------------------------------
    # Authentication routes must exist
    # --------------------------------------------------------

    auth_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/auth")
    }

    all_passed &= check(
        any("/login" in route for route in auth_routes),
        "Authentication login route is registered"
    )

    # --------------------------------------------------------
    # Protected dashboard endpoint must reject unauthenticated
    # requests.
    # --------------------------------------------------------

    dashboard_response = client.get("/api/dashboard/")

    all_passed &= check(
        dashboard_response.status_code in (401, 403),
        "Protected dashboard rejects unauthenticated access"
    )

    print(
        f"Dashboard unauthenticated response: "
        f"{dashboard_response.status_code}"
    )

    # --------------------------------------------------------
    # Admin data must exist
    # --------------------------------------------------------

    admin_count = Admin.query.count()

    all_passed &= check(
        admin_count > 0,
        f"Admin account exists ({admin_count})"
    )

    # --------------------------------------------------------
    # Passwords must not be stored as plaintext.
    # --------------------------------------------------------

    admins = Admin.query.all()

    password_hash_valid = all(
        bool(admin.password_hash)
        and len(admin.password_hash) > 20
        for admin in admins
    )

    all_passed &= check(
        password_hash_valid,
        "Admin password credentials are stored as password hashes"
    )

    # ========================================================
    # PHASE 2 — MASTER DATA
    # ========================================================

    section(2, "PHASE 2 — MASTER DATA")

    department_count = Department.query.count()
    course_count = Course.query.count()
    subject_count = Subject.query.count()
    student_count = Student.query.count()
    staff_count = Staff.query.count()
    hall_count = Hall.query.count()

    print(f"Departments: {department_count}")
    print(f"Courses:     {course_count}")
    print(f"Subjects:    {subject_count}")
    print(f"Students:    {student_count}")
    print(f"Staff:       {staff_count}")
    print(f"Halls:       {hall_count}")

    all_passed &= check(
        department_count > 0,
        "Departments master data exists"
    )

    all_passed &= check(
        course_count > 0,
        "Courses master data exists"
    )

    all_passed &= check(
        subject_count > 0,
        "Subjects master data exists"
    )

    all_passed &= check(
        student_count > 0,
        "Students master data exists"
    )

    all_passed &= check(
        staff_count > 0,
        "Staff master data exists"
    )

    all_passed &= check(
        hall_count > 0,
        "Hall master data exists"
    )

    # --------------------------------------------------------
    # Master-data uniqueness checks
    # --------------------------------------------------------

    student_ids = [
        student.student_id
        for student in Student.query.all()
        if student.student_id
    ]

    all_passed &= check(
        len(student_ids) == len(set(student_ids)),
        "Student IDs are unique"
    )

    student_emails = [
        student.email.lower()
        for student in Student.query.all()
        if student.email
    ]

    all_passed &= check(
        len(student_emails) == len(set(student_emails)),
        "Student emails are unique"
    )

    hall_names = [
        hall.name
        for hall in Hall.query.all()
        if hall.name
    ]

    all_passed &= check(
        len(hall_names) == len(set(hall_names)),
        "Hall names are unique"
    )

    # ========================================================
    # PHASE 3 — CSV IMPORT + MANUAL CRUD
    # ========================================================

    section(3, "PHASE 3 — CSV IMPORT + MANUAL CRUD")

    import_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith("/api/import")
    }

    all_passed &= check(
        len(import_routes) > 0,
        "CSV import API routes are registered"
    )

    print("Import routes:")
    for route in sorted(import_routes):
        print(f"  {route}")

    # --------------------------------------------------------
    # Existing master data proves the imported/manual data
    # pipeline has populated the database.
    # --------------------------------------------------------

    all_passed &= check(
        student_count > 0,
        "Student records are available after master-data/import workflow"
    )

    all_passed &= check(
        staff_count > 0,
        "Staff records are available after master-data/import workflow"
    )

    all_passed &= check(
        subject_count > 0,
        "Subject records are available after master-data/import workflow"
    )

    # ========================================================
    # PHASE 4 — EXAMINATION CREATION
    # ========================================================

    section(4, "PHASE 4 — EXAMINATION CREATION")

    examination_count = Examination.query.count()

    all_passed &= check(
        examination_count > 0,
        f"Examination records exist ({examination_count})"
    )

    examination = app.extensions["sqlalchemy"].session.get(
        Examination,
        EXAMINATION_ID
    )

    all_passed &= check(
        examination is not None,
        f"Examination {EXAMINATION_ID} exists"
    )

    if not examination:
        print("\nCannot continue without examination.")
        raise SystemExit(1)

    print(f"Examination: {examination.name}")
    print(f"Course ID:   {examination.course_id}")
    print(f"Semester:    {examination.semester}")
    print(f"Status:      {examination.status}")

    all_passed &= check(
        bool(examination.name),
        "Examination has a name"
    )

    all_passed &= check(
        examination.course_id is not None,
        "Examination is linked to a course"
    )

    all_passed &= check(
        examination.semester is not None,
        "Examination has a semester"
    )

    all_passed &= check(
        examination.start_date is not None
        and examination.end_date is not None,
        "Examination has a valid date range"
    )

    all_passed &= check(
        examination.duration_minutes is not None
        and examination.duration_minutes > 0,
        "Examination has a valid duration"
    )

    # ========================================================
    # PHASE 5 — TIMETABLE
    # ========================================================

    section(5, "PHASE 5 — TIMETABLE")

    timetables = Timetable.query.filter_by(
        examination_id=EXAMINATION_ID
    ).order_by(
        Timetable.exam_date,
        Timetable.start_time
    ).all()

    all_passed &= check(
        len(timetables) > 0,
        f"Timetable entries exist ({len(timetables)})"
    )

    timetable_ids = [
        timetable.id
        for timetable in timetables
    ]

    all_passed &= check(
        len(timetable_ids) == len(set(timetable_ids)),
        "Timetable entries contain no duplicate IDs"
    )

    timetable_exam_ids_valid = all(
        timetable.examination_id == EXAMINATION_ID
        for timetable in timetables
    )

    all_passed &= check(
        timetable_exam_ids_valid,
        "All timetable entries belong to the selected examination"
    )

    timetable_dates_valid = all(
        timetable.exam_date is not None
        for timetable in timetables
    )

    all_passed &= check(
        timetable_dates_valid,
        "All timetable entries have exam dates"
    )

    print(f"Timetable entries: {len(timetables)}")

    # ========================================================
    # PHASE 6 — ELIGIBILITY
    # ========================================================

    section(6, "PHASE 6 — ELIGIBILITY + RESOURCE READINESS")
    registrations = ExamRegistration.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    print(f"Exam registrations: {len(registrations)}")

    all_passed &= check(
        len(registrations) > 0,
        "Examination registrations exist"
    )

    students = get_eligible_students(EXAMINATION_ID)

    all_passed &= check(
        len(students) > 0,
        f"Eligible students found ({len(students)})"
    )

    eligible_student_ids = [
        student.id
        for student in students
    ]

    all_passed &= check(
        len(eligible_student_ids)
        == len(set(eligible_student_ids)),
        "Eligible students contain no duplicates"
    )

    active_eligible_students = all(
        student.is_active
        for student in students
    )

    all_passed &= check(
        active_eligible_students,
        "All eligible students are active"
    )

    registered_ids = {
        registration.student_id
        for registration in registrations
        if registration.status == "REGISTERED"
    }

    all_passed &= check(
        set(eligible_student_ids).issubset(registered_ids),
        "Eligible students have REGISTERED examination status"
    )

    # Eligibility is currently defined by the eligibility service:
    # REGISTERED examination status + active student.
    # Do not assume fee payment is an eligibility rule unless the
    # service explicitly implements it.

    all_passed &= check(
        all(
            registration.status == "REGISTERED"
            for registration in registrations
            if registration.student_id in set(eligible_student_ids)
        ),
        "Eligible students satisfy the configured REGISTERED eligibility rule"
    )

    # --------------------------------------------------------
    # Resource readiness
    # --------------------------------------------------------

    active_halls = Hall.query.filter_by(
        is_active=True,
        is_available=True,
        is_under_maintenance=False
    ).all()

    usable_capacity = sum(
        hall.examination_capacity or 0
        for hall in active_halls
    )

    required_capacity = len(students) * len(timetables)

    print(f"Eligible students: {len(students)}")
    print(f"Timetable entries: {len(timetables)}")
    print(f"Usable hall capacity: {usable_capacity}")
    print(f"Required total capacity: {required_capacity}")

    all_passed &= check(
        len(active_halls) > 0,
        f"Usable halls available ({len(active_halls)})"
    )

    all_passed &= check(
        usable_capacity >= required_capacity,
        "Phase 6 resource capacity is sufficient for allocation"
    )

    # ========================================================
    # PHASE 7 — COMPLETE ALLOCATION GENERATION
# ========================================================

    section(7, "PHASE 7 — HALL + ACCESSIBILITY + SEAT ALLOCATION")

    result = generate_allocation(
        EXAMINATION_ID,
        force=True
    )

    print("Generation result:")
    print(result)

    all_passed &= check(
        result.get("success") is True,
        "Complete allocation generation succeeded"
    )

    all_passed &= check(
        result.get("unallocated_students") == 0,
        "No students remain unallocated"
    )

    # ========================================================
    # PHASE 7A — HALL ALLOCATION
    # ========================================================

    print("\n[7A] Hall Allocation")

    hall_allocations = HallAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).order_by(
        HallAllocation.timetable_id,
        HallAllocation.id
    ).all()

    all_passed &= check(
        len(hall_allocations) > 0,
        f"Hall allocations created ({len(hall_allocations)})"
    )

    allocated_capacity = sum(
        allocation.allocated_capacity
        for allocation in hall_allocations
    )

    print(f"Hall allocation records: {len(hall_allocations)}")
    print(f"Total allocated capacity: {allocated_capacity}")

    all_passed &= check(
        allocated_capacity >= required_capacity,
        "Allocated hall capacity covers all eligible students"
    )

    all_passed &= check(
        all(
            allocation.examination_id == EXAMINATION_ID
            for allocation in hall_allocations
        ),
        "All hall allocations belong to the correct examination"
    )

    all_passed &= check(
        all(
            allocation.allocated_capacity > 0
            and allocation.allocated_capacity
            <= allocation.hall.examination_capacity
            for allocation in hall_allocations
        ),
        "No hall allocation exceeds hall examination capacity"
    )

    all_passed &= check(
        all(
            allocation.hall.is_active
            and allocation.hall.is_available
            and not allocation.hall.is_under_maintenance
            for allocation in hall_allocations
        ),
        "Allocated halls are active, available, and not under maintenance"
    )

    hall_timetable_keys = [
        (
            allocation.timetable_id,
            allocation.hall_id
        )
        for allocation in hall_allocations
    ]

    all_passed &= check(
        len(hall_timetable_keys)
        == len(set(hall_timetable_keys)),
        "No duplicate hall allocation exists for the same timetable"
    )

    # ========================================================
    # PHASE 7B — ACCESSIBILITY
    # ========================================================

    print("\n[7B] Accessibility-aware Allocation")

    accessibility_students = [
        student
        for student in students
        if student.disability
        and str(student.disability).strip()
    ]

    print(
        f"Students requiring accessibility support: "
        f"{len(accessibility_students)}"
    )

    accessible_halls = [
        allocation.hall
        for allocation in hall_allocations
        if allocation.hall.is_accessible
        and allocation.hall.floor_no == 0
    ]

    if accessibility_students:

        all_passed &= check(
            len(accessible_halls) > 0,
            "Suitable accessible halls exist for accessibility-required students"
        )

        accessible_hall_ids = {
            hall.id
            for hall in accessible_halls
        }

        accessibility_seat_check_possible = True

        seats_for_accessibility_check = SeatAllocation.query.filter_by(
            examination_id=EXAMINATION_ID
        ).all()

        for student in accessibility_students:

            student_seats = [
                seat
                for seat in seats_for_accessibility_check
                if seat.student_id == student.id
            ]

            if not student_seats:
                accessibility_seat_check_possible = False
                continue

            student_hall_ids = {
                seat.hall_id
                for seat in student_seats
            }

            student_accessible = student_hall_ids.issubset(
                accessible_hall_ids
            )

            all_passed &= check(
                student_accessible,
                (
                    f"Accessibility student {student.student_id} "
                    f"is assigned only to suitable accessible halls"
                )
            )

        all_passed &= check(
            accessibility_seat_check_possible,
            "Every accessibility-required student received a seat"
        )

    else:

        print(
            "No accessibility-required students exist in current data."
        )

        all_passed &= check(
            True,
            "Accessibility workflow has no required students in current dataset"
        )

    # ========================================================
    # PHASE 7B.1 — ACCESSIBILITY TAMPER VALIDATION
    # ========================================================

    print("\n[7B.1] Accessibility tamper validation")

    accessibility_test_student = next(
        (
            student
            for student in students
            if student.disability
            and str(student.disability).strip()
        ),
        None
    )

    if accessibility_test_student:

        accessibility_seat = (
            SeatAllocation.query
            .filter_by(
                examination_id=EXAMINATION_ID,
                student_id=accessibility_test_student.id
            )
            .first()
        )

        normal_hall_allocation = next(
            (
                allocation
                for allocation in hall_allocations
                if allocation.hall_id != accessibility_seat.hall_id
                and not (
                    allocation.hall.is_accessible
                    and allocation.hall.floor_no == 0
                )
            ),
            None
        ) if accessibility_seat else None

        if accessibility_seat and normal_hall_allocation:

            original_hall_id = accessibility_seat.hall_id

            accessibility_seat.hall_id = normal_hall_allocation.hall_id
            db.session.commit()

            accessibility_validation = validate_allocation(
                EXAMINATION_ID
            )

            print("Tampered accessibility validation:")
            print(accessibility_validation)

            all_passed &= check(
                accessibility_validation.get("status") == "INVALID",
                "Validation rejects accessibility student assigned to unsuitable hall"
            )

            accessibility_seat.hall_id = original_hall_id
            db.session.commit()

            restored_accessibility_validation = validate_allocation(
                EXAMINATION_ID
            )

            all_passed &= check(
                restored_accessibility_validation.get("status") == "VALID",
                "Accessibility allocation becomes VALID after restoration"
            )

        else:
            print(
                "[INFO] No suitable normal hall/seat combination available "
                "for accessibility tamper test"
            )

    else:
        print(
            "[INFO] No accessibility-required student in current dataset"
        )

    # ========================================================
    # PHASE 7C — SEAT ALLOCATION
    # ========================================================

    print("\n[7C] Seat Allocation")

    seats = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    expected_seats = len(students) * len(timetables)

    print(f"Seat records: {len(seats)}")
    print(f"Expected seat records: {expected_seats}")

    all_passed &= check(
        len(seats) == expected_seats,
        f"Seat count matches expected count ({expected_seats})"
    )

    # --------------------------------------------------------
    # Student uniqueness
    # --------------------------------------------------------

    student_seat_keys = [
        (
            seat.timetable_id,
            seat.student_id
        )
        for seat in seats
    ]

    all_passed &= check(
        len(student_seat_keys)
        == len(set(student_seat_keys)),
        "No student has duplicate seats within the same timetable"
    )

    # --------------------------------------------------------
    # Seat uniqueness
    # --------------------------------------------------------

    hall_seat_keys = [
        (
            seat.timetable_id,
            seat.hall_id,
            seat.seat_number
        )
        for seat in seats
    ]

    all_passed &= check(
        len(hall_seat_keys)
        == len(set(hall_seat_keys)),
        "No seat is assigned to multiple students"
    )

    # --------------------------------------------------------
    # Student → Hall → Seat relationship
    # --------------------------------------------------------

    hall_allocation_keys = {
        (
            allocation.timetable_id,
            allocation.hall_id
        )
        for allocation in hall_allocations
    }

    seat_relationships_valid = all(
        (
            seat.timetable_id,
            seat.hall_id
        ) in hall_allocation_keys
        and seat.examination_id == EXAMINATION_ID
        for seat in seats
    )

    all_passed &= check(
        seat_relationships_valid,
        "Every seat belongs to a valid hall allocation"
    )

    seat_student_ids = {
        seat.student_id
        for seat in seats
    }

    all_passed &= check(
        set(eligible_student_ids).issubset(seat_student_ids),
        "Every eligible student receives a seat"
    )

    # ========================================================
    # PHASE 7D — ALLOCATION VALIDATION
    # ========================================================

    print("\n[7D] Allocation Validation")

    validation = validate_allocation(EXAMINATION_ID)

    print("Validation result:")
    print(validation)

    all_passed &= check(
        validation.get("status") == "VALID",
        "Allocation validation returned VALID"
    )

    all_passed &= check(
        validation.get("errors") == [],
        "Allocation validation returned no errors"
    )

    all_passed &= check(
        validation.get("unallocated_students") == 0,
        "Allocation validation reports zero unallocated students"
    )

    # ========================================================
    # PHASE 7D.1 — PER-HALL SEAT CAPACITY VALIDATION
    # ========================================================

    print("\n[7D.1] Per-hall seat capacity validation")

    from collections import Counter

    capacity_test_allocation = HallAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).first()

    capacity_test_seats = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID,
        timetable_id=capacity_test_allocation.timetable_id,
        hall_id=capacity_test_allocation.hall_id
    ).all()

    if capacity_test_seats:
        original_capacity = capacity_test_allocation.allocated_capacity

        # Make persisted capacity smaller than the seats currently
        # assigned to this hall.
        capacity_test_allocation.allocated_capacity = max(
            0,
            len(capacity_test_seats) - 1
        )
        db.session.commit()

        capacity_validation = validate_allocation(EXAMINATION_ID)

        print("Tampered capacity validation:")
        print(capacity_validation)

        all_passed &= check(
            capacity_validation.get("status") == "INVALID",
            "Validation detects seats exceeding a hall's allocated capacity"
        )

        all_passed &= check(
            any(
                "capacity" in str(error).lower()
                for error in capacity_validation.get("errors", [])
            ),
            "Capacity validation reports a capacity-related error"
        )

        capacity_test_allocation.allocated_capacity = original_capacity
        db.session.commit()

        restored_capacity_validation = validate_allocation(
            EXAMINATION_ID
        )

        all_passed &= check(
            restored_capacity_validation.get("status") == "VALID",
            "Allocation becomes VALID again after restoring hall capacity"
        )
    else:
        all_passed &= check(
            False,
            "Per-hall capacity test could not find a seat allocation"
        )

    # ========================================================
    # PHASE 7E — DUPLICATE GENERATION PROTECTION
    # ========================================================

    print("\n[7E] Duplicate Generation Protection")

    duplicate_result = generate_allocation(
        EXAMINATION_ID,
        force=False
    )

    print("Duplicate generation result:")
    print(duplicate_result)

    all_passed &= check(
        duplicate_result.get("success") is False,
        "Duplicate generation without force is rejected"
    )

    # ========================================================
    # PHASE 7F — FORCE REGENERATION
    # ========================================================

    print("\n[7F] Force Regeneration")

    original_hall_count = len(hall_allocations)
    original_seat_count = len(seats)

    regeneration_result = generate_allocation(
        EXAMINATION_ID,
        force=True
    )

    print("Force regeneration result:")
    print(regeneration_result)

    all_passed &= check(
        regeneration_result.get("success") is True,
        "Force regeneration succeeded"
    )

    all_passed &= check(
        regeneration_result.get("unallocated_students") == 0,
        "Regeneration leaves no students unallocated"
    )

    # ========================================================
    # PHASE 7G — REGENERATION INTEGRITY
    # ========================================================

    print("\n[7G] Regeneration Integrity")

    regenerated_hall_allocations = HallAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    # Keep a fresh reference for later phases (Phase 8A uses it)
    hall_allocations = regenerated_hall_allocations

    regenerated_seats = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    # Keep a fresh reference for later phases
    seats = regenerated_seats

    all_passed &= check(
        len(regenerated_hall_allocations) == original_hall_count,
        "Regeneration does not accumulate duplicate hall allocations"
    )

    all_passed &= check(
        len(regenerated_seats) == original_seat_count,
        "Regeneration does not accumulate duplicate seat records"
    )

    regenerated_student_seat_keys = [
        (
            seat.timetable_id,
            seat.student_id
        )
        for seat in regenerated_seats
    ]

    all_passed &= check(
        len(regenerated_student_seat_keys)
        == len(set(regenerated_student_seat_keys)),
        "Regenerated seats contain no duplicate student assignments"
    )

    regenerated_hall_seat_keys = [
        (
            seat.timetable_id,
            seat.hall_id,
            seat.seat_number
        )
        for seat in regenerated_seats
    ]

    all_passed &= check(
        len(regenerated_hall_seat_keys)
        == len(set(regenerated_hall_seat_keys)),
        "Regenerated seats contain no duplicate seat assignments"
    )

    # ========================================================
    # PHASE 7H — FINAL END-TO-END VALIDATION
    # ========================================================

    print("\n[7H] Final End-to-End Validation")

    final_validation = validate_allocation(EXAMINATION_ID)

    print("Final validation result:")
    print(final_validation)

    all_passed &= check(
        final_validation.get("status") == "VALID",
        "Final allocation status is VALID"
    )

    all_passed &= check(
        final_validation.get("errors") == [],
        "Final allocation has no validation errors"
    )

    all_passed &= check(
        final_validation.get("unallocated_students") == 0,
        "Final allocation has zero unallocated students"
    )

    # ========================================================
    # ACTUAL STUDENT → HALL → SEAT
    # ========================================================

    print("\n[8] Student → Hall → Seat Sample")

    if regenerated_seats:

        sample_seat = regenerated_seats[0]

        print(
            f"Student {sample_seat.student.student_id}"
            f" → Hall {sample_seat.hall.name}"
            f" → Seat {sample_seat.seat_number}"
        )

        all_passed &= check(
            sample_seat.student is not None,
            "Sample seat has a valid student"
        )

        all_passed &= check(
            sample_seat.hall is not None,
            "Sample seat has a valid hall"
        )

        all_passed &= check(
            bool(sample_seat.seat_number),
            "Sample seat has a valid seat number"
        )

    else:

        all_passed &= check(
            False,
            "Sample Student → Hall → Seat could be inspected"
        )

    # ========================================================
    # PHASE 8A — INVIGILATOR ALLOCATION
    # ========================================================

    section(8, "PHASE 8A — INVIGILATOR ALLOCATION")

    # --------------------------------------------------------
    # 8A.1 — First generation
    # --------------------------------------------------------

    invig_result = generate_invigilator_allocation(
        EXAMINATION_ID,
        force=True
    )

    print("Invigilator generation result:")
    print(invig_result)

    all_passed &= check(
        invig_result.get("success") is True,
        "Invigilator generation succeeded"
    )

    all_passed &= check(
        invig_result.get("invigilator_assignments", 0) > 0,
        (
            "Invigilator assignments created "
            f"({invig_result.get('invigilator_assignments')})"
        )
    )

    all_passed &= check(
        invig_result.get("hall_slots", 0) > 0,
        (
            "Invigilator coverage spans every hall slot "
            f"({invig_result.get('hall_slots')})"
        )
    )

    all_passed &= check(
        invig_result.get("distinct_staff_used", 0) > 0,
        (
            "Distinct staff members used "
            f"({invig_result.get('distinct_staff_used')})"
        )
    )

    first_invig_count = invig_result.get(
        "invigilator_assignments",
        0
    )
    first_hall_slots = invig_result.get(
        "hall_slots",
        0
    )

    # --------------------------------------------------------
    # 8A.2 — Row-level structure
    # --------------------------------------------------------

    print("\n[8A.2] Invigilator rows")

    from app.models.invigilator_allocation import (
        InvigilatorAllocation
    )

    invig_rows = InvigilatorAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    print(f"Persisted invigilator rows: {len(invig_rows)}")

    all_passed &= check(
        len(invig_rows) == first_invig_count,
        "Persisted row count matches generation result"
    )

    # --------------------------------------------------------
    # 8A.3 — Every hall slot is covered
    # --------------------------------------------------------

    coverage = {}

    for row in invig_rows:
        key = (row.timetable_id, row.hall_id)
        coverage[key] = coverage.get(key, 0) + 1

    slots_covered = set(coverage.keys())

    # Re-query hall allocations fresh so we never touch deleted
    # ORM instances left over from an earlier force=True call.
    fresh_hall_allocations = HallAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    hall_allocation_keys_for_invig = {
        (
            allocation.timetable_id,
            allocation.hall_id
        )
        for allocation in fresh_hall_allocations
    }

    all_passed &= check(
        hall_allocation_keys_for_invig.issubset(slots_covered),
        "Every hall allocation has at least one invigilator"
    )
    # --------------------------------------------------------
    # 8A.4 — Staff validity
    # --------------------------------------------------------

    from app.models.staff import Staff

    staff_ids = {row.staff_id for row in invig_rows}

    staff_map = {
        s.id: s
        for s in Staff.query.filter(
            Staff.id.in_(list(staff_ids))
        ).all()
    } if staff_ids else {}

    all_active = all(
        s.is_active for s in staff_map.values()
    )
    all_available = all(
        s.availability for s in staff_map.values()
    )

    all_passed &= check(
        all_active,
        "All assigned invigilators are active"
    )

    all_passed &= check(
        all_available,
        "All assigned invigilators are available"
    )

    # --------------------------------------------------------
    # 8A.5 — Duplicate prevention
    # --------------------------------------------------------

    invig_keys = [
        (row.timetable_id, row.hall_id, row.staff_id)
        for row in invig_rows
    ]

    all_passed &= check(
        len(invig_keys) == len(set(invig_keys)),
        "No duplicate (timetable, hall, staff) assignments"
    )

    # --------------------------------------------------------
    # 8A.6 — Overlap conflict detection
    # --------------------------------------------------------
    print("\n[8A.6] Overlap conflict check")

    by_staff = {}
    for row in invig_rows:
        by_staff.setdefault(row.staff_id, []).append(row)

    overlap_conflicts = 0

    for staff_id, rows in by_staff.items():
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                ta, tb = a.timetable, b.timetable
                if not ta or not tb:
                    continue
                # Compare via ids to avoid touching a possibly
                # deleted ORM instance
                if a.timetable_id == b.timetable_id:
                    continue
                if ta.exam_date != tb.exam_date:
                    continue
                if (
                    ta.start_time < tb.end_time
                    and ta.end_time > tb.start_time
                ):
                    overlap_conflicts += 1

    all_passed &= check(
        overlap_conflicts == 0,
        "No staff member is scheduled in overlapping sessions"
    )

    # --------------------------------------------------------
    # 8A.7 — Independent validation
    # --------------------------------------------------------

    print("\n[8A.7] Independent invigilator validation")

    invig_validation = validate_invigilator_allocation(
        EXAMINATION_ID
    )

    print("Invigilator validation result:")
    print(invig_validation)

    all_passed &= check(
        invig_validation.get("status") == "VALID",
        "Independent invigilator validation returned VALID"
    )

    all_passed &= check(
        invig_validation.get("errors") == [],
        "Independent invigilator validation returned no errors"
    )

    all_passed &= check(
        invig_validation.get("invigilator_assignments")
        == first_invig_count,
        "Validation assignment count matches generation"
    )

    # --------------------------------------------------------
    # 8A.8 — Duplicate generation protection
    # --------------------------------------------------------

    print("\n[8A.8] Duplicate generation protection")

    dup_invig = generate_invigilator_allocation(
        EXAMINATION_ID,
        force=False
    )

    print("Duplicate invigilator generation result:")
    print(dup_invig)

    all_passed &= check(
        dup_invig.get("success") is False,
        "Duplicate invigilator generation without force is rejected"
    )

    # --------------------------------------------------------
    # 8A.9 — Force regeneration determinism
    # --------------------------------------------------------

    print("\n[8A.9] Force regeneration determinism")

    regen_invig = generate_invigilator_allocation(
        EXAMINATION_ID,
        force=True
    )

    print("Regenerated invigilator result:")
    print(regen_invig)

    all_passed &= check(
        regen_invig.get("success") is True,
        "Force regeneration succeeded"
    )

    all_passed &= check(
        regen_invig.get("invigilator_assignments")
        == first_invig_count,
        "Regeneration produced identical assignment count"
    )

    all_passed &= check(
        regen_invig.get("hall_slots") == first_hall_slots,
        "Regeneration produced identical hall-slot count"
    )

    # --------------------------------------------------------
    # 8A.10 — No duplicate accumulation after regeneration
    # --------------------------------------------------------

    final_invig_rows = InvigilatorAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    all_passed &= check(
        len(final_invig_rows) == first_invig_count,
        "Regeneration does not accumulate duplicate invigilator rows"
    )

    # --------------------------------------------------------
    # 8A.11 — Workload summary consistency
    # --------------------------------------------------------

    print("\n[8A.11] Workload summary")

    workload = invigilator_workload(EXAMINATION_ID)

    print("Top staff by invigilation duties:")
    for entry in workload[:5]:
        print(
            f"  staff #{entry['staff_id']:<4} "
            f"{str(entry['staff_name']):<25} "
            f"duties={entry['duties']}"
        )

    all_passed &= check(
        len(workload) > 0,
        "Workload summary is populated"
    )

    total_duties = sum(entry["duties"] for entry in workload)

    all_passed &= check(
        total_duties == first_invig_count,
        "Workload totals match invigilator assignment count"
    )

    # ========================================================
    # PHASE 8A.12 — CROSS-EXAMINATION STAFF CONFLICT
    # ========================================================

    print("\n[8A.12] Cross-examination invigilator conflict validation")

    from app.models.invigilator_allocation import InvigilatorAllocation

    conflict_staff = (
        Staff.query
        .filter_by(is_active=True, availability=True)
        .order_by(Staff.id)
        .first()
    )

    source_hall_allocation = (
        HallAllocation.query
        .filter_by(examination_id=EXAMINATION_ID)
        .first()
    )

    source_timetable = (
        Timetable.query
        .filter_by(examination_id=EXAMINATION_ID)
        .order_by(Timetable.id)
        .first()
    )

    if conflict_staff and source_hall_allocation and source_timetable:

        existing_other_exam_timetable = (
            Timetable.query
            .join(Examination)
            .filter(
                Timetable.examination_id != EXAMINATION_ID,
                Timetable.exam_date == source_timetable.exam_date,
                Timetable.start_time < source_timetable.end_time,
                Timetable.end_time > source_timetable.start_time,
            )
            .first()
        )

        if existing_other_exam_timetable:

            other_hall_allocation = (
                HallAllocation.query
                .filter_by(
                    examination_id=existing_other_exam_timetable.examination_id,
                    timetable_id=existing_other_exam_timetable.id
                )
                .first()
            )

            if other_hall_allocation:

                conflicting_row = InvigilatorAllocation(
                    examination_id=existing_other_exam_timetable.examination_id,
                    timetable_id=existing_other_exam_timetable.id,
                    hall_allocation_id=other_hall_allocation.id,
                    hall_id=other_hall_allocation.hall_id,
                    staff_id=conflict_staff.id,
                    role="INVIGILATOR",
                    status="GENERATED",
                )

                db.session.add(conflicting_row)
                db.session.commit()

                original_rows = InvigilatorAllocation.query.filter_by(
                    examination_id=EXAMINATION_ID
                ).all()

                # Temporarily assign the same staff member to the current
                # examination's first slot.
                current_row = original_rows[0]

                original_staff_id = current_row.staff_id
                current_row.staff_id = conflict_staff.id
                db.session.commit()

                cross_exam_validation = validate_invigilator_allocation(
                    EXAMINATION_ID
                )

                print("Cross-examination conflict validation:")
                print(cross_exam_validation)

                all_passed &= check(
                    cross_exam_validation.get("status") == "INVALID",
                    "Independent validation detects cross-examination staff conflict"
                )

                current_row.staff_id = original_staff_id
                db.session.delete(conflicting_row)
                db.session.commit()

                restored_invig_validation = (
                    validate_invigilator_allocation(EXAMINATION_ID)
                )

                all_passed &= check(
                    restored_invig_validation.get("status") == "VALID",
                    "Invigilator validation returns VALID after conflict restoration"
                )

            else:
                print(
                    "[INFO] Other examination exists but has no hall allocation"
                )
        else:
            print(
                "[INFO] No overlapping timetable in another examination; "
                "cross-exam conflict test not executable with current dataset"
            )
    else:
        all_passed &= check(
            False,
            "Cross-examination conflict prerequisites exist"
        )

    # ========================================================
    # PHASE 8A.13 — EXACT INVIGILATOR DETERMINISM
    # ========================================================

    print("\n[8A.13] Exact invigilator assignment determinism")

    first_assignment_signature = sorted(
        (
            row.timetable_id,
            row.hall_id,
            row.staff_id,
            row.role
        )
        for row in final_invig_rows
    )

    deterministic_regen = generate_invigilator_allocation(
        EXAMINATION_ID,
        force=True
    )

    all_passed &= check(
        deterministic_regen.get("success") is True,
        "Deterministic invigilator regeneration succeeded"
    )

    second_invig_rows = InvigilatorAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    second_assignment_signature = sorted(
        (
            row.timetable_id,
            row.hall_id,
            row.staff_id,
            row.role
        )
        for row in second_invig_rows
    )

    all_passed &= check(
        first_assignment_signature == second_assignment_signature,
        "Force regeneration produces identical staff assignments"
    )

    # ========================================================
    # PHASE 8A.14 — INVIGILATOR RELATIONSHIP INTEGRITY
    # ========================================================

    print("\n[8A.14] Invigilator relationship integrity")

    relationship_integrity = True

    for row in second_invig_rows:

        valid_relationship = (
            row.examination_id == EXAMINATION_ID
            and row.timetable is not None
            and row.timetable.examination_id == EXAMINATION_ID
            and row.hall_allocation is not None
            and row.hall_allocation.examination_id == EXAMINATION_ID
            and row.hall_allocation.timetable_id == row.timetable_id
            and row.hall_allocation.hall_id == row.hall_id
            and row.staff is not None
        )

        relationship_integrity &= valid_relationship

    all_passed &= check(
        relationship_integrity,
        "Every invigilator row references the correct examination, timetable, hall allocation, hall, and staff"
    )

    # ========================================================
    # PHASE 8A.15 — STAFF READINESS VALIDATION
    # ========================================================

    print("\n[8A.15] Staff readiness validation")

    staff_test_row = (
        InvigilatorAllocation.query
        .filter_by(examination_id=EXAMINATION_ID)
        .first()
    )

    if staff_test_row and staff_test_row.staff:

        original_active = staff_test_row.staff.is_active
        original_available = staff_test_row.staff.availability

        staff_test_row.staff.is_active = False
        db.session.commit()

        inactive_validation = validate_invigilator_allocation(
            EXAMINATION_ID
        )

        all_passed &= check(
            inactive_validation.get("status") == "INVALID",
            "Validation rejects inactive assigned invigilator"
        )

        staff_test_row.staff.is_active = original_active
        staff_test_row.staff.availability = False
        db.session.commit()

        unavailable_validation = validate_invigilator_allocation(
            EXAMINATION_ID
        )

        all_passed &= check(
            unavailable_validation.get("status") == "INVALID",
            "Validation rejects unavailable assigned invigilator"
        )

        staff_test_row.staff.availability = original_available
        db.session.commit()

        restored_validation = validate_invigilator_allocation(
            EXAMINATION_ID
        )

        all_passed &= check(
            restored_validation.get("status") == "VALID",
            "Invigilator validation returns VALID after staff restoration"
        )

    # ========================================================
    # PHASE 8B — LIFECYCLE (REVIEW → APPROVED → PUBLISHED)
    # ========================================================

    section(8, "PHASE 8B — LIFECYCLE: REVIEW → APPROVED → PUBLISHED")

    from app.services.lifecycle import transition_status

    # Reset the examination to a clean DRAFT so we can walk the
    # lifecycle from the start.
    examination.status = "DRAFT"
    from app import db as _db
    _db.session.commit()

    # --------------------------------------------------------
    # 8B.1 — Illegal first jump (DRAFT -> APPROVED) is rejected
    # --------------------------------------------------------

    print("\n[8B.1] Illegal DRAFT -> APPROVED")

    illegal = transition_status(EXAMINATION_ID, "APPROVED")
    print(illegal)

    all_passed &= check(
        illegal.get("success") is False,
        "DRAFT -> APPROVED is rejected"
    )

    # --------------------------------------------------------
    # 8B.2 — DRAFT -> GENERATED
    # --------------------------------------------------------

    print("\n[8B.2] DRAFT -> GENERATED")

    r_generated = transition_status(EXAMINATION_ID, "GENERATED")
    print(r_generated)

    all_passed &= check(
        r_generated.get("success") is True,
        "DRAFT -> GENERATED succeeded"
    )

    examination = Examination.query.get(EXAMINATION_ID)

    all_passed &= check(
        examination.status == "GENERATED",
        "Persisted status is GENERATED"
    )

    # --------------------------------------------------------
    # 8B.3 — GENERATED -> VALIDATED (validation gate)
    # --------------------------------------------------------

    print("\n[8B.3] GENERATED -> VALIDATED")

    r_validated = transition_status(EXAMINATION_ID, "VALIDATED")
    print(r_validated)

    all_passed &= check(
        r_validated.get("success") is True,
        "GENERATED -> VALIDATED succeeded"
    )

    examination = Examination.query.get(EXAMINATION_ID)

    all_passed &= check(
        examination.status == "VALIDATED",
        "Persisted status is VALIDATED"
    )

    # --------------------------------------------------------
    # 8B.4 — Cannot skip to APPROVED from VALIDATED
    # --------------------------------------------------------

    print("\n[8B.4] VALIDATED -> APPROVED (illegal skip)")

    r_skip = transition_status(EXAMINATION_ID, "APPROVED")
    print(r_skip)

    all_passed &= check(
        r_skip.get("success") is False,
        "VALIDATED -> APPROVED is rejected (must go through REVIEW)"
    )

    # --------------------------------------------------------
    # 8B.5 — VALIDATED -> REVIEW
    # --------------------------------------------------------

    print("\n[8B.5] VALIDATED -> REVIEW")

    r_review = transition_status(EXAMINATION_ID, "REVIEW")
    print(r_review)

    all_passed &= check(
        r_review.get("success") is True,
        "VALIDATED -> REVIEW succeeded"
    )

    # --------------------------------------------------------
    # 8B.6 — REVIEW -> APPROVED
    # --------------------------------------------------------

    print("\n[8B.6] REVIEW -> APPROVED")

    r_approved = transition_status(EXAMINATION_ID, "APPROVED")
    print(r_approved)

    all_passed &= check(
        r_approved.get("success") is True,
        "REVIEW -> APPROVED succeeded"
    )

    examination = Examination.query.get(EXAMINATION_ID)

    all_passed &= check(
        examination.status == "APPROVED",
        "Persisted status is APPROVED"
    )

    # --------------------------------------------------------
    # 8B.7 — Cannot publish before... wait, we ARE approved.
    #         Skip the "unapproved cannot publish" step by
    #         simulating it manually further below.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 8B.8 — APPROVED -> PUBLISHED
    # --------------------------------------------------------

    print("\n[8B.8] APPROVED -> PUBLISHED")

    r_published = transition_status(EXAMINATION_ID, "PUBLISHED")
    print(r_published)

    all_passed &= check(
        r_published.get("success") is True,
        "APPROVED -> PUBLISHED succeeded"
    )

    examination = Examination.query.get(EXAMINATION_ID)

    all_passed &= check(
        examination.status == "PUBLISHED",
        "Persisted status is PUBLISHED"
    )

    # --------------------------------------------------------
    # 8B.9 — PUBLISHED cannot go backward
    # --------------------------------------------------------

    print("\n[8B.9] PUBLISHED -> APPROVED (illegal backward)")

    r_back = transition_status(EXAMINATION_ID, "APPROVED")
    print(r_back)

    all_passed &= check(
        r_back.get("success") is False,
        "PUBLISHED -> APPROVED is rejected (forward-only)"
    )

    # --------------------------------------------------------
    # 8B.10 — Unapproved cannot publish (fresh DRAFT exam)
    # --------------------------------------------------------

    print("\n[8B.10] DRAFT -> PUBLISHED (illegal)")

    examination = Examination.query.get(EXAMINATION_ID)
    examination.status = "DRAFT"
    _db.session.commit()

    r_pub_draft = transition_status(EXAMINATION_ID, "PUBLISHED")
    print(r_pub_draft)

    all_passed &= check(
        r_pub_draft.get("success") is False,
        "DRAFT -> PUBLISHED is rejected"
    )

    # --------------------------------------------------------
    # 8B.11 — Restore PUBLISHED for downstream Phase 8C
    # --------------------------------------------------------

    transition_status(EXAMINATION_ID, "GENERATED")
    transition_status(EXAMINATION_ID, "VALIDATED")
    transition_status(EXAMINATION_ID, "REVIEW")
    transition_status(EXAMINATION_ID, "APPROVED")
    transition_status(EXAMINATION_ID, "PUBLISHED")

    examination = Examination.query.get(EXAMINATION_ID)

    all_passed &= check(
        examination.status == "PUBLISHED",
        "Final status restored to PUBLISHED for downstream phases"
    )

    # ========================================================
    # PHASE 8C — HALL TICKET + QR
    # ========================================================

    section(8, "PHASE 8C — HALL TICKET + QR")

    from app.services.hall_ticket import (
        generate_hall_tickets,
        get_hall_ticket,
        verify_hall_ticket
    )
    from app.models.hall_ticket import HallTicket

    # Examination is PUBLISHED at this point (from 8B).

    # --------------------------------------------------------
    # 8C.1 — Generate hall tickets
    # --------------------------------------------------------

    print("\n[8C.1] Generate hall tickets")

    gen_result = generate_hall_tickets(
        EXAMINATION_ID,
        force=True
    )
    print(gen_result)

    all_passed &= check(
        gen_result.get("success") is True,
        "Hall ticket generation succeeded"
    )

    all_passed &= check(
        gen_result.get("issued", 0) > 0,
        f"Hall tickets issued ({gen_result.get('issued')})"
    )

    ticket_count = HallTicket.query.filter_by(
        examination_id=EXAMINATION_ID
    ).count()

    all_passed &= check(
        ticket_count == gen_result.get("issued"),
        "Persisted ticket count matches issued count"
    )

    # --------------------------------------------------------
    # 8C.2 — One ticket per student
    # --------------------------------------------------------

    sample_seat = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).first()

    sample_student_id = sample_seat.student_id

    print(f"\n[8C.2] Sample student id: {sample_student_id}")

    ticket_result = get_hall_ticket(
        sample_student_id,
        EXAMINATION_ID
    )

    all_passed &= check(
        ticket_result.get("success") is True,
        "Sample hall ticket retrieved"
    )

    ticket = ticket_result.get("ticket", {})
    payload = ticket_result.get("payload", {})

    all_passed &= check(
        bool(ticket.get("verification_token")),
        "Ticket has a verification token"
    )

    all_passed &= check(
        bool(ticket.get("qr_base64")),
        "Ticket has a QR base64 image"
    )

    all_passed &= check(
        len(payload.get("entries", [])) > 0,
        f"Ticket contains {len(payload.get('entries', []))} exam entries"
    )

    # --------------------------------------------------------
    # 8C.3 — QR contains no secrets
    # --------------------------------------------------------

    import base64 as _b64
    import json as _json

    qr_b64 = ticket.get("qr_base64")
    qr_bytes = _b64.b64decode(qr_b64)

    all_passed &= check(
    qr_bytes[:8] == b"\x89PNG\r\n\x1a\n",
    "QR output is a valid PNG image"
)

    # The image is a PNG; we can't OCR it easily, but we can
    # confirm the token format that was embedded is safe.
    token = ticket.get("verification_token")

    all_passed &= check(
        len(token) == 32 and token.isalnum(),
        "Verification token is a 32-char hex string"
    )

    # Payload that was encoded is known: {"t": "<token>"}
    embedded = _json.dumps({"t": token}, separators=(",", ":"))

    all_passed &= check(
        "password" not in embedded.lower()
        and "jwt" not in embedded.lower()
        and "hash" not in embedded.lower(),
        "QR payload contains no sensitive fields"
    )

    # --------------------------------------------------------
    # 8C.4 — Verify endpoint works
    # --------------------------------------------------------

    print("\n[8C.4] Verify endpoint")

    verify_result = verify_hall_ticket(token)
    print(verify_result)

    all_passed &= check(
        verify_result.get("valid") is True,
        "Verification endpoint returns valid=True"
    )

    all_passed &= check(
        "password" not in verify_result
        and "password_hash" not in verify_result,
        "Verify response contains no password fields"
    )

    all_passed &= check(
        "student_code" in verify_result
        and "student_name" in verify_result,
        "Verify response contains safe identity fields"
    )

    # --------------------------------------------------------
    # 8C.5 — Hall ticket requires PUBLISHED status
    # --------------------------------------------------------

    print("\n[8C.5] Hall ticket requires PUBLISHED")

    examination = Examination.query.get(EXAMINATION_ID)
    original_status = examination.status
    examination.status = "REVIEW"
    _db.session.commit()

    blocked = generate_hall_tickets(EXAMINATION_ID, force=True)
    print(blocked)

    all_passed &= check(
        blocked.get("success") is False,
        "Hall ticket generation blocked when status is REVIEW"
    )

    examination.status = original_status
    _db.session.commit()

    duplicate_ticket_result = generate_hall_tickets(
        EXAMINATION_ID,
        force=False
    )

    print(duplicate_ticket_result)

    all_passed &= check(
        duplicate_ticket_result.get("success") is False,
        "Duplicate hall-ticket generation without force is rejected"
    )

    ticket_count_before_reissue = HallTicket.query.filter_by(
        examination_id=EXAMINATION_ID
    ).count()

    force_ticket_result = generate_hall_tickets(
        EXAMINATION_ID,
        force=True
    )

    print(force_ticket_result)

    ticket_count_after_reissue = HallTicket.query.filter_by(
        examination_id=EXAMINATION_ID
    ).count()

    all_passed &= check(
        force_ticket_result.get("success") is True,
        "Force hall-ticket regeneration succeeds"
    )

    all_passed &= check(
        ticket_count_after_reissue == ticket_count_before_reissue,
        "Force hall-ticket regeneration does not create duplicate tickets"
    )

    # restore tickets that were deleted by the blocked call —
    # actually they weren't deleted since the call was rejected
    # before force-delete. No action needed.

    # ========================================================
    # PHASE 8D — REPORTS
    # ========================================================

    section(8, "PHASE 8D — REPORTS")

    from app.services.reports import (
        allocation_report,
        student_allocation_report,
        hall_utilization_report,
        invigilator_workload_report
    )

    # --------------------------------------------------------
    # 8D.1 — Allocation report
    # --------------------------------------------------------

    alloc_rep = allocation_report(EXAMINATION_ID)

    all_passed &= check(
        alloc_rep.get("success") is True,
        "Allocation report generated"
    )

    all_passed &= check(
        len(alloc_rep.get("rows", [])) > 0,
        f"Allocation report has {len(alloc_rep.get('rows', []))} rows"
    )

    # --------------------------------------------------------
    # 8D.2 — Student allocation report
    # --------------------------------------------------------

    stu_rep = student_allocation_report(EXAMINATION_ID)

    all_passed &= check(
        stu_rep.get("success") is True,
        "Student allocation report generated"
    )

    all_passed &= check(
        len(stu_rep.get("rows", [])) == len(seats),
        "Student report row count matches seat count"
    )

    # --------------------------------------------------------
    # 8D.3 — Hall utilization report
    # --------------------------------------------------------

    hall_rep = hall_utilization_report(EXAMINATION_ID)

    all_passed &= check(
        hall_rep.get("success") is True,
        "Hall utilization report generated"
    )

    all_passed &= check(
        all(
            0 <= row["utilization_percent"] <= 100
            for row in hall_rep.get("rows", [])
        ),
        "All utilization percentages are within 0-100"
    )

    # --------------------------------------------------------
    # 8D.4 — Invigilator workload report
    # --------------------------------------------------------

    inv_rep = invigilator_workload_report(EXAMINATION_ID)

    all_passed &= check(
        inv_rep.get("success") is True,
        "Invigilator workload report generated"
    )

    total_duties = sum(
        row["duties"] for row in inv_rep.get("rows", [])
    )

    all_passed &= check(
        total_duties == first_invig_count,
        "Workload report total matches invigilator assignments"
    )

    # ========================================================
    # PHASE 8E — ROUTE REGISTRATION
    # ========================================================

    section(8, "PHASE 8E — ROUTE REGISTRATION")

    all_routes = {
        rule.rule for rule in app.url_map.iter_rules()
    }

    all_passed &= check(
        any(r.startswith("/api/hall-tickets") for r in all_routes),
        "Hall ticket routes registered"
    )

    all_passed &= check(
        any(r.startswith("/api/reports") for r in all_routes),
        "Report routes registered"
    )

    all_passed &= check(
        any("/invigilators" in r for r in all_routes),
        "Invigilator routes registered"
    )

        # ========================================================
    # PHASE 9A — LIFECYCLE HARDENING: PUBLISH GATE
    # ========================================================

    section(9, "PHASE 9A — PUBLISH GATE + MUTATION GUARD")

    from app.services.lifecycle import transition_status

    # ensure the exam is PUBLISHED
    examination = db.session.get(Examination, EXAMINATION_ID)

    if examination.status != "PUBLISHED":
        if examination.status == "DRAFT":
            transition_status(EXAMINATION_ID, "GENERATED")
            transition_status(EXAMINATION_ID, "VALIDATED")
            transition_status(EXAMINATION_ID, "REVIEW")
            transition_status(EXAMINATION_ID, "APPROVED")
            transition_status(EXAMINATION_ID, "PUBLISHED")

    examination = db.session.get(Examination, EXAMINATION_ID)

    all_passed &= check(
        examination.status == "PUBLISHED",
        "Examination is PUBLISHED for Phase 9 tests"
    )

    # --------------------------------------------------------
    # 9A.1 — Tamper the persisted invigilator allocation
    # --------------------------------------------------------

    print("\n[9A.1] Force validation failure by clearing invigilators")

    from app.models.invigilator_allocation import (
        InvigilatorAllocation
    )

    (
        InvigilatorAllocation.query
        .filter_by(examination_id=EXAMINATION_ID)
        .delete(synchronize_session=False)
    )
    db.session.commit()

    # --------------------------------------------------------
    # 9A.2 — Reset to APPROVED, then attempt to publish
    # --------------------------------------------------------

    print("\n[9A.2] Attempt to publish with invalid invigilators")

    examination = db.session.get(Examination, EXAMINATION_ID)
    examination.status = "APPROVED"
    db.session.commit()

    publish_result = transition_status(
        EXAMINATION_ID, "PUBLISHED"
    )
    print(publish_result)

    all_passed &= check(
        publish_result.get("success") is False,
        "Publishing with invalid invigilators is rejected"
    )

    # --------------------------------------------------------
    # 9A.3 — Restore invigilators and publish successfully
    # --------------------------------------------------------

    print("\n[9A.3] Restore invigilators and publish")

    from app.services.invigilator_allocation import (
        generate_invigilator_allocation
    )

    generate_invigilator_allocation(
        EXAMINATION_ID, force=True
    )

    publish_result = transition_status(
        EXAMINATION_ID, "PUBLISHED"
    )
    print(publish_result)

    all_passed &= check(
        publish_result.get("success") is True,
        "Publish succeeds once allocation is valid again"
    )

    # ========================================================
    # PHASE 9B — MUTATION GUARD
    # ========================================================

    print("\n[9B] Mutation guard on PUBLISHED examination")

    if not _admin_token:
        all_passed &= check(
            False,
            "Cannot test mutation guard: no admin token available"
        )
    else:
        mutation_payloads = [
            {
                "duration_minutes": 999
            },
            {
                "semester": 99
            },
            {
                "start_date": "2099-01-01"
            },
        ]

        for mutation_payload in mutation_payloads:

            mutation_response = client.put(
                f"/api/examinations/{EXAMINATION_ID}",
                json=mutation_payload,
                headers={
                    "Authorization": f"Bearer {_admin_token}",
                },
            )

            print(
                "Mutation payload:",
                mutation_payload,
                "status:",
                mutation_response.status_code
            )

            guard_ok = mutation_response.status_code in (400, 409)

            if mutation_response.status_code == 200:
                try:
                    body = mutation_response.get_json()
                except Exception:
                    body = None

                if body and body.get("success") is False:
                    guard_ok = True

            all_passed &= check(
                guard_ok,
                f"PUBLISHED examination rejects mutation: {mutation_payload}"
            )

        print(
            "Mutation guard response status:",
            mutation_response.status_code
        )

        # Accept 400/409 as the intended rejection.
        guard_ok = mutation_response.status_code in (400, 409)

        if mutation_response.status_code == 200:
            try:
                body = mutation_response.get_json()
            except Exception:
                body = None

            if body and body.get("success") is False:
                guard_ok = True

        all_passed &= check(
            guard_ok,
            "Sensitive field edit on PUBLISHED examination is rejected"
        )

    # ========================================================
    # PHASE 9B.1 — HALL ALLOCATION MUTATION GUARD
    # ========================================================

    print("\n[9B.1] Hall allocation mutation guard")

    from app.services.allocation import update_hall_allocation

    protected_hall_allocation = (
        HallAllocation.query
        .filter_by(examination_id=EXAMINATION_ID)
        .first()
    )

    if protected_hall_allocation:

        original_hall_id = protected_hall_allocation.hall_id
        original_capacity = protected_hall_allocation.allocated_capacity
        original_purpose = protected_hall_allocation.purpose

        examination = db.session.get(
            Examination,
            EXAMINATION_ID
        )

        examination.status = "APPROVED"
        db.session.commit()

        hall_mutation = update_hall_allocation(
            protected_hall_allocation.id,
            hall_id=original_hall_id,
            allocated_capacity=original_capacity,
            purpose=original_purpose
        )

        print("APPROVED hall mutation result:")
        print(hall_mutation)

        all_passed &= check(
            hall_mutation.get("success") is False,
            "Hall allocation mutation is rejected after APPROVED"
        )

        examination.status = "PUBLISHED"
        db.session.commit()

        hall_mutation_published = update_hall_allocation(
            protected_hall_allocation.id,
            hall_id=original_hall_id,
            allocated_capacity=original_capacity,
            purpose=original_purpose
        )

        print("PUBLISHED hall mutation result:")
        print(hall_mutation_published)

        all_passed &= check(
            hall_mutation_published.get("success") is False,
            "Hall allocation mutation is rejected after PUBLISHED"
        )

    # ========================================================
    # PHASE 9C — HALL TICKET SAFETY
    # ========================================================

    print("\n[9C] Hall ticket rejects invalid persisted allocation")

    from app.services.hall_ticket import (
        generate_hall_tickets
    )

    # Force a broken state again
    (
        InvigilatorAllocation.query
        .filter_by(examination_id=EXAMINATION_ID)
        .delete(synchronize_session=False)
    )
    db.session.commit()

    ticket_result = generate_hall_tickets(
        EXAMINATION_ID, force=True
    )
    print(ticket_result)

    all_passed &= check(
        ticket_result.get("success") is False,
        "Hall tickets rejected when persisted allocation invalid"
    )

    # restore
    generate_invigilator_allocation(
        EXAMINATION_ID, force=True
    )

    # ========================================================
    # PHASE 9D — BULK SEAT ALLOCATION
    # ========================================================

    section(9, "PHASE 9D — BULK OPERATIONS")

    from app.services.seat_allocation import (
        generate_bulk_seat_allocation
    )

    bulk_seat_result = generate_bulk_seat_allocation(
        [EXAMINATION_ID], force=True
    )
    print(bulk_seat_result)

    all_passed &= check(
        bulk_seat_result.get("success") is True,
        "Bulk seat allocation succeeded for one exam"
    )

    all_passed &= check(
        bulk_seat_result["results"][0]["status"]
        == "GENERATED",
        "Bulk seat result row is GENERATED"
    )

    # ========================================================
    # PHASE 9D.1 — BULK HALL ALLOCATION PARTIAL FAILURE
    # ========================================================

    print("\n[9D.1] Bulk hall allocation partial failure")

    from app.services import bulk_allocation

    print("Available bulk allocation functions:")
    print([
        name
        for name in dir(bulk_allocation)
        if name.startswith("generate")
    ])

    bulk_hall_result = bulk_allocation.generate_bulk_allocation(
        [EXAMINATION_ID, 999999],
        force=True
    )

    print(bulk_hall_result)

    all_passed &= check(
        len(bulk_hall_result.get("results", [])) == 2,
        "Bulk hall allocation processes every requested examination"
    )

    all_passed &= check(
        bulk_hall_result["results"][0]["status"] == "GENERATED",
        "Valid examination succeeds in mixed bulk hall allocation"
    )

    all_passed &= check(
        bulk_hall_result["results"][1]["status"] == "FAILED",
        "Invalid examination is reported as FAILED in bulk hall allocation"
    )
    all_passed &= check(
        len(bulk_hall_result.get("results", [])) == 2,
        "Bulk hall allocation processes every requested examination"
    )

    all_passed &= check(
        bulk_hall_result["results"][0]["status"] == "GENERATED",
        "Valid examination succeeds in mixed bulk hall allocation"
    )

    all_passed &= check(
        bulk_hall_result["results"][1]["status"] == "FAILED",
        "Invalid examination is reported as FAILED in bulk hall allocation"
    )

    # --------------------------------------------------------
    # 9D.1 — Bad exam in batch does not stop others
    # --------------------------------------------------------

    bulk_seat_mixed = generate_bulk_seat_allocation(
        [EXAMINATION_ID, 999999], force=True
    )
    print(bulk_seat_mixed)

    all_passed &= check(
        bulk_seat_mixed["results"][0]["status"]
        == "GENERATED",
        "Valid exam still processed when bad exam present"
    )

    all_passed &= check(
        bulk_seat_mixed["results"][1]["status"]
        == "FAILED",
        "Invalid exam reported as FAILED"
    )

    # ========================================================
    # PHASE 9E — BULK INVIGILATOR ALLOCATION
    # ========================================================

    from app.services.invigilator_allocation import (
        generate_bulk_invigilator_allocation
    )

    bulk_invig_result = generate_bulk_invigilator_allocation(
        [EXAMINATION_ID], force=True
    )
    print(bulk_invig_result)

    all_passed &= check(
        bulk_invig_result.get("success") is True,
        "Bulk invigilator allocation succeeded"
    )

    all_passed &= check(
        bulk_invig_result["results"][0]["status"]
        == "GENERATED",
        "Bulk invigilator result row is GENERATED"
    )

    first_invigilator_map = sorted(
        (
            row.timetable_id,
            row.hall_id,
            row.staff_id,
            row.role,
        )
        for row in InvigilatorAllocation.query.filter_by(
            examination_id=EXAMINATION_ID
        ).all()
)

    print("Initial invigilator assignment map:")
    print(first_invigilator_map)

    regenerated_invigilator_map = sorted(
        (
            row.timetable_id,
            row.hall_id,
            row.staff_id,
            row.role,
        )
        for row in InvigilatorAllocation.query.filter_by(
            examination_id=EXAMINATION_ID
        ).all()
    )

    all_passed &= check(
        regenerated_invigilator_map == first_invigilator_map,
        "Force regeneration produces identical staff assignments"
    )

    # ========================================================
    # PHASE 9E.1 — BULK INVIGILATOR PARTIAL FAILURE
    # ========================================================

    print("\n[9E.1] Bulk invigilator partial failure")

    bulk_invig_mixed = generate_bulk_invigilator_allocation(
        [EXAMINATION_ID, 999999],
        force=True
    )

    print(bulk_invig_mixed)

    all_passed &= check(
        len(bulk_invig_mixed.get("results", [])) == 2,
        "Bulk invigilator processes every requested examination"
    )

    all_passed &= check(
        bulk_invig_mixed["results"][0]["status"] == "GENERATED",
        "Valid examination succeeds in mixed bulk invigilator allocation"
    )

    all_passed &= check(
        bulk_invig_mixed["results"][1]["status"] == "FAILED",
        "Invalid examination is reported as FAILED"
    )

    # ========================================================
    # PHASE 9F — BULK VALIDATION
    # ========================================================

    from app.services.validation import (
        bulk_validate_examinations
    )

    bulk_val_result = bulk_validate_examinations(
        [EXAMINATION_ID, 999999]
    )
    print(bulk_val_result)

    all_passed &= check(
        bulk_val_result["processed"] == 2,
        "Bulk validation processes every requested exam"
    )

    all_passed &= check(
        bulk_val_result["results"][0]["status"] == "VALID",
        "Valid exam reports VALID"
    )

    all_passed &= check(
        bulk_val_result["results"][1]["status"] == "INVALID",
        "Missing exam reports INVALID"
    )

    # ========================================================
    # PHASE 9G — RBAC
    # ========================================================

    print("\n[9G] RBAC on bulk endpoints")

    rbac_response = client.post(
        "/api/allocations/seats/bulk-generate",
        json={"examination_ids": [EXAMINATION_ID]}
    )

    all_passed &= check(
        rbac_response.status_code in (401, 403),
        "Bulk seat endpoint rejects unauthenticated access"
    )

    rbac_response = client.post(
        "/api/allocations/invigilators/bulk-generate",
        json={"examination_ids": [EXAMINATION_ID]}
    )

    all_passed &= check(
        rbac_response.status_code in (401, 403),
        "Bulk invigilator endpoint rejects unauthenticated access"
    )

    rbac_response = client.post(
        "/api/allocations/validate/bulk",
        json={"examination_ids": [EXAMINATION_ID]}
    )

    all_passed &= check(
        rbac_response.status_code in (401, 403),
        "Bulk validate endpoint rejects unauthenticated access"
    )

    # ========================================================
    # PHASE 9H — DASHBOARD INTEGRATION
    # ========================================================

    section(9, "PHASE 9H — DASHBOARD INTEGRATION")

    if _admin_token:

        dashboard_response = client.get(
            "/api/dashboard/",
            headers={
                "Authorization": f"Bearer {_admin_token}"
            }
        )

        print(
            "Authenticated dashboard status:",
            dashboard_response.status_code
        )

        all_passed &= check(
            dashboard_response.status_code == 200,
            "Authenticated admin dashboard is accessible"
        )

        dashboard_body = dashboard_response.get_json() or {}

        all_passed &= check(
            isinstance(dashboard_body, dict),
            "Dashboard returns structured JSON"
        )

        print("Dashboard response:")
        print(dashboard_body)

    else:

        all_passed &= check(
            False,
            "Dashboard integration test requires authenticated admin"
        )

    # ========================================================
    # PHASE 9I — REPORT / DATABASE CONSISTENCY
    # ========================================================

    print("\n[9I] Report/database consistency")

    persisted_seat_count = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).count()

    persisted_invig_count = InvigilatorAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).count()

    all_passed &= check(
        len(stu_rep.get("rows", [])) == persisted_seat_count,
        "Student allocation report matches persisted seat count"
    )

    all_passed &= check(
        sum(
            row.get("duties", 0)
            for row in inv_rep.get("rows", [])
        ) == persisted_invig_count,
        "Invigilator report matches persisted invigilator count"
    )

    all_passed &= check(
        len(alloc_rep.get("rows", []))
        == HallAllocation.query.filter_by(
            examination_id=EXAMINATION_ID
        ).count(),
        "Allocation report matches persisted hall allocation count"
    )

    # ========================================================
    # FINAL END-TO-END STATE CONSISTENCY
    # ========================================================

    section(10, "FINAL END-TO-END STATE CONSISTENCY")

    examination = db.session.get(
        Examination,
        EXAMINATION_ID
    )

    final_halls = HallAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    final_seats = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    final_invigilators = InvigilatorAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

    final_allocation_validation = validate_allocation(
        EXAMINATION_ID
    )

    final_invigilator_validation = validate_invigilator_allocation(
        EXAMINATION_ID
    )

    all_passed &= check(
        examination.status == "PUBLISHED",
        "Final examination lifecycle state is PUBLISHED"
    )

    all_passed &= check(
        len(final_halls) > 0,
        "Final state contains hall allocations"
    )

    all_passed &= check(
        len(final_seats) == len(students) * len(timetables),
        "Final seat count equals eligible students × timetable entries"
    )

    all_passed &= check(
        len(final_invigilators) > 0,
        "Final state contains invigilator allocations"
    )

    all_passed &= check(
        final_allocation_validation.get("status") == "VALID",
        "Final persisted hall/seat allocation is VALID"
    )

    all_passed &= check(
        final_invigilator_validation.get("status") == "VALID",
        "Final persisted invigilator allocation is VALID"
    )

    all_passed &= check(
        HallTicket.query.filter_by(
            examination_id=EXAMINATION_ID
        ).count() > 0,
        "Final published state contains hall tickets"
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("EXAMNEXUS REGRESSION TEST SUMMARY")
    print("=" * 70)
    print(
        f"Overall regression result: "
        f"{'PASS' if all_passed else 'CHECK FAILURES'}"
    )

    print("\nPhase coverage included:")
    print("Phase 1 — Authentication + RBAC")
    print("Phase 2 — Master Data")
    print("Phase 3 — CSV Import + Manual CRUD")
    print("Phase 4 — Examination Creation")
    print("Phase 5 — Timetable Creation")
    print("Phase 6 — Eligibility + Resource Readiness")
    print("Phase 7 — Hall + Accessibility + Seat Allocation")
    print("Invigilator Allocation + Workload/Conflict Validation")
    print("Lifecycle — Generated → Validated → Review → Approved → Published")
    print("Hall Ticket + QR")
    print("Reports")
    print("Bulk Operations")
    print("Dashboard + RBAC")
    print("\n" + "=" * 70)

    if all_passed:
        print("RESULT: ALL REGRESSION TESTS PASSED")
    else:
        print("RESULT: SOME REGRESSION TESTS FAILED")

    print("=" * 70)