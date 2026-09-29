import random
import sys

from pathlib import Path


# ---------------------------------------------------------
# MAKE BACKEND AVAILABLE TO PYTHON
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app import create_app, db
from app.models.hall import Hall
from app.models.course import Course


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

RANDOM_SEED = 42

# Total halls to generate
NUM_HALLS = 148

# ---------------------------------------------------------
# CLASSROOM SETTINGS
# ---------------------------------------------------------

CLASS_BUILDINGS = [
    "The Nexus Institute",
    "The Quantum Hall",
    "The Insight Pavilion",
    "The Luminary Tower",
    "The Cognition Hub",
    "The Horizon Forum",
    "The Idea Foundry",
    "The Vanguard Annex",
]

CLASS_FLOORS_PER_BUILDING = 3

ROOMS_PER_CLASS_FLOOR = 2


# ---------------------------------------------------------
# LAB SETTINGS
# ---------------------------------------------------------

LAB_BUILDING = "The Experimental Hub"

LAB_FLOORS = 6

LAB_ROOM_COUNT = 100


# ---------------------------------------------------------
# CAPACITY
# ---------------------------------------------------------

MIN_CAPACITY = 60
MAX_CAPACITY = 69


# ---------------------------------------------------------
# EXAMINATION CAPACITY
# ---------------------------------------------------------

MIN_EXAM_CAPACITY = 40
MAX_EXAM_CAPACITY = 60


# ---------------------------------------------------------
# ROOM TYPES
# ---------------------------------------------------------

ROOM_TYPES = [
    "Class",
    "Lab",
]


# ---------------------------------------------------------
# AMENITIES
# ---------------------------------------------------------

AVAILABLE_AMENITIES = [
    "Projector",
    "Whiteboard",
    "Computer",
    "Speakers",
    "Microphone",
    "Air Conditioning",
]


# ---------------------------------------------------------
# ACCESSIBILITY
# ---------------------------------------------------------

# Based on your student accessibility requirements:
#
# Mobility Assistance
# Visual Assistance
# Wheelchair
#
# We make most halls accessible so that the
# examination system has enough accessible rooms.

ACCESSIBLE_PERCENTAGE = 0.30

# Minimum examination capacity that must be available
# in accessible ground-floor (floor 0) halls.
MIN_ACCESSIBLE_GROUND_FLOOR_CAPACITY = 500


# ---------------------------------------------------------
# LOAD ACTIVE COURSES
# ---------------------------------------------------------

def get_active_courses():

    return (
        Course.query
        .filter_by(
            is_active=True
        )
        .order_by(
            Course.course_code
        )
        .all()
    )


# ---------------------------------------------------------
# GENERATE AMENITIES
# ---------------------------------------------------------

def generate_amenities():

    number_of_amenities = random.randint(
        2,
        len(AVAILABLE_AMENITIES)
    )

    selected_amenities = random.sample(
        AVAILABLE_AMENITIES,
        number_of_amenities
    )

    return ", ".join(
        selected_amenities
    )


# ---------------------------------------------------------
# GENERATE CAPACITY
# ---------------------------------------------------------

def generate_capacity():

    return random.randint(
        MIN_CAPACITY,
        MAX_CAPACITY
    )


# ---------------------------------------------------------
# GENERATE EXAMINATION CAPACITY
# ---------------------------------------------------------

def generate_examination_capacity(
    capacity
):
    """
    Examination capacity should never be greater
    than the normal room capacity.

    Example:

        Capacity: 65
        Examination capacity: 50
    """

    maximum = min(
        capacity,
        MAX_EXAM_CAPACITY
    )

    minimum = min(
        MIN_EXAM_CAPACITY,
        maximum
    )

    return random.randint(
        minimum,
        maximum
    )


# ---------------------------------------------------------
# GENERATE ACCESSIBILITY
# ---------------------------------------------------------

def generate_accessibility():

    return (
        random.random()
        < ACCESSIBLE_PERCENTAGE
    )


# ---------------------------------------------------------
# GENERATE COURSE ASSIGNMENT
# ---------------------------------------------------------

