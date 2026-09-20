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
from app.models.staff import Staff
from app.models.department import Department
from app.models.course import Course


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

RANDOM_SEED = 42

NUM_STAFF = 100

DEMO_PASSWORD = "Demo@123"

DEMO_PASSWORD_HASH = generate_password_hash(
    DEMO_PASSWORD
)


# ---------------------------------------------------------
# STAFF OPTIONS
# ---------------------------------------------------------

DESIGNATIONS = [
    "Professor",
    "Assistant Professor",
    "Lab Assistant",
]

GENDERS = [
    "Male",
    "Female",
]


# Staff availability is Boolean in the model.
#
# True  = Available
# False = Unavailable

AVAILABILITY = [
    True,
    False,
]


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

    random.shuffle(
        possible_names
    )

    return possible_names[:required_count]


# ---------------------------------------------------------
# DATE OF BIRTH
# ---------------------------------------------------------

def generate_dob(
    age_min=25,
    age_max=60
):
    """
    Generate a realistic staff date of birth.
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
# STAFF DISPLAY ID
# ---------------------------------------------------------

def generate_staff_id(number):
    """
    Generate a display/login identifier.

    The Staff model does NOT have a separate
    staff_id column.

    Therefore this is only used for email generation
    and console output.

    Examples:

        STF001
        STF002
        STF003
    """

    return f"STF{number:03d}"


# ---------------------------------------------------------
# EMAIL
# ---------------------------------------------------------

def generate_email(staff_id):
    """
    Generate a unique demo email.
    """

    return (
        f"{staff_id.lower()}"
        f"@examnexus.edu"
    )


# ---------------------------------------------------------
# CONTACT NUMBER
# ---------------------------------------------------------

def generate_contact_number(number):
    """
    Generate a unique demo contact number.
    """

    return f"90000{number:05d}"


# ---------------------------------------------------------
# GET COURSES FOR DEPARTMENT
# ---------------------------------------------------------

def get_courses_for_department(
    department_id
):
    """
    Get active courses belonging to
    the selected department.
    """

    return (
        Course.query
        .filter_by(
            department_id=department_id,
            is_active=True
        )
        .order_by(
            Course.course_code
        )
        .all()
    )


# ---------------------------------------------------------
# ASSIGNED COURSES
# ---------------------------------------------------------

def generate_assigned_courses(
    department_courses
):
    """
    Assign 1 to 3 courses to a staff member.

    IMPORTANT:

    Courses are selected ONLY from the staff
    member's department.

    Example:

        Engineering staff
        ->
        CSEM01,CSEA01

    The course codes are stored as a comma-separated
    string because Staff.assigned_courses is a Text field.
    """

    if not department_courses:
        return None

    max_courses = min(
        3,
        len(department_courses)
    )

    number_of_courses = random.randint(
        1,
        max_courses
    )

    selected_courses = random.sample(
        department_courses,
        number_of_courses
    )

    return ",".join(
        course.course_code
        for course in selected_courses
    )


# ---------------------------------------------------------
# ASSIGNED BATCH
# ---------------------------------------------------------

def generate_assigned_batch(
    department_courses,
    assigned_courses
):
    """
    Generate the staff assigned batch from
    the study_shift of one of the assigned courses.

    Example:

        CSEM01 -> Morning
        CSEA01 -> Afternoon

    Therefore, if a staff member is assigned:

        CSEM01,CSEA01

    one of those courses is selected and its
    study_shift becomes the assigned_batch.
    """

    if not assigned_courses:

        return None

    # Convert:
    #
    # "CSEM01,CSEA01"
    #
    # into:
    #
    # ["CSEM01", "CSEA01"]

    assigned_course_codes = (
        assigned_courses.split(",")
    )

    # Select one assigned course

    selected_code = random.choice(
        assigned_course_codes
    )

    # Find that course in the department

    for course in department_courses:

        if course.course_code == selected_code:

            return course.study_shift

    return None


# ---------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------

def generate_demo_staff():

    random.seed(
        RANDOM_SEED
    )

    app = create_app()

    with app.app_context():

        print()
        print("=" * 80)
        print("ExamNexus - Demo Staff Generator")
        print("=" * 80)
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
        # GET ACTIVE DEPARTMENTS
        # -------------------------------------------------

        departments = (
            Department.query
            .filter_by(
                is_active=True
            )
            .order_by(
                Department.id
            )
            .all()
        )

        if not departments:

            print(
                "ERROR: No active departments found."
            )

            print(
                "Run your department/course generator first."
            )

            return

        print(
            f"Active departments found: "
            f"{len(departments)}"
        )

        print()

        # -------------------------------------------------
        # DEPARTMENT / COURSE MAPPING
        # -------------------------------------------------

        print("-" * 80)
        print("Department / Course Mapping")
        print("-" * 80)

        department_courses_map = {}

        valid_departments = []

        for department in departments:

            department_courses = (
                get_courses_for_department(
                    department.id
                )
            )

            if not department_courses:

                print(
                    f"{department.department_name:<30} "
                    f"| No active courses"
                )

                continue

            department_courses_map[
                department.id
            ] = department_courses

            valid_departments.append(
                department
            )

            course_details = ", ".join(
                f"{course.course_code}="
                f"{course.study_shift}"
                for course in department_courses
            )

            print(
                f"{department.department_name:<30} "
                f"| {course_details}"
            )

        print()

        if not valid_departments:

            print(
                "ERROR: No departments have "
                "active courses."
            )

            return

        # -------------------------------------------------
        # CHECK EXISTING STAFF
        # -------------------------------------------------

        existing_staff = (
            Staff.query.all()
        )

        existing_count = len(
            existing_staff
        )

        if existing_count > 0:

            print(
                f"WARNING: {existing_count} "
                f"staff members already exist."
            )

            print(
                "Existing staff will NOT be deleted."
            )

            print(
                "Only new unique staff will be added."
            )

            print()

        # -------------------------------------------------
        # GENERATE UNIQUE NAME POOL
        # -------------------------------------------------

        names = generate_unique_names(
            first_names,
            last_names,
            NUM_STAFF
        )

        name_index = 0

        # -------------------------------------------------
        # EXISTING EMAILS
        # -------------------------------------------------

        existing_emails = {
            staff.email
            for staff in existing_staff
        }

        # -------------------------------------------------
        # GENERATE STAFF
        # -------------------------------------------------

        staff_to_insert = []

        generated_count = 0

        staff_number = existing_count + 1

        print("-" * 80)
        print("Generating staff...")
        print("-" * 80)
        print()

        while generated_count < NUM_STAFF:

            # ---------------------------------------------
            # SELECT DEPARTMENT
            # ---------------------------------------------

            department = random.choice(
                valid_departments
            )

            department_courses = (
                department_courses_map[
                    department.id
                ]
            )

            # ---------------------------------------------
            # NAME
            # ---------------------------------------------

            staff_name = names[
                name_index
            ]

            name_index += 1

            # ---------------------------------------------
            # STAFF DISPLAY ID
            # ---------------------------------------------

            staff_id = generate_staff_id(
                staff_number
            )

            staff_number += 1

            # ---------------------------------------------
            # EMAIL
            # ---------------------------------------------

            email = generate_email(
                staff_id
            )

            if email in existing_emails:

                continue

            existing_emails.add(
                email
            )

            # ---------------------------------------------
            # DESIGNATION
            # ---------------------------------------------

            designation = random.choice(
                DESIGNATIONS
            )

            # ---------------------------------------------
            # GENDER
            # ---------------------------------------------

            gender = random.choice(
                GENDERS
            )

            # ---------------------------------------------
            # DATE OF BIRTH
            # ---------------------------------------------

            dob = generate_dob()

            # ---------------------------------------------
            # CONTACT NUMBER
            # ---------------------------------------------

            contact_no = (
                generate_contact_number(
                    generated_count + 1
                )
            )

            # ---------------------------------------------
            # ASSIGNED COURSES
            # ---------------------------------------------

            assigned_courses = (
                generate_assigned_courses(
                    department_courses
                )
            )

            # ---------------------------------------------
            # ASSIGNED BATCH
            #
            # IMPORTANT:
            #
            # The batch now comes from the course
            # study_shift.
            # ---------------------------------------------

            assigned_batch = (
                generate_assigned_batch(
                    department_courses,
                    assigned_courses
                )
            )

            # ---------------------------------------------
            # AVAILABILITY
            # ---------------------------------------------

            availability = random.choice(
                AVAILABILITY
            )

            # ---------------------------------------------
            # CREATE STAFF OBJECT
            # ---------------------------------------------

            staff = Staff(

                name=staff_name,

                department_id=department.id,

                email=email,

                contact_no=contact_no,

                designation=designation,

                dob=dob,

                assigned_courses=assigned_courses,

                gender=gender,

                availability=availability,

                assigned_batch=assigned_batch,

                password_hash=DEMO_PASSWORD_HASH,

                image=None,

                is_active=True
            )

            staff_to_insert.append(
                staff
            )

            generated_count += 1

            # ---------------------------------------------
            # DISPLAY
            # ---------------------------------------------

            print(
                f"{staff_id:<8} | "
                f"{staff_name:<30} | "
                f"{department.department_name:<25} | "
                f"{designation:<20} | "
                f"{assigned_courses or '-':<20} | "
                f"{assigned_batch or '-':<10} | "
                f"{'Available' if availability else 'Unavailable'}"
            )

        # -------------------------------------------------
        # INSERT
        # -------------------------------------------------

        print()

        print("-" * 80)

        print(
            f"Generated staff: "
            f"{len(staff_to_insert)}"
        )

        print("-" * 80)

        print()

        if not staff_to_insert:

            print(
                "No staff generated."
            )

            return

        # -------------------------------------------------
        # INSERT IN CHUNKS
        # -------------------------------------------------

        CHUNK_SIZE = 50

        try:

            total = len(
                staff_to_insert
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

                chunk = staff_to_insert[
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
                "ERROR while inserting staff:"
            )

            print(error)

            return

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        final_count = Staff.query.count()

        print()

        print("=" * 80)
        print("DEMO STAFF GENERATION COMPLETE")
        print("=" * 80)

        print()

        print(
            f"Staff currently in database: "
            f"{final_count}"
        )

        print()

        print(
            f"Demo password: "
            f"{DEMO_PASSWORD}"
        )

        print(
            "Only the hashed password is stored "
            "in the database."
        )

        print()

        print("=" * 80)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    generate_demo_staff()
