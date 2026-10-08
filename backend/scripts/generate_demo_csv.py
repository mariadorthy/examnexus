import csv
import random
import sys

from datetime import date
from pathlib import Path


# ---------------------------------------------------------
# MAKE BACKEND AVAILABLE TO PYTHON
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app import create_app
from app.models.department import Department
from app.models.course import Course


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

RANDOM_SEED = 42

OUTPUT_DIR = BACKEND_DIR / "data" / "demo_csv"

VALID_DEPARTMENTS = 5
VALID_COURSES = 10
VALID_SUBJECTS = 8
VALID_STUDENTS = 10
VALID_STAFF = 5
VALID_HALLS = 5


# ---------------------------------------------------------
# DEMO VALUES
# ---------------------------------------------------------

DEPARTMENT_DATA = [
    ("CSE", "Computer Science and Engineering"),
    ("ECE", "Electronics and Communication Engineering"),
    ("EEE", "Electrical and Electronics Engineering"),
    ("MECH", "Mechanical Engineering"),
    ("CIVIL", "Civil Engineering"),
]


COURSE_DATA = [
    (
        "BTECH-CSE",
        "Bachelor of Technology Computer Science",
        "B.Tech CSE",
        "UG",
        "MORNING",
        "2026-27",
        1,
        8,
    ),
    (
        "BTECH-ECE",
        "Bachelor of Technology Electronics",
        "B.Tech ECE",
        "UG",
        "MORNING",
        "2026-27",
        2,
        8,
    ),
    (
        "BTECH-EEE",
        "Bachelor of Technology Electrical",
        "B.Tech EEE",
        "UG",
        "MORNING",
        "2026-27",
        3,
        8,
    ),
    (
        "BTECH-MECH",
        "Bachelor of Technology Mechanical",
        "B.Tech MECH",
        "UG",
        "MORNING",
        "2026-27",
        4,
        8,
    ),
    (
        "BTECH-CIVIL",
        "Bachelor of Technology Civil",
        "B.Tech CIVIL",
        "UG",
        "MORNING",
        "2026-27",
        5,
        8,
    ),
    (
        "BTECH-CSE-AI",
        "Bachelor of Technology Computer Science Artificial Intelligence",
        "B.Tech CSE AI",
        "UG",
        "MORNING",
        "2026-27",
        1,
        8,
    ),
    (
        "BTECH-CSE-DS",
        "Bachelor of Technology Computer Science Data Science",
        "B.Tech CSE DS",
        "UG",
        "EVENING",
        "2026-27",
        1,
        8,
    ),
    (
        "BTECH-ECE-VLSI",
        "Bachelor of Technology Electronics VLSI",
        "B.Tech ECE VLSI",
        "UG",
        "MORNING",
        "2026-27",
        2,
        8,
    ),
    (
        "BTECH-EEE-POWER",
        "Bachelor of Technology Electrical Power Systems",
        "B.Tech EEE Power",
        "UG",
        "EVENING",
        "2026-27",
        3,
        8,
    ),
    (
        "BTECH-MECH-AUTO",
        "Bachelor of Technology Mechanical Automobile",
        "B.Tech MECH Auto",
        "UG",
        "MORNING",
        "2026-27",
        4,
        8,
    ),
]


SUBJECT_DATA = [
    ("CS101", "Programming Fundamentals", 1, "THEORY"),
    ("CS102", "Data Structures", 2, "THEORY"),
    ("CS103", "Database Management Systems", 3, "THEORY"),
    ("CS104", "Operating Systems", 4, "THEORY"),
    ("EC101", "Digital Electronics", 1, "THEORY"),
    ("EC102", "Communication Systems", 2, "THEORY"),
    ("ME101", "Engineering Mechanics", 1, "THEORY"),
    ("CE101", "Engineering Mathematics", 1, "THEORY"),
]


FIRST_NAMES = [
    "Aarav",
    "Aditya",
    "Ananya",
    "Arjun",
    "Diya",
    "Ishaan",
    "Kavya",
    "Meera",
    "Rahul",
    "Riya",
    "Rohan",
    "Sneha",
    "Vivek",
    "Neha",
    "Kiran",
]


LAST_NAMES = [
    "Sharma",
    "Kumar",
    "Patel",
    "Reddy",
    "Nair",
    "Iyer",
    "Menon",
    "Rao",
    "Singh",
    "Das",
    "Pillai",
    "Verma",
]


STAFF_NAMES = [
    "Dr. Arun Kumar",
    "Dr. Priya Sharma",
    "Dr. Ravi Menon",
    "Prof. Anjali Rao",
    "Prof. Karthik Nair",
]


STAFF_DESIGNATIONS = [
    "Professor",
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Assistant Professor",
]


# ---------------------------------------------------------
# CSV WRITER
# ---------------------------------------------------------

def write_csv(filename, headers, rows):
    """
    Write rows to a CSV file.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=headers
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Created: {path}"
    )

    return path


# ---------------------------------------------------------
# LOAD DATABASE REFERENCES
# ---------------------------------------------------------

def load_database_references():
    """
    Read existing active departments and courses.

    The database is read-only.
    Nothing is inserted or modified.
    """

    app = create_app()

    with app.app_context():

        departments = (
            Department.query
            .filter_by(is_active=True)
            .order_by(Department.id)
            .all()
        )

        courses = (
            Course.query
            .filter_by(is_active=True)
            .order_by(Course.id)
            .all()
        )

        department_refs = [
            {
                "id": department.id,
                "code": getattr(
                    department,
                    "department_code",
                    None
                ),
                "name": getattr(
                    department,
                    "department_name",
                    None
                ),
            }
            for department in departments
        ]

        course_refs = [
            {
                "id": course.id,
                "code": getattr(
                    course,
                    "course_code",
                    None
                ),
                "name": getattr(
                    course,
                    "course_name",
                    None
                ),
                "abbreviation": getattr(
                    course,
                    "course_abbreviation",
                    None
                ),
            }
            for course in courses
        ]

        return department_refs, course_refs


# ---------------------------------------------------------
# DEPARTMENTS
# ---------------------------------------------------------

def generate_departments():
    """
    Generate valid department CSV.
    """

    headers = [
        "department_code",
        "department_name",
    ]

    rows = []

    for code, name in DEPARTMENT_DATA[:VALID_DEPARTMENTS]:

        rows.append(
            {
                "department_code": code,
                "department_name": name,
            }
        )

    return write_csv(
        "departments_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# COURSES
# ---------------------------------------------------------

def generate_courses(department_refs):
    """
    Generate courses using real department IDs
    when available.

    The generated CSV follows the current Feature 13
    Course ENTITY_CONFIG.
    """

    headers = [
        "course_code",
        "course_name",
        "course_abbreviation",
        "program_level",
        "study_shift",
        "session",
        "department_id",
        "total_semesters",
    ]

    rows = []

    for index, (
        code,
        name,
        abbreviation,
        program_level,
        study_shift,
        session,
        fallback_department_id,
        semesters,
    ) in enumerate(
        COURSE_DATA[:VALID_COURSES]
    ):

        if department_refs:
            department_id = department_refs[
                index % len(department_refs)
            ]["id"]

        else:
            department_id = fallback_department_id

        rows.append(
            {
                "course_code": code,
                "course_name": name,
                "course_abbreviation": abbreviation,
                "program_level": program_level,
                "study_shift": study_shift,
                "session": session,
                "department_id": department_id,
                "total_semesters": semesters,
            }
        )

    return write_csv(
        "courses_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# SUBJECTS
# ---------------------------------------------------------

def generate_subjects(course_refs):
    """
    Generate valid subjects.

    If existing courses are available, use their IDs.
    Otherwise use deterministic demo course IDs 1..N.

    This keeps the generator usable against an empty
    development database as well as an existing database.
    """

    headers = [
        "subject_code",
        "subject_name",
        "course_id",
        "semester",
        "subject_type",
    ]

    rows = []

    for index, (
        code,
        name,
        semester,
        subject_type,
    ) in enumerate(
        SUBJECT_DATA[:VALID_SUBJECTS]
    ):

        if course_refs:
            course_id = course_refs[
                index % len(course_refs)
            ]["id"]

        else:
            course_id = (
                index % VALID_COURSES
            ) + 1

        rows.append(
            {
                "subject_code": code,
                "subject_name": name,
                "course_id": course_id,
                "semester": semester,
                "subject_type": subject_type,
            }
        )

    return write_csv(
        "subjects_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# STUDENTS
# ---------------------------------------------------------

def generate_students(course_refs):
    """
    Generate valid student CSV.

    Follows the current Feature 13 Student schema:
        student_id
        name
        course_id
        email
        password
        batch
        semester
        dob
    """

    headers = [
        "student_id",
        "name",
        "course_id",
        "email",
        "password",
        "batch",
        "semester",
        "dob",
    ]

    rows = []

    used_ids = set()

    for number in range(
        1,
        VALID_STUDENTS + 1
    ):

        first = FIRST_NAMES[
            (number - 1) % len(FIRST_NAMES)
        ]

        last = LAST_NAMES[
            (number - 1) % len(LAST_NAMES)
        ]

        student_id = (
            f"DEMO{number:04d}"
        )

        while student_id in used_ids:
            number += 1
            student_id = (
                f"DEMO{number:04d}"
            )

        used_ids.add(student_id)

        if course_refs:
            course_id = course_refs[
                (number - 1) % len(course_refs)
            ]["id"]

        else:
            course_id = (
                (number - 1) % VALID_COURSES
            ) + 1

        student_name = f"{first} {last}"

        email = (
            f"{student_id.lower()}"
            "@examnexus.edu"
        )

        password = "Demo@123"

        batch = "2026"

        semester = 1

        dob = date(
            2000 + ((number - 1) % 5),
            ((number - 1) % 12) + 1,
            ((number - 1) % 27) + 1
        )

        rows.append(
            {
                "student_id": student_id,
                "name": student_name,
                "course_id": course_id,
                "email": email,
                "password": password,
                "batch": batch,
                "semester": semester,
                "dob": dob.isoformat(),
            }
        )

    return write_csv(
        "students_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# STAFF
# ---------------------------------------------------------

def generate_staff(department_refs):
    """
    Generate valid staff CSV.

    Follows the current Feature 13 Staff schema.
    staff_id is intentionally omitted because it is not
    part of the current required/imported staff fields.
    """

    headers = [
        "name",
        "department_id",
        "email",
        "designation",
        "password",
        "dob",
    ]

    rows = []

    for number in range(
        1,
        VALID_STAFF + 1
    ):

        if department_refs:
            department_id = department_refs[
                (number - 1) % len(department_refs)
            ]["id"]

        else:
            department_id = (
                (number - 1) % VALID_DEPARTMENTS
            ) + 1

        staff_id = (
            f"STAFF{number:04d}"
        )

        email = (
            f"{staff_id.lower()}"
            "@examnexus.edu"
        )

        dob = date(
            1980 + ((number - 1) % 10),
            ((number - 1) % 12) + 1,
            10
        )

        rows.append(
            {
                "name": STAFF_NAMES[number - 1],
                "department_id": department_id,
                "email": email,
                "designation": STAFF_DESIGNATIONS[number - 1],
                "password": "Staff@123",
                "dob": dob.isoformat(),
            }
        )

    return write_csv(
        "staff_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# HALLS
# ---------------------------------------------------------

def generate_halls():
    """
    Generate valid hall CSV.
    """

    headers = [
        "name",
        "building_name",
        "floor_no",
        "capacity",
        "examination_capacity",
        "room_type",
        "amenities",
        "is_available",
        "is_under_maintenance",
        "is_accessible",
        "assigned_course_id",
        "assigned_batch",
    ]

    rows = []

    for number in range(
        1,
        VALID_HALLS + 1
    ):

        rows.append(
            {
                "name": f"Demo Hall {number}",
                "building_name": "Main Block",
                "floor_no": number % 3,
                "capacity": 100,
                "examination_capacity": 90,
                "room_type": "THEORY",
                "amenities": "Projector, Fan, Power",
                "is_available": "true",
                "is_under_maintenance": "false",
                "is_accessible": "true",
                "assigned_course_id": "",
                "assigned_batch": "",
            }
        )

    return write_csv(
        "halls_valid.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# INVALID STUDENTS
# ---------------------------------------------------------

def generate_invalid_students(course_refs):
    """
    Generate a CSV containing deliberate validation errors.

    Required columns are included so each row demonstrates
    the intended validation rule rather than failing because
    of missing CSV headers.
    """

    headers = [
        "student_id",
        "name",
        "course_id",
        "email",
        "password",
        "batch",
        "semester",
        "dob",
    ]

    valid_course_id = (
        course_refs[0]["id"]
        if course_refs
        else 1
    )

    rows = [

        # -------------------------------------------------
        # Invalid email
        # -------------------------------------------------
        {
            "student_id": "INVALID001",
            "name": "Invalid Email",
            "course_id": valid_course_id,
            "email": "not-an-email",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 1,
            "dob": "2002-01-15",
        },

        # -------------------------------------------------
        # Invalid integer
        # -------------------------------------------------
        {
            "student_id": "INVALID002",
            "name": "Invalid Course",
            "course_id": "ABC",
            "email": "invalid002@examnexus.edu",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 1,
            "dob": "2002-02-15",
        },

        # -------------------------------------------------
        # Invalid date
        # -------------------------------------------------
        {
            "student_id": "INVALID003",
            "name": "Invalid Date",
            "course_id": valid_course_id,
            "email": "invalid003@examnexus.edu",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 1,
            "dob": "not-a-date",
        },

        # -------------------------------------------------
        # Invalid semester
        # -------------------------------------------------
        {
            "student_id": "INVALID004",
            "name": "Invalid Semester",
            "course_id": valid_course_id,
            "email": "invalid004@examnexus.edu",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 99,
            "dob": "2002-04-15",
        },

        # -------------------------------------------------
        # Missing required name
        # -------------------------------------------------
        {
            "student_id": "INVALID005",
            "name": "",
            "course_id": valid_course_id,
            "email": "invalid005@examnexus.edu",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 1,
            "dob": "2002-05-15",
        },

        # -------------------------------------------------
        # Unknown course reference
        # -------------------------------------------------
        {
            "student_id": "INVALID006",
            "name": "Unknown Course",
            "course_id": 999999,
            "email": "invalid006@examnexus.edu",
            "password": "Demo@123",
            "batch": "2026",
            "semester": 1,
            "dob": "2002-06-15",
        },
    ]

    return write_csv(
        "students_invalid_demo.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# DUPLICATE DEPARTMENTS
# ---------------------------------------------------------

def generate_duplicate_departments():
    """
    Generate a CSV containing duplicate department rows.
    """

    headers = [
        "department_code",
        "department_name",
    ]

    rows = [
        {
            "department_code": "DEMO-DUP",
            "department_name": "Demo Duplicate Department",
        },
        {
            "department_code": "DEMO-DUP",
            "department_name": "Demo Duplicate Department",
        },
        {
            "department_code": "DEMO-DUP-2",
            "department_name": "Another Demo Department",
        },
        {
            "department_code": "DEMO-DUP-2",
            "department_name": "Another Demo Department",
        },
    ]

    return write_csv(
        "departments_duplicate_demo.csv",
        headers,
        rows
    )


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

def print_summary(
    department_refs,
    course_refs
):
    print()
    print("=" * 70)
    print("ExamNexus - Demo CSV Generator")
    print("=" * 70)
    print()

    print(
        f"Output directory:"
        f"\n{OUTPUT_DIR}"
    )

    print()

    print(
        f"Existing departments detected: "
        f"{len(department_refs)}"
    )

    print(
        f"Existing courses detected: "
        f"{len(course_refs)}"
    )

    print()

    print("Generated files:")
    print()

    print("  1. departments_valid.csv")
    print("  2. courses_valid.csv")
    print("  3. subjects_valid.csv")
    print("  4. students_valid.csv")
    print("  5. staff_valid.csv")
    print("  6. halls_valid.csv")
    print("  7. students_invalid_demo.csv")
    print("  8. departments_duplicate_demo.csv")

    print()

    print("=" * 70)
    print("IMPORTANT")
    print("=" * 70)
    print()

    print(
        "These files are generated for CSV import testing."
    )

    print(
        "This script DOES NOT insert or modify database records."
    )

    print(
        "Passwords are demo values only and are hashed by "
        "the backend during import."
    )

    print(
        "Upload the files through the ExamNexus CSV Import UI."
    )

    print()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def generate_demo_csvs():

    random.seed(RANDOM_SEED)

    print()
    print("=" * 70)
    print("Starting ExamNexus Demo CSV Generation")
    print("=" * 70)
    print()

    # -----------------------------------------------------
    # READ DATABASE REFERENCES
    # -----------------------------------------------------

    department_refs, course_refs = (
        load_database_references()
    )

    # -----------------------------------------------------
    # GENERATE FILES
    # -----------------------------------------------------

    generate_departments()

    generate_courses(
        department_refs
    )

    generate_subjects(
        course_refs
    )

    generate_students(
        course_refs
    )

    generate_staff(
        department_refs
    )

    generate_halls()

    generate_invalid_students(
        course_refs
    )

    generate_duplicate_departments()

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    print_summary(
        department_refs,
        course_refs
    )


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    generate_demo_csvs()