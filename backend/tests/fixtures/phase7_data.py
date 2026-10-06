from datetime import date, time

from werkzeug.security import generate_password_hash

from app import db
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject
from app.models.student import Student
from app.models.staff import Staff
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration
from app.models.hall import Hall
from app.models.timetable import Timetable


def seed_phase7_data():
    """
    Create a small, controlled dataset for Phase 7 allocation tests.

    This data is intended only for the pytest database.
    It is independent from the main demo database.
    """

    # ---------------------------------------------------------
    # Department
    # ---------------------------------------------------------
    department = Department(
        department_code="TEST-CSE",
        department_name="Test Computer Science"
    )
    db.session.add(department)
    db.session.flush()

    # ---------------------------------------------------------
    # Courses
    # ---------------------------------------------------------
    course1 = Course(
        course_code="TEST-CSE-A",
        course_name="Test Computer Science A",
        course_abbreviation="TCSEA",
        program_level="Undergraduate",
        department_id=department.id,
        study_shift="DAY",
        session="UG",
        total_semesters=8,
        is_active=True
    )

    course2 = Course(
        course_code="TEST-CSE-B",
        course_name="Test Computer Science B",
        course_abbreviation="TCSEB",
        program_level="Undergraduate",
        department_id=department.id,
        study_shift="DAY",
        session="UG",
        total_semesters=8,
        is_active=True
    )

    db.session.add_all([course1, course2])
    db.session.flush()

    # ---------------------------------------------------------
    # Subjects
    # ---------------------------------------------------------
    subject1 = Subject(
        subject_code="TEST-CS401",
        subject_name="Test Database Systems",
        course_id=course1.id,
        semester=4,
        subject_type="THEORY",
        is_active=True
    )

    subject2 = Subject(
        subject_code="TEST-CS402",
        subject_name="Test Operating Systems",
        course_id=course2.id,
        semester=4,
        subject_type="THEORY",
        is_active=True
    )

    db.session.add_all([subject1, subject2])
    db.session.flush()

    # ---------------------------------------------------------
    # Examination
    # ---------------------------------------------------------
    examination = Examination(
        name="Phase 7 Allocation Test Examination",
        exam_type="END_SEMESTER",
        course_id=course1.id,
        semester=4,
        start_date=date(2026, 10, 15),
        end_date=date(2026, 10, 15),
        duration_minutes=180,
        status="DRAFT",
        session_config=["FN", "AN"],
        excluded_dates=[]
    )

    db.session.add(examination)
    db.session.flush()

    # ---------------------------------------------------------
    # Students
    # ---------------------------------------------------------
    students = []

    for i in range(1, 13):
        if i <= 6:
            course_id = course1.id
            course_prefix = "A"
        else:
            course_id = course2.id
            course_prefix = "B"

        disability = None

        # Two accessibility students.
        if i in (1, 7):
            disability = "Mobility support"

        student = Student(
            student_id=f"TEST-{course_prefix}-{i:03d}",
            name=f"Test Student {i}",
            course_id=course_id,
            email=f"test.student{i}@examnexus.edu",
            password_hash=generate_password_hash("Test@123"),
            batch="2023",
            semester=4,
            class_name="TEST-A",
            session="UG",
            disability=disability,
            email_verified=True,
            two_factor_enabled=False,
            is_active=True
        )

        students.append(student)

    db.session.add_all(students)
    db.session.flush()

    # ---------------------------------------------------------
    # Exam registrations
    # ---------------------------------------------------------
    registrations = [
        ExamRegistration(
            student_id=student.id,
            examination_id=examination.id,
            status="REGISTERED",
            fee_status="PENDING"
        )
        for student in students
    ]

    db.session.add_all(registrations)

    # ---------------------------------------------------------
    # Halls
    #
    # Capacities deliberately allow the optimization tests
    # to exercise multiple-hall allocation.
    # ---------------------------------------------------------
    hall1 = Hall(
        name="TEST-H101",
        building_name="Test Block",
        floor_no=0,
        capacity=6,
        examination_capacity=6,
        room_type="CLASS",
        amenities="Fans, Lights",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=True,
        is_active=True
    )

    hall2 = Hall(
        name="TEST-H102",
        building_name="Test Block",
        floor_no=0,
        capacity=6,
        examination_capacity=6,
        room_type="CLASS",
        amenities="Fans, Lights",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=True,
        is_active=True
    )

    hall3 = Hall(
        name="TEST-H103",
        building_name="Test Block",
        floor_no=1,
        capacity=7,
        examination_capacity=7,
        room_type="CLASS",
        amenities="Fans, Lights",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=False,
        is_active=True
    )

    hall4 = Hall(
        name="TEST-H104",
        building_name="Test Block",
        floor_no=1,
        capacity=7,
        examination_capacity=7,
        room_type="CLASS",
        amenities="Fans, Lights",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=False,
        is_active=True
    )

    db.session.add_all([hall1, hall2, hall3, hall4])
    db.session.flush()

    # ---------------------------------------------------------
    # Staff
    #
    # Four staff members are available so simultaneous hall
    # allocations can receive separate invigilators.
    # ---------------------------------------------------------
    staff_members = []

    for i in range(1, 5):
        staff = Staff(
            name=f"Test Staff {i}",
            department_id=department.id,
            email=f"test.staff{i}@examnexus.edu",
            contact_no=f"900000000{i}",
            designation="Assistant Professor",
            assigned_courses="TEST-CSE-A,TEST-CSE-B",
            gender="Other",
            availability=True,
            assigned_batch="2023",
            password_hash=generate_password_hash("Test@123"),
            is_active=True
        )
        staff_members.append(staff)

    db.session.add_all(staff_members)
    db.session.flush()

    # ---------------------------------------------------------
    # Timetable
    #
    # Two timetable entries for the same examination.
    # This allows tests to verify that halls/students can be
    # allocated independently per timetable.
    # ---------------------------------------------------------
    timetable1 = Timetable(
        examination_id=examination.id,
        subject_id=subject1.id,
        exam_date=date(2026, 10, 15),
        session="FN",
        start_time=time(9, 30),
        end_time=time(12, 30),
        duration_minutes=180,
        status="GENERATED"
    )

    timetable2 = Timetable(
        examination_id=examination.id,
        subject_id=subject2.id,
        exam_date=date(2026, 10, 15),
        session="AN",
        start_time=time(14, 00),
        end_time=time(17, 00),
        duration_minutes=180,
        status="GENERATED"
    )

    db.session.add_all([timetable1, timetable2])

    db.session.commit()

    return {
        "examination": examination,
        "courses": [course1, course2],
        "subjects": [subject1, subject2],
        "students": students,
        "halls": [hall1, hall2, hall3, hall4],
        "staff": staff_members,
        "timetables": [timetable1, timetable2],
    }