def generate_course_assignment(
    courses
):
    """
    Select an active course.

    The hall's assigned batch is derived from
    the selected course's study_shift.

    Example:

        CSEM01 -> Morning
        CSEA01 -> Afternoon
        MEM01  -> Morning
        MEA01  -> Afternoon
    """

    if not courses:
        return None, None

    course = random.choice(
        courses
    )

    assigned_batch = (
        course.study_shift
    )

    return (
        course,
        assigned_batch
    )


# ---------------------------------------------------------
# CREATE HALL OBJECT
# ---------------------------------------------------------

def create_hall(
    hall_name,
    building_name,
    floor_no,
    room_type,
    courses
):

    capacity = generate_capacity()

    examination_capacity = (
        generate_examination_capacity(
            capacity
        )
    )

    is_accessible = (
    True
    if floor_no == 0
    else generate_accessibility()
)

    course, assigned_batch = (
        generate_course_assignment(
            courses
        )
    )

    hall = Hall(

        name=hall_name,

        building_name=building_name,

        floor_no=floor_no,

        capacity=capacity,

        examination_capacity=(
            examination_capacity
        ),

        room_type=room_type,

        amenities=generate_amenities(),

        is_available=True,

        is_under_maintenance=False,

        is_accessible=is_accessible,

        assigned_course_id=(
            course.id
            if course
            else None
        ),

        assigned_batch=assigned_batch,

        is_active=True
    )

    return hall


# ---------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------

def generate_demo_halls():

    random.seed(
        RANDOM_SEED
    )

    app = create_app()

    with app.app_context():

        print()
        print("=" * 80)
        print("ExamNexus - Demo Hall Generator")
        print("=" * 80)
        print()

        # -------------------------------------------------
        # GET COURSES
        # -------------------------------------------------

        courses = get_active_courses()

        if not courses:

            print(
                "ERROR: No active courses found."
            )

            print(
                "Create courses before generating halls."
            )

            return

        print(
            f"Active courses found: "
            f"{len(courses)}"
        )

        print()

        # -------------------------------------------------
        # SHOW COURSE / SHIFT MAPPING
        # -------------------------------------------------

        print("-" * 80)
        print("Course / Department / Shift Mapping")
        print("-" * 80)

        for course in courses:

            department_name = (
                course.department.department_name
                if course.department
                else "Unknown"
            )

            print(
                f"{course.course_code:<10} | "
                f"{department_name:<25} | "
                f"{course.course_name:<40} | "
                f"{course.study_shift:<10} | "
                f"{course.session}"
            )

        print()

        # -------------------------------------------------
        # CHECK EXISTING HALLS
        # -------------------------------------------------

        existing_halls = (
            Hall.query.all()
        )

        existing_count = len(
            existing_halls
        )

        if existing_count > 0:

            print(
                f"WARNING: {existing_count} "
                f"halls already exist."
            )

            print(
                "Existing halls will NOT be deleted."
            )

            print(
                "Only new halls will be added."
            )

            print()

        # -------------------------------------------------
        # GENERATE HALLS
        # -------------------------------------------------

        halls_to_insert = []

        accessible_ground_floor_capacity = 0

        print("-" * 80)
        print("Generating halls...")
        print("-" * 80)
        print()

        hall_number = (
            existing_count + 1
        )

        # -------------------------------------------------
        # CLASS HALLS
        # -------------------------------------------------

        class_hall_count = 0

        for building in CLASS_BUILDINGS:

            for floor_no in range(
    0,
    CLASS_FLOORS_PER_BUILDING
):

                for floor_no in range(
    0,
    LAB_FLOORS
):
                    if (
                        len(halls_to_insert)
                        >= NUM_HALLS
                    ):
                        break

                    hall_name = (
                        f"Hall {hall_number:03d}"
                    )

                    hall = create_hall(

                        hall_name=hall_name,

                        building_name=building,

                        floor_no=floor_no,

                        room_type="Class",

                        courses=courses
                    )

                    halls_to_insert.append(
                        hall
                    )

                    class_hall_count += 1

                    course_code = (
                        Course.query.get(
                            hall.assigned_course_id
                        ).course_code
                        if hall.assigned_course_id
                        else "-"
                    )

                    print(
                        f"{hall_name:<12} | "
                        f"{building:<30} | "
                        f"Floor {floor_no:<2} | "
                        f"{hall.room_type:<6} | "
                        f"Capacity: "
                        f"{hall.capacity:<2} | "
                        f"Exam: "
                        f"{hall.examination_capacity:<2} | "
                        f"{course_code:<10} | "
                        f"{hall.assigned_batch or '-':<10} | "
                        f"{'Accessible' if hall.is_accessible else 'Standard'}"
                    )

                    hall_number += 1

                if (
                    len(halls_to_insert)
                    >= NUM_HALLS
                ):
                    break

            if (
                len(halls_to_insert)
                >= NUM_HALLS
            ):
                break

        # -------------------------------------------------
        # LAB HALLS
        # -------------------------------------------------

        lab_hall_count = 0

        if len(halls_to_insert) < NUM_HALLS:

            for floor_no in range(
                1,
                LAB_FLOORS + 1
            ):

                for room_no in range(
                    1,
                    LAB_ROOM_COUNT + 1
                ):

                    if (
                        len(halls_to_insert)
                        >= NUM_HALLS
                    ):
                        break

                    hall_name = (
                        f"Lab {hall_number:03d}"
                    )

                    hall = create_hall(

                        hall_name=hall_name,

                        building_name=LAB_BUILDING,

                        floor_no=floor_no,

                        room_type="Lab",

                        courses=courses
                    )

                    halls_to_insert.append(
                        hall
                    )

                    lab_hall_count += 1

                    course_code = (
                        Course.query.get(
                            hall.assigned_course_id
                        ).course_code
                        if hall.assigned_course_id
                        else "-"
                    )

                    print(
                        f"{hall_name:<12} | "
                        f"{LAB_BUILDING:<30} | "
                        f"Floor {floor_no:<2} | "
                        f"{hall.room_type:<6} | "
                        f"Capacity: "
                        f"{hall.capacity:<2} | "
                        f"Exam: "
                        f"{hall.examination_capacity:<2} | "
                        f"{course_code:<10} | "
                        f"{hall.assigned_batch or '-':<10} | "
                        f"{'Accessible' if hall.is_accessible else 'Standard'}"
                    )

                    hall_number += 1

                if (
                    len(halls_to_insert)
                    >= NUM_HALLS
                ):
                    break

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        print()

        print("-" * 80)

        print(
            f"Class halls generated: "
            f"{class_hall_count}"
        )

        print(
            f"Lab halls generated: "
            f"{lab_hall_count}"
        )

        print(
            f"Total halls generated: "
            f"{len(halls_to_insert)}"
        )

        print("-" * 80)

        print()

        if not halls_to_insert:

            print(
                "No halls generated."
            )

            return

        # -------------------------------------------------
        # INSERT IN CHUNKS
        # -------------------------------------------------

        CHUNK_SIZE = 50

        try:

            total = len(
                halls_to_insert
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

                chunk = halls_to_insert[
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
                "ERROR while inserting halls:"
            )

            print(error)

            return

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        final_count = (
            Hall.query.count()
        )

        accessible_count = (
            Hall.query
            .filter_by(
                is_accessible=True
            )
            .count()
        )

        available_count = (
            Hall.query
            .filter_by(
                is_available=True
            )
            .count()
        )

        maintenance_count = (
            Hall.query
            .filter_by(
                is_under_maintenance=True
            )
            .count()
        )

        print()

        print("=" * 80)
        print("DEMO HALL GENERATION COMPLETE")
        print("=" * 80)

        print()

        print(
            f"Halls currently in database: "
            f"{final_count}"
        )

        print(
            f"Accessible halls: "
            f"{accessible_count}"
        )

        print(
            f"Available halls: "
            f"{available_count}"
        )

        print(
            f"Under maintenance: "
            f"{maintenance_count}"
        )

        print()

        print("=" * 80)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    generate_demo_halls()
