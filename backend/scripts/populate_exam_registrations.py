import random

from app import create_app, db
from app.models.student import Student
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration


# ============================================================
# CONFIGURATION
# ============================================================

# Percentage of registered students whose fee is marked PAID.
PAID_PERCENTAGE = 0.80

# Fixed seed so the demo data is repeatable.
RANDOM_SEED = 42


def populate_exam_registrations():
    random.seed(RANDOM_SEED)

    # --------------------------------------------------------
    # 1. Get all examinations
    # --------------------------------------------------------

    examinations = Examination.query.order_by(
        Examination.id
    ).all()

    if not examinations:
        print("ERROR: No examinations found.")
        return

    # --------------------------------------------------------
    # 2. Get all active students
    # --------------------------------------------------------

    students = Student.query.filter_by(
        is_active=True
    ).all()

    print("=" * 70)
    print("EXAMNEXUS — EXAM REGISTRATION DEMO DATA")
    print("=" * 70)

    print(f"Active students found : {len(students)}")
    print(f"Examinations found    : {len(examinations)}")
    print(f"Paid percentage       : {PAID_PERCENTAGE * 100:.0f}%")
    print()

    if not students:
        print("ERROR: No active students found.")
        return

    total_created = 0
    total_paid = 0
    total_pending = 0

    # --------------------------------------------------------
    # 3. Process every examination
    # --------------------------------------------------------

    for examination in examinations:

        print("-" * 70)
        print(
            f"Examination {examination.id}: "
            f"{examination.name}"
        )
        print(
            f"Course ID: {examination.course_id} | "
            f"Semester: {examination.semester}"
        )

        # ----------------------------------------------------
        # 4. Match students to the examination
        #
        # Examination course + semester determine
        # which students belong to this examination.
        # ----------------------------------------------------

        matching_students = [
            student
            for student in students
            if student.course_id == examination.course_id
            and student.semester == examination.semester
        ]

        print(
            f"Matching students: "
            f"{len(matching_students)}"
        )

        if not matching_students:
            print("No matching students. Skipping.")
            continue

        # ----------------------------------------------------
        # 5. Get existing registrations
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 6. Create missing registrations
        #
        # Every registration starts as PENDING.
        # ----------------------------------------------------

        new_registrations = []

        for student in matching_students:

            if student.id in existing_registrations:
                continue

            registration = ExamRegistration(
                student_id=student.id,
                examination_id=examination.id,
                status="REGISTERED",
                fee_status="PENDING",
            )

            new_registrations.append(registration)

        if new_registrations:
            db.session.add_all(new_registrations)
            db.session.commit()

        print(
            f"New registrations created: "
            f"{len(new_registrations)}"
        )

        total_created += len(new_registrations)

        # ----------------------------------------------------
        # 7. Get all registrations for this examination
        # ----------------------------------------------------

        registrations = ExamRegistration.query.filter_by(
            examination_id=examination.id,
            status="REGISTERED",
        ).all()

        # ----------------------------------------------------
        # 8. Assign PAID / PENDING
        #
        # Only registered students for THIS examination
        # receive this examination's fee status.
        # ----------------------------------------------------

        paid_count = 0
        pending_count = 0

        for registration in registrations:

            if random.random() < PAID_PERCENTAGE:
                registration.fee_status = "PAID"
                paid_count += 1
            else:
                registration.fee_status = "PENDING"
                pending_count += 1

        db.session.commit()

        total_paid += paid_count
        total_pending += pending_count

        print(f"PAID       : {paid_count}")
        print(f"PENDING    : {pending_count}")
        print(
            f"Total      : "
            f"{paid_count + pending_count}"
        )

    # --------------------------------------------------------
    # 9. Final result
    # --------------------------------------------------------

    total_registrations = ExamRegistration.query.count()

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(f"Students in database       : {len(students)}")
    print(f"Examinations processed     : {len(examinations)}")
    print(f"New registrations created  : {total_created}")
    print(f"Total registrations        : {total_registrations}")
    print()

    print("Eligibility data:")
    print(f"PAID                       : {total_paid}")
    print(f"PENDING                    : {total_pending}")

    print()
    print("Meaning:")
    print("PAID    → Eligible for examination allocation")
    print("PENDING → Not ready for examination allocation")

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        populate_exam_registrations()