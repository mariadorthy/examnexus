from datetime import date, time

from app import create_app, db
from app.models.department import Department
from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration
from app.models.hall import Hall
from app.models.staff import Staff


app = create_app()


with app.app_context():

    # -------------------------
    # Department
    # -------------------------

    department = Department(
        department_code="CSE",
        department_name="Computer Science and Engineering"
    )

    db.session.add(department)
    db.session.flush()


    # -------------------------
    # Course
    # -------------------------

    course = Course(
        course_code="BTECH-CSE",
        course_name="Bachelor of Technology - Computer Science",
        course_abbreviation="BTECH-CSE",
        program_level="Undergraduate",
        department_id=department.id,
        total_semesters=8
    )

    db.session.add(course)
    db.session.flush()


    # -------------------------
    # Students
    # -------------------------

    student1 = Student(
        student_id="CSE001",
        name="Arun Kumar",
        course_id=course.id,
        email="arun@example.com",
        password_hash="temporary_hash",
        batch="2023",
        semester=4
    )

    student2 = Student(
        student_id="CSE002",
        name="Priya Sharma",
        course_id=course.id,
        email="priya@example.com",
        password_hash="temporary_hash",
        batch="2023",
        semester=4
    )

    student3 = Student(
        student_id="CSE003",
        name="Rahul Raj",
        course_id=course.id,
        email="rahul@example.com",
        password_hash="temporary_hash",
        batch="2023",
        semester=4
    )

    db.session.add_all([
        student1,
        student2,
        student3
    ])


    # -------------------------
    # Subject
    # -------------------------

    subject = Subject(
        subject_code="CS401",
        subject_name="Database Management Systems",
        course_id=course.id,
        semester=4,
        subject_type="THEORY"
    )

    db.session.add(subject)
    db.session.flush()


    # -------------------------
    # Examination
    # -------------------------

    examination = Examination(
        subject_id=subject.id,
        exam_date=date(2026, 10, 15),
        session="MORNING",
        start_time=time(9, 30),
        end_time=time(12, 30),
        duration_minutes=180,
        exam_type="END_SEMESTER"
    )

    db.session.add(examination)


    # -------------------------
    # Exam Registrations
    # -------------------------

    db.session.flush()

    registrations = [
        ExamRegistration(
            student_id=student1.id,
            examination_id=examination.id
        ),
        ExamRegistration(
            student_id=student2.id,
            examination_id=examination.id
        ),
        ExamRegistration(
            student_id=student3.id,
            examination_id=examination.id
        )
    ]

    db.session.add_all(registrations)


    # -------------------------
    # Halls
    # -------------------------

    hall1 = Hall(
        name="H101",
        building_name="Main Block",
        floor_no=1,
        capacity=60,
        examination_capacity=50,
        room_type="CLASS",
        amenities="Projector, Fans, Lights",
        assigned_course_id=course.id,
        assigned_batch="2023",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=True
    )

    hall2 = Hall(
        name="H102",
        building_name="Main Block",
        floor_no=1,
        capacity=80,
        examination_capacity=70,
        room_type="CLASS",
        amenities="Fans, Lights",
        assigned_course_id=course.id,
        assigned_batch="2023",
        is_available=True,
        is_under_maintenance=False,
        is_accessible=True
    )

    db.session.add_all([
        hall1,
        hall2
    ])


    # -------------------------
    # Staff
    # -------------------------

    staff = Staff(
        name="Dr. Meena Kumar",
        department_id=department.id,
        email="meena@example.com",
        contact_no="9876543210",
        designation="Assistant Professor",
        assigned_courses="BTECH-CSE",
        gender="Female",
        availability=True,
        assigned_batch="2023",
        password_hash="temporary_hash"
    )

    db.session.add(staff)

    db.session.commit()

    print("Sample data inserted successfully.")