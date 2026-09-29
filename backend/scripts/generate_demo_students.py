import random
import sys

from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

# ---------------------------------------------------------
# MAKE BACKEND AVAILABLE TO PYTHON
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app import create_app, db
from app.models.student import Student
from app.models.course import Course


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

RANDOM_SEED = 42

MIN_STUDENTS_PER_CLASS = 40
MAX_STUDENTS_PER_CLASS = 50

CLASSES = ["A", "B"]

CURRENT_YEAR = 2026


# ---------------------------------------------------------
# PASSWORD
# ---------------------------------------------------------

DEMO_PASSWORD = "Demo@123"

DEMO_PASSWORD_HASH = generate_password_hash(
    DEMO_PASSWORD
)


# ---------------------------------------------------------
# ACCESSIBILITY
# ---------------------------------------------------------

DISABILITY_PERCENTAGE = 0.05


# ---------------------------------------------------------
# DATA FILES
# ---------------------------------------------------------

DATA_DIR = BACKEND_DIR / "data"

FIRST_NAMES_FILE = DATA_DIR / "first_names.txt"
LAST_NAMES_FILE = DATA_DIR / "Last_names.txt"


# ---------------------------------------------------------
# LOAD NAMES
# ---------------------------------------------------------

def load_names(file_path):
    """
    Load names from a text file.

    Each line contains one name.
    Empty lines are ignored.
    Duplicate names are removed.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Name file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        names = [
            line.strip()
            for line in file
            if line.strip()
        ]

    names = list(dict.fromkeys(names))

    if not names:
        raise ValueError(
            f"No names found in {file_path}"
        )

    return names


def load_first_and_last_names():

    first_names = load_names(
        FIRST_NAMES_FILE
    )

    last_names = load_names(
        LAST_NAMES_FILE
    )

    return first_names, last_names


# ---------------------------------------------------------
# NAME GENERATION
# ---------------------------------------------------------

def generate_unique_names(
    first_names,
    last_names,
    required_count
):
    """
    Generate unique full names.
    """

    possible_names = [
        f"{first} {last}"
        for first in first_names
        for last in last_names
    ]

    if len(possible_names) < required_count:

        raise ValueError(
            f"Not enough unique name combinations.\n"
            f"Available combinations: "
            f"{len(possible_names)}\n"
            f"Required: {required_count}"
        )

    random.shuffle(possible_names)

    return possible_names[:required_count]


# ---------------------------------------------------------
# DATE OF BIRTH
# ---------------------------------------------------------

def generate_dob(
    age_min=18,
    age_max=25
):
    """
    Generate a realistic student date of birth.
    """

    today = date.today()

    earliest_dob = today - timedelta(
        days=age_max * 365
    )

    latest_dob = today - timedelta(
        days=age_min * 365
    )

    days_range = (
        latest_dob - earliest_dob
    ).days

    return earliest_dob + timedelta(
        days=random.randint(
            0,
            days_range
        )
    )


# ---------------------------------------------------------
# BATCH GENERATION
# ---------------------------------------------------------

def generate_batch(
    course,
    admission_year
):
    """
    Generate an academic admission batch.

    UG examples:

        2023-2026
        2024-2027
        2025-2028
        2026-2029

    PG examples:

        2024-2025
        2025-2026
        2026-2027
    """

    course_duration_years = (
        course.total_semesters // 2
    )

    end_year = (
        admission_year
        + course_duration_years
        - 1
    )

    return f"{admission_year}-{end_year}"


# ---------------------------------------------------------
# DETERMINE ADMISSION YEARS
# ---------------------------------------------------------

def get_admission_years(course):
    """
    Return the admission years that should exist
    for the current demo snapshot.

    UG:
        2023
        2024
        2025
        2026

    PG:
        2024
        2025
        2026
    """

    course_duration_years = (
        course.total_semesters // 2
    )

    first_admission_year = (
        CURRENT_YEAR
        - course_duration_years
        + 1
    )

    return range(
        first_admission_year,
        CURRENT_YEAR + 1
    )


# ---------------------------------------------------------
# DETERMINE SEMESTERS
# ---------------------------------------------------------

def get_current_semesters(
    admission_year,
    course
):
    """
    Determine the two semesters represented
    by a batch in the 2026 demo snapshot.

    UG:

        2023-2026 -> 7, 8
        2024-2027 -> 5, 6
        2025-2028 -> 3, 4
        2026-2029 -> 1, 2

    PG:

        2024-2025 -> 3, 4
        2025-2026 -> 1, 2
        2026-2027 -> 1, 2
    """

    years_completed = (
        CURRENT_YEAR - admission_year
    )

    first_semester = (
        years_completed * 2 + 1
    )

    second_semester = (
        years_completed * 2 + 2
    )

    semesters = [
        first_semester,
        second_semester
    ]

    # Safety check
    semesters = [
        semester
        for semester in semesters
        if semester <= course.total_semesters
    ]

    return semesters


# ---------------------------------------------------------
# STUDENT ID
# ---------------------------------------------------------

def generate_student_id(
    course,
    batch,
    semester,
    class_name,
    number
):
    """
    Generate a student ID.

    Structure:

        COURSE + ADMISSION YEAR + SEMESTER + CLASS + NUMBER

    Examples:

        CSEM261A001
        CSEM261A002
        CSEM261B001
        CSEM257A001
    """

    abbreviation = (
        course.course_abbreviation
        .upper()
        .replace(" ", "")
    )

    admission_year = batch.split("-")[0]

    admission_year_short = admission_year[-2:]

    return (
        f"{abbreviation}"
        f"{admission_year_short}"
        f"{semester}"
        f"{class_name}"
        f"{number:03d}"
    )


# ---------------------------------------------------------
# EMAIL
# ---------------------------------------------------------

def generate_email(student_id):
    """
    Generate a unique demo email.
    """

    return (
        f"{student_id.lower()}"
        f"@examnexus.edu"
    )


# ---------------------------------------------------------
# CONTACT NUMBER
# ---------------------------------------------------------

def generate_contact_number(number):
    """
    Generate a unique-looking demo contact number.
    """

    return f"90000{number:05d}"


# ---------------------------------------------------------
# DISABILITY / ACCESSIBILITY
# ---------------------------------------------------------

def generate_disability():

    if random.random() < DISABILITY_PERCENTAGE:

        return random.choice([
            "Wheelchair",
            "Visual Assistance",
            "Mobility Assistance"
        ])

    return None


# ---------------------------------------------------------
# GENDER
# ---------------------------------------------------------

def generate_gender():

    return random.choice([
        "Male",
        "Female"
    ])


# ---------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------

def generate_demo_students():

    random.seed(RANDOM_SEED)

    app = create_app()

    with app.app_context():

        print()
        print("=" * 70)
        print("ExamNexus - Demo Student Generator")
        print("=" * 70)
        print()

        # -------------------------------------------------
        # LOAD NAME FILES
        # -------------------------------------------------

        first_names, last_names = (
            load_first_and_last_names()
        )

        print(
            f"First names loaded : "
            f"{len(first_names)}"
        )

        print(
            f"Last names loaded  : "
            f"{len(last_names)}"
        )

        print()

        # -------------------------------------------------
        # GET COURSES
        # -------------------------------------------------

        courses = (
            Course.query
            .filter_by(is_active=True)
            .order_by(Course.id)
            .all()
        )

        if not courses:

            print(
                "ERROR: No active courses found."
            )

            print(
                "Create departments and courses "
                "before generating students."
            )

            return

        print(
            f"Active courses found: "
            f"{len(courses)}"
        )

        print()

        # -------------------------------------------------
        # CHECK EXISTING STUDENTS
        # -------------------------------------------------

        existing_students = Student.query.all()

        existing_count = len(
            existing_students
        )

        if existing_count > 0:

            print(
                f"WARNING: {existing_count} "
                f"students already exist."
            )

            print(
                "Existing students will NOT be deleted."
            )

            print(
                "Only new unique demo students "
                "will be added."
            )

            print()

        # -------------------------------------------------
        # CALCULATE MAXIMUM STUDENTS
        # -------------------------------------------------

        total_required = 0

        for course in courses:

            admission_years = (
                get_admission_years(course)
            )

            for admission_year in admission_years:

                semesters = (
                    get_current_semesters(
                        admission_year,
                        course
                    )
                )

                total_required += (
                    len(semesters)
                    * len(CLASSES)
                    * MAX_STUDENTS_PER_CLASS
                )

        print(
            "Maximum possible students: "
            f"{total_required}"
        )

        print()

        # -------------------------------------------------
        # GENERATE UNIQUE NAME POOL
        # -------------------------------------------------

        names = generate_unique_names(
            first_names,
            last_names,
            total_required
        )

        name_index = 0

        # -------------------------------------------------
        # TRACK EXISTING IDs / EMAILS
        # -------------------------------------------------

        existing_student_ids = {
            student.student_id
            for student in existing_students
        }

        existing_emails = {
            student.email
            for student in existing_students
        }

        # -------------------------------------------------
        # GENERATE STUDENTS
        # -------------------------------------------------

        students_to_insert = []

        global_number = existing_count + 1

        print("-" * 70)
        print("Generating students...")
        print("-" * 70)
        print()

        # -------------------------------------------------
        # EACH COURSE
        # -------------------------------------------------

        for course in courses:

            course_count = 0

            # -------------------------------------------------
            # GENERATE BATCHES
            # -------------------------------------------------

            admission_years = (
                get_admission_years(course)
            )

            for admission_year in admission_years:

                batch = generate_batch(
                    course,
                    admission_year
                )

                # -------------------------------------------------
                # DETERMINE SEMESTERS
                # -------------------------------------------------

                semesters = get_current_semesters(
                    admission_year,
                    course
                )

                # -------------------------------------------------
                # EACH SEMESTER
                # -------------------------------------------------

                for semester in semesters:

                    # -------------------------------------------------
                    # CLASS A / CLASS B
                    # -------------------------------------------------

                    for class_name in CLASSES:

                        number_of_students = random.randint(
                            MIN_STUDENTS_PER_CLASS,
                            MAX_STUDENTS_PER_CLASS
                        )

                        # -------------------------------------------------
                        # STUDENTS
                        # -------------------------------------------------

                        for class_number in range(
                            1,
                            number_of_students + 1
                        ):

                            # -----------------------------------------
                            # UNIQUE NAME
                            # -----------------------------------------

                            student_name = names[
                                name_index
                            ]

                            name_index += 1

                            # -----------------------------------------
                            # STUDENT ID
                            # -----------------------------------------

                            student_id = generate_student_id(
                                course=course,
                                batch=batch,
                                semester=semester,
                                class_name=class_name,
                                number=class_number
                            )

                            # -----------------------------------------
                            # SAFETY CHECK FOR STUDENT ID
                            # -----------------------------------------

                            if student_id in existing_student_ids:

                                print(
                                    f"Skipping duplicate "
                                    f"student ID: {student_id}"
                                )

                                continue

                            existing_student_ids.add(
                                student_id
                            )

                            # -----------------------------------------
                            # EMAIL
                            # -----------------------------------------

                            email = generate_email(
                                student_id
                            )

                            if email in existing_emails:

                                print(
                                    f"Skipping duplicate "
                                    f"email: {email}"
                                )

                                continue

                            existing_emails.add(
                                email
                            )

                            # -----------------------------------------
                            # OTHER DATA
                            # -----------------------------------------

                            dob = generate_dob()

                            contact_no = (
                                generate_contact_number(
                                    global_number
                                )
                            )

                            gender = generate_gender()

                            disability = (
                                generate_disability()
                            )

                            # -----------------------------------------
                            # CREATE STUDENT
                            # -----------------------------------------

                            student = Student(
                                student_id=student_id,
                                name=student_name,
                                course_id=course.id,
                                email=email,
                                password_hash=DEMO_PASSWORD_HASH,
                                contact_no=contact_no,
                                gender=gender,
                                disability=disability,

                                # Admission batch
                                batch=batch,

                                # Current semester
                                semester=semester,

                                # Class
                                class_name=class_name,

                                # Course session
                                session=course.session,

                                student_img=None,

                                email_verified=True,

                                two_factor_enabled=True,

                                is_active=True,

                                dob=dob
                            )

                            students_to_insert.append(
                                student
                            )

                            course_count += 1

                            global_number += 1

            print(
                f"{course.course_code:<15} "
                f"{course.course_name:<40} "
                f"{course_count:>5} students"
            )

        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        print()

        print("-" * 70)

        print(
            f"Generated students: "
            f"{len(students_to_insert)}"
        )

        print("-" * 70)

        print()

        if not students_to_insert:

            print(
                "No students generated."
            )

            return

        # -------------------------------------------------
        # INSERT IN CHUNKS
        # -------------------------------------------------

        CHUNK_SIZE = 500

        try:

            total = len(
                students_to_insert
            )

            for start in range(
                0,
                total,
                CHUNK_SIZE
            ):

                end = min(
                    start + CHUNK_SIZE,
                    total
                )

                chunk = students_to_insert[
                    start:end
                ]

                db.session.add_all(
                    chunk
                )

                db.session.commit()

                print(
                    f"Inserted {end}/{total}"
                )

        except Exception as error:

            db.session.rollback()

            print()

            print(
                "ERROR while inserting students:"
            )

            print(error)

            return

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        final_count = Student.query.count()

        print()

        print("=" * 70)
        print("DEMO STUDENT GENERATION COMPLETE")
        print("=" * 70)

        print()

        print(
            f"Students currently in PostgreSQL: "
            f"{final_count}"
        )

        print()

        print(
            "Demo password: "
            f"{DEMO_PASSWORD}"
        )

        print(
            "Only the hashed password is stored "
            "in PostgreSQL."
        )

        print()

        print("=" * 70)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    generate_demo_students()