from app import create_app, db
from app.models.department import Department
from app.models.course import Course


COURSES = [
    {
        "course_code": "CSEM01",
        "course_name": "Computer Science Engineering",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "CSEM",
        "total_semesters": 8,
    },
    {
        "course_code": "CSEA01",
        "course_name": "Computer Science Engineering",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "CSEA",
        "total_semesters": 8,
    },
    {
        "course_code": "MEM01",
        "course_name": "Mechanical Engineering",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "MEM",
        "total_semesters": 8,
    },
    {
        "course_code": "MEA01",
        "course_name": "Mechanical Engineering",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "MEA",
        "total_semesters": 8,
    },
    {
        "course_code": "CEM01",
        "course_name": "Civil Engineering",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "CEM",
        "total_semesters": 8,
    },
    {
        "course_code": "CEA01",
        "course_name": "Civil Engineering",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "CEA",
        "total_semesters": 8,
    },
    {
        "course_code": "ITM01",
        "course_name": "Information Technology",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "ITM",
        "total_semesters": 8,
    },
    {
        "course_code": "ITA01",
        "course_name": "Information Technology",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "ITA",
        "total_semesters": 8,
    },
    {
        "course_code": "EEEM01",
        "course_name": "Electrical and Electronics Engineering",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "EEEM",
        "total_semesters": 8,
    },
    {
        "course_code": "EEEA01",
        "course_name": "Electrical and Electronics Engineering",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "EEEA",
        "total_semesters": 8,
    },
    {
        "course_code": "ECEM01",
        "course_name": "Electronics and Communication Engineering",
        "program_level": "UG",
        "study_shift": "Morning",
        "session": "FN",
        "department": "Engineering",
        "abbreviation": "ECEM",
        "total_semesters": 8,
    },
    {
        "course_code": "ECEA01",
        "course_name": "Electronics and Communication Engineering",
        "program_level": "UG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Engineering",
        "abbreviation": "ECEA",
        "total_semesters": 8,
    },
    {
        "course_code": "MBAA01",
        "course_name": "Master of Business Administration",
        "program_level": "PG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Management",
        "abbreviation": "MBAA",
        "total_semesters": 4,
    },
    {
        "course_code": "MCAA01",
        "course_name": "Master of Computer Applications",
        "program_level": "PG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Management",
        "abbreviation": "MCAA",
        "total_semesters": 4,
    },
    {
        "course_code": "AIA01",
        "course_name": "Artificial Intelligence",
        "program_level": "PG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Specialized Programs",
        "abbreviation": "AIA",
        "total_semesters": 4,
    },
    {
        "course_code": "CYA01",
        "course_name": "Cybersecurity",
        "program_level": "PG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Specialized Programs",
        "abbreviation": "CYA",
        "total_semesters": 4,
    },
    {
        "course_code": "MArchA01",
        "course_name": "Master of Architecture",
        "program_level": "PG",
        "study_shift": "Afternoon",
        "session": "AN",
        "department": "Architecture",
        "abbreviation": "MARCHA",
        "total_semesters": 4,
    },
]


DEPARTMENTS = [
    {
        "code": "ENG1",
        "name": "Engineering",
    },
    {
        "code": "MAN1",
        "name": "Management",
    },
    {
        "code": "SPE1",
        "name": "Specialized Programs",
    },
    {
        "code": "ARC1",
        "name": "Architecture",
    },
]


def create_departments():
    for department_data in DEPARTMENTS:
        department = Department.query.filter_by(
            department_code=department_data["code"]
        ).first()

        if department:
            continue

        department = Department(
            department_code=department_data["code"],
            department_name=department_data["name"],
            is_active=True,
        )

        db.session.add(department)

    db.session.commit()


def create_courses():
    created = 0
    skipped = 0

    for course_data in COURSES:

        existing = Course.query.filter_by(
            course_code=course_data["course_code"]
        ).first()

        if existing:
            skipped += 1
            continue

        department = Department.query.filter_by(
            department_name=course_data["department"]
        ).first()

        if not department:
            print(
                f"Skipping {course_data['course_code']}: "
                f"department not found"
            )
            continue

        course = Course(
            course_code=course_data["course_code"],
            course_name=course_data["course_name"],
            course_abbreviation=course_data["abbreviation"],
            program_level=course_data["program_level"],
            department_id=department.id,
            study_shift=course_data["study_shift"],
            session=course_data["session"],
            total_semesters=course_data["total_semesters"],
            is_active=True,
        )

        db.session.add(course)
        created += 1

    db.session.commit()

    print(f"Courses created: {created}")
    print(f"Courses already existed: {skipped}")


def show_courses():
    courses = Course.query.order_by(Course.course_code).all()

    print("\nCurrent courses:")
    print("-" * 100)

    for course in courses:
        print(
            f"{course.course_code:10} | "
            f"{course.course_name:45} | "
            f"{course.study_shift:9} | "
            f"{course.session:2} | "
            f"{course.program_level:2} | "
            f"Semesters: {course.total_semesters}"
        )


def main():
    app = create_app()

    with app.app_context():
        create_departments()
        create_courses()
        show_courses()


if __name__ == "__main__":
    main()