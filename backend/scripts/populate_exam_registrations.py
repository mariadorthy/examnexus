import random

from app import create_app, db
from app.models.student import Student
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration


# ============================================================
# CONFIGURATION
# ============================================================

EXAMINATION_IDS = [1]

# Number of students to register for the demo examination.
TARGET_REGISTRATIONS = 8000

# Percentage of registrations that should be marked PAID.
PAID_PERCENTAGE = 0.90

# Use a fixed seed so the result is repeatable.
RANDOM_SEED = 42


def populate_exam_registrations():
    random.seed(RANDOM_SEED)

    for examination_id in EXAMINATION_IDS:

        # --------------------------------------------------------
        # 1. Find examination
        # --------------------------------------------------------

        examination = Examination.query.get(examination_id)

        if not examination:
            print(f"ERROR: Examination {examination_id} not found.")
            continue

    print("=" * 60)
    print("EXAM REGISTRATION DEMO DATA")
    print("=" * 60)

    print(f"Examination ID : {examination.id}")
    print(f"Examination    : {examination.name}")
    print(f"Course ID      : {examination.course_id}")
    print(f"Semester       : {examination.semester}")
    print()

    # --------------------------------------------------------
    # 2. Find active students matching the examination
    # --------------------------------------------------------

    students = Student.query.filter_by(
            is_active=True
        ).all()

    print(f"Matching active students: {len(students)}")

    if not students:
        print("No matching students found.")
        return

    # --------------------------------------------------------
    # 3. Find existing registrations
    # --------------------------------------------------------

    existing_registrations = {
        registration.student_id: registration
        for registration in ExamRegistration.query.filter_by(
            examination_id=examination.id
        ).all()
    }

    print(
        f"Existing registrations: "
        f"{len(existing_registrations)}"
    )

    # --------------------------------------------------------
    # 4. Create missing registrations as PENDING
    # --------------------------------------------------------

    new_registrations = []

    random.shuffle(students)

    for student in students:

        if len(existing_registrations) + len(new_registrations) >= TARGET_REGISTRATIONS:
            break

        if student.id in existing_registrations:
            continue

        registration = ExamRegistration(
            student_id=student.id,
            examination_id=examination.id,
            status="REGISTERED",
            fee_status="PENDING"
        )

        new_registrations.append(registration)

    if new_registrations:
        db.session.add_all(new_registrations)
        db.session.commit()

    print(
        f"New registrations created: "
        f"{len(new_registrations)}"
    )

    # --------------------------------------------------------
    # 5. Get all registrations for this examination
    # --------------------------------------------------------

    registrations = ExamRegistration.query.filter_by(
        examination_id=examination.id,
        status="REGISTERED"
    ).all()

    if not registrations:
        print("No registrations available.")
        return

    # --------------------------------------------------------
    # 6. Randomly assign PAID / PENDING
    # --------------------------------------------------------

    for registration in registrations:

        if random.random() < PAID_PERCENTAGE:
            registration.fee_status = "PAID"
        else:
            registration.fee_status = "PENDING"

    db.session.commit()

    # --------------------------------------------------------
    # 7. Print final counts
    # --------------------------------------------------------

    paid_count = sum(
        1
        for registration in registrations
        if registration.fee_status == "PAID"
    )

    pending_count = sum(
        1
        for registration in registrations
        if registration.fee_status == "PENDING"
    )

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(f"Total registrations : {len(registrations)}")
    print(f"PAID                : {paid_count}")
    print(f"PENDING             : {pending_count}")

    print()
    print("Eligibility readiness:")
    print(
        f"Eligible candidates : {paid_count}"
    )
    print(
        f"Not ready candidates: {pending_count}"
    )

    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        populate_exam_registrations()
