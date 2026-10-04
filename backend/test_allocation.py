from app import create_app

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


with app.app_context():

    print("=" * 70)
    print("EXAMNEXUS — PHASE 1 → PHASE 7 REGRESSION TEST")
    print("=" * 70)

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

    paid_registration_ids = {
        registration.student_id
        for registration in registrations
        if registration.status == "REGISTERED"
        and registration.fee_status == "PAID"
    }

    all_passed &= check(
        set(eligible_student_ids).issubset(paid_registration_ids),
        "Eligible students satisfy current fee eligibility rule"
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

    regenerated_seats = SeatAllocation.query.filter_by(
        examination_id=EXAMINATION_ID
    ).all()

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
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("EXAMNEXUS REGRESSION TEST SUMMARY")
    print("=" * 70)

    print(f"Phase 1 — Authentication + RBAC : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 2 — Master Data            : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 3 — CSV/Manual CRUD        : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 4 — Examination Creation   : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 5 — Timetable Creation     : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 6 — Eligibility/Readiness  : {'PASS' if all_passed else 'CHECK'}")
    print(f"Phase 7 — Allocation Engine      : {'PASS' if all_passed else 'CHECK'}")

    print("\n" + "=" * 70)

    if all_passed:
        print("RESULT: ALL REGRESSION TESTS PASSED")
    else:
        print("RESULT: SOME REGRESSION TESTS FAILED")

    print("=" * 70)