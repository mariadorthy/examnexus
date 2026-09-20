import random

from app import create_app, db
from app.models.course import Course
from app.models.subject import Subject


# =========================================================
# CONFIGURATION
# =========================================================

RANDOM_SEED = 42


# =========================================================
# SUBJECT CURRICULUM
# =========================================================
#
# Structure:
#
# COURSE NAME
#   -> PROGRAM LEVEL
#       -> SEMESTER
#           -> core
#           -> elective
#           -> lab
#
# Subject Type stored in database:
#
#   Core
#   Elective
#   Lab
#
# =========================================================

SUBJECT_LIST = {

    # =====================================================
    # COMPUTER SCIENCE ENGINEERING
    # =====================================================

    "Computer Science Engineering": {

        "UG": {

            1: {
                "core": [
                    "Mathematics I",
                    "Basic Programming",
                    "Digital Logic Design",
                    "Computer Organization",
                    "Discrete Mathematics",
                ],
                "elective": [],
                "lab": [
                    "Basic Programming"
                ],
            },

            2: {
                "core": [
                    "Data Structures",
                    "Object-Oriented Programming",
                    "Operating Systems",
                    "Database Management Systems",
                    "Software Engineering",
                ],
                "elective": [],
                "lab": [
                    "Object-Oriented Programming",
                    "Database Management Systems",
                ],
            },

            3: {
                "core": [
                    "Computer Networks",
                    "Algorithms",
                    "Web Development",
                    "Cybersecurity Basics",
                    "Probability and Statistics",
                ],
                "elective": [],
                "lab": [
                    "Web Development"
                ],
            },

            4: {
                "core": [
                    "Theory of Computation",
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Cloud Computing",
                    "Blockchain Technology",
                ],
                "elective": [],
                "lab": [
                    "Machine Learning"
                ],
            },

            5: {
                "core": [
                    "Big Data Analytics",
                    "IoT",
                    "Advanced Networking",
                    "Mobile App Development",
                    "Human-Computer Interaction",
                ],
                "elective": [
                    "IoT",
                    "Big Data Analytics",
                ],
                "lab": [
                    "Mobile App Development"
                ],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Research Methods",
                    "Distributed Systems",
                    "Advanced Algorithms",
                    "Cyber-Physical Systems",
                ],
                "elective": [
                    "Distributed Systems",
                    "Cyber-Physical Systems",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Advanced Software Engineering",
                    "Compiler Design",
                    "Advanced Computer Networks",
                    "Information Security",
                    "Professional Practice",
                ],
                "elective": [
                    "Information Security"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "Project Management",
                    "Research Seminar",
                    "Technical Entrepreneurship",
                    "Professional Ethics",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # MECHANICAL ENGINEERING
    # =====================================================

    "Mechanical Engineering": {

        "UG": {

            1: {
                "core": [
                    "Engineering Mechanics",
                    "Mathematics I",
                    "Physics I",
                    "Chemistry",
                    "Basic Electrical Engineering",
                ],
                "elective": [],
                "lab": [],
            },

            2: {
                "core": [
                    "Fluid Mechanics",
                    "Thermodynamics",
                    "Strength of Materials",
                    "Mathematics II",
                    "Manufacturing Processes",
                ],
                "elective": [],
                "lab": [
                    "Fluid Mechanics",
                    "Strength of Materials",
                ],
            },

            3: {
                "core": [
                    "Machine Design",
                    "Material Science",
                    "Heat Transfer",
                    "Dynamics of Machinery",
                    "Machine Tools",
                ],
                "elective": [],
                "lab": [
                    "Heat Transfer"
                ],
            },

            4: {
                "core": [
                    "Mechanical Vibrations",
                    "Refrigeration and Air Conditioning",
                    "Control Systems",
                    "Production Planning",
                    "Finite Element Analysis",
                ],
                "elective": [],
                "lab": [
                    "Refrigeration and Air Conditioning"
                ],
            },

            5: {
                "core": [
                    "Energy Systems",
                    "Internal Combustion Engines",
                    "Renewable Energy",
                    "CAD/CAM",
                    "Automobile Engineering",
                ],
                "elective": [
                    "Automobile Engineering",
                    "Renewable Energy",
                ],
                "lab": [
                    "Internal Combustion Engines"
                ],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Industrial Training",
                    "Operations Research",
                    "Engineering Management",
                    "Advanced Mechanics",
                ],
                "elective": [],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Advanced Machine Design",
                    "Mechatronics",
                    "Advanced Manufacturing",
                    "Industrial Engineering",
                    "Engineering Economics",
                ],
                "elective": [
                    "Mechatronics"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "Professional Practice",
                    "Engineering Management",
                    "Research Seminar",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # CIVIL ENGINEERING
    # =====================================================

    "Civil Engineering": {

        "UG": {

            1: {
                "core": [
                    "Mathematics I",
                    "Engineering Mechanics",
                    "Surveying",
                    "Basic Civil Engineering",
                    "Physics I",
                ],
                "elective": [],
                "lab": [],
            },

            2: {
                "core": [
                    "Building Materials",
                    "Strength of Materials",
                    "Fluid Mechanics",
                    "Surveying Practice",
                    "Structural Analysis I",
                ],
                "elective": [],
                "lab": [
                    "Surveying Practice"
                ],
            },

            3: {
                "core": [
                    "Concrete Technology",
                    "Soil Mechanics",
                    "Environmental Engineering",
                    "Structural Analysis II",
                    "Transportation Engineering",
                ],
                "elective": [],
                "lab": [
                    "Concrete Technology",
                    "Soil Mechanics",
                ],
            },

            4: {
                "core": [
                    "Hydraulic Engineering",
                    "Geotechnical Engineering",
                    "Construction Management",
                    "Structural Design",
                    "Building Services",
                ],
                "elective": [],
                "lab": [],
            },

            5: {
                "core": [
                    "Water Resources Engineering",
                    "Earthquake Engineering",
                    "Advanced Structural Design",
                    "Municipal Engineering",
                    "Urban Planning",
                ],
                "elective": [
                    "Earthquake Engineering",
                    "Urban Planning",
                ],
                "lab": [],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Research Methodology",
                    "Professional Practice",
                    "Construction Technology",
                    "Infrastructure Development",
                ],
                "elective": [],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Advanced Structural Engineering",
                    "Advanced Geotechnical Engineering",
                    "Construction Planning",
                    "Environmental Management",
                    "Infrastructure Planning",
                ],
                "elective": [
                    "Infrastructure Planning"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "Professional Practice",
                    "Construction Management",
                    "Research Seminar",
                    "Engineering Economics",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # INFORMATION TECHNOLOGY
    # =====================================================

    "Information Technology": {

        "UG": {

            1: {
                "core": [
                    "Mathematics I",
                    "Introduction to Programming",
                    "Digital Logic Design",
                    "Computer Organization",
                    "Introduction to IT",
                ],
                "elective": [],
                "lab": [
                    "Introduction to Programming"
                ],
            },

            2: {
                "core": [
                    "Data Structures",
                    "Object-Oriented Programming",
                    "Database Management Systems",
                    "Operating Systems",
                    "Web Development",
                ],
                "elective": [],
                "lab": [
                    "Object-Oriented Programming",
                    "Web Development",
                ],
            },

            3: {
                "core": [
                    "Computer Networks",
                    "Algorithms",
                    "Software Engineering",
                    "Cybersecurity Basics",
                    "Discrete Mathematics",
                ],
                "elective": [],
                "lab": [
                    "Software Engineering"
                ],
            },

            4: {
                "core": [
                    "Cloud Computing",
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Computer Graphics",
                    "Mobile Computing",
                ],
                "elective": [],
                "lab": [],
            },

            5: {
                "core": [
                    "Big Data Analytics",
                    "IoT",
                    "Blockchain Technology",
                    "Advanced Database Systems",
                    "Human-Computer Interaction",
                ],
                "elective": [
                    "Blockchain Technology",
                    "Human-Computer Interaction",
                ],
                "lab": [],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Advanced Networking",
                    "Research Methods",
                    "Cyber-Physical Systems",
                    "Distributed Systems",
                ],
                "elective": [
                    "Distributed Systems",
                    "Cyber-Physical Systems",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Cloud Architecture",
                    "Advanced Web Technologies",
                    "IT Service Management",
                    "Enterprise Systems",
                    "Information Security",
                ],
                "elective": [
                    "Enterprise Systems"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "IT Governance",
                    "Research Seminar",
                    "Professional Ethics",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # ELECTRICAL AND ELECTRONICS ENGINEERING
    # =====================================================

    "Electrical and Electronics Engineering": {

        "UG": {

            1: {
                "core": [
                    "Mathematics I",
                    "Basic Electrical Engineering",
                    "Electronics Devices",
                    "Digital Electronics",
                    "Engineering Physics",
                ],
                "elective": [],
                "lab": [
                    "Digital Electronics"
                ],
            },

            2: {
                "core": [
                    "Circuit Theory",
                    "Electromagnetic Fields",
                    "Signals and Systems",
                    "Analog Electronics",
                    "Control Systems",
                ],
                "elective": [],
                "lab": [
                    "Signals and Systems",
                    "Analog Electronics",
                ],
            },

            3: {
                "core": [
                    "Electrical Machines",
                    "Power Systems",
                    "Power Electronics",
                    "Microprocessors",
                    "Signals and Communication",
                ],
                "elective": [],
                "lab": [
                    "Power Electronics",
                    "Microprocessors",
                ],
            },

            4: {
                "core": [
                    "Electrical Drives",
                    "Renewable Energy",
                    "Advanced Control Systems",
                    "Electrical Measurements",
                    "VLSI Design",
                ],
                "elective": [
                    "Renewable Energy",
                    "Electrical Measurements",
                ],
                "lab": [
                    "VLSI Design"
                ],
            },

            5: {
                "core": [
                    "Power Distribution",
                    "High Voltage Engineering",
                    "Microcontroller Applications",
                    "Electrical Engineering Design",
                    "Embedded Systems",
                ],
                "elective": [
                    "High Voltage Engineering",
                    "Embedded Systems",
                ],
                "lab": [
                    "Microcontroller Applications"
                ],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Industrial Training",
                    "Research Methodology",
                    "Power System Protection",
                    "Smart Grids",
                ],
                "elective": [
                    "Smart Grids"
                ],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Advanced Power Systems",
                    "Power Quality",
                    "Electric Vehicle Technology",
                    "Smart Grid Technology",
                    "Industrial Automation",
                ],
                "elective": [
                    "Electric Vehicle Technology"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "Professional Practice",
                    "Research Seminar",
                    "Engineering Management",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # ELECTRONICS AND COMMUNICATION ENGINEERING
    # =====================================================

    "Electronics and Communication Engineering": {

        "UG": {

            1: {
                "core": [
                    "Mathematics I",
                    "Basic Electronics",
                    "Electrical Engineering",
                    "Digital Logic Design",
                    "Electromagnetic Theory",
                ],
                "elective": [],
                "lab": [
                    "Basic Electronics",
                    "Digital Logic Design",
                ],
            },

            2: {
                "core": [
                    "Signals and Systems",
                    "Analog Electronics",
                    "Communication Systems",
                    "Electromagnetic Waves",
                    "Microprocessors",
                ],
                "elective": [],
                "lab": [
                    "Analog Electronics",
                    "Microprocessors",
                ],
            },

            3: {
                "core": [
                    "Digital Communication",
                    "Microcontrollers",
                    "VLSI Design",
                    "Control Systems",
                    "Embedded Systems",
                ],
                "elective": [],
                "lab": [
                    "VLSI Design",
                    "Embedded Systems",
                ],
            },

            4: {
                "core": [
                    "Wireless Communication",
                    "Optical Fiber Communication",
                    "Digital Signal Processing",
                    "Communication Networks",
                    "Power Electronics",
                ],
                "elective": [],
                "lab": [
                    "Digital Signal Processing",
                    "Communication Networks",
                ],
            },

            5: {
                "core": [
                    "Advanced Communication Systems",
                    "Radar Systems",
                    "Satellite Communication",
                    "Nanoelectronics",
                    "Signal Processing Algorithms",
                ],
                "elective": [
                    "Advanced Communication Systems",
                    "Nanoelectronics",
                ],
                "lab": [],
            },

            6: {
                "core": [
                    "Capstone Project",
                    "Industrial Training",
                    "Research Methods",
                    "IoT and Embedded Systems",
                    "Advanced Electronics",
                ],
                "elective": [
                    "IoT and Embedded Systems",
                    "Advanced Electronics",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },

            7: {
                "core": [
                    "Advanced VLSI Design",
                    "5G Communication",
                    "Embedded System Design",
                    "Advanced Signal Processing",
                    "Optical Networks",
                ],
                "elective": [
                    "5G Communication"
                ],
                "lab": []
            },

            8: {
                "core": [
                    "Major Project",
                    "Research Seminar",
                    "Professional Practice",
                    "Technical Entrepreneurship",
                    "Engineering Management",
                ],
                "elective": [],
                "lab": [
                    "Major Project"
                ]
            },
        }
    },


    # =====================================================
    # MASTER OF BUSINESS ADMINISTRATION
    # =====================================================

    "Master of Business Administration": {

        "PG": {

            1: {
                "core": [
                    "Managerial Economics",
                    "Organizational Behavior",
                    "Business Communication",
                    "Marketing Management",
                    "Financial Accounting",
                ],
                "elective": [],
                "lab": [],
            },

            2: {
                "core": [
                    "Operations Management",
                    "Human Resource Management",
                    "Business Strategy",
                    "Macroeconomics",
                    "Financial Management",
                ],
                "elective": [],
                "lab": [],
            },

            3: {
                "core": [
                    "International Business",
                    "Entrepreneurship",
                    "Business Analytics",
                    "Marketing Research",
                    "Managerial Accounting",
                ],
                "elective": [],
                "lab": [],
            },

            4: {
                "core": [
                    "Capstone Project",
                    "Business Ethics",
                    "Corporate Governance",
                    "Supply Chain Management",
                    "Leadership in Organizations",
                ],
                "elective": [],
                "lab": [
                    "Capstone Project"
                ],
            },
        }
    },


    # =====================================================
    # MASTER OF COMPUTER APPLICATIONS
    # =====================================================

    "Master of Computer Applications": {

        "PG": {

            1: {
                "core": [
                    "Discrete Mathematics",
                    "Programming in C",
                    "Data Structures",
                    "Computer Organization",
                    "Database Management Systems",
                ],
                "elective": [],
                "lab": [
                    "Programming in C",
                    "Data Structures",
                ],
            },

            2: {
                "core": [
                    "Object-Oriented Programming",
                    "Software Engineering",
                    "Operating Systems",
                    "Web Technologies",
                    "Data Mining",
                ],
                "elective": [],
                "lab": [
                    "Object-Oriented Programming",
                    "Web Technologies",
                ],
            },

            3: {
                "core": [
                    "Computer Networks",
                    "Mobile Computing",
                    "Artificial Intelligence",
                    "Cloud Computing",
                    "Information Security",
                ],
                "elective": [],
                "lab": [
                    "Mobile Computing",
                    "Artificial Intelligence",
                ],
            },

            4: {
                "core": [
                    "Capstone Project",
                    "Advanced Databases",
                    "Software Development Life Cycle",
                    "Research Methodology",
                    "Distributed Computing",
                ],
                "elective": [
                    "Advanced Databases",
                    "Distributed Computing",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },
        }
    },


    # =====================================================
    # ARTIFICIAL INTELLIGENCE
    # =====================================================

    "Artificial Intelligence": {

        "PG": {

            1: {
                "core": [
                    "Machine Learning",
                    "Artificial Intelligence",
                    "Data Science",
                    "Python Programming",
                    "Mathematics for AI",
                ],
                "elective": [],
                "lab": [
                    "Machine Learning",
                    "Python Programming",
                ],
            },

            2: {
                "core": [
                    "Deep Learning",
                    "Natural Language Processing",
                    "Computer Vision",
                    "Reinforcement Learning",
                    "AI Ethics",
                ],
                "elective": [],
                "lab": [
                    "Deep Learning",
                    "Natural Language Processing",
                ],
            },

            3: {
                "core": [
                    "Advanced Machine Learning",
                    "Robotics",
                    "AI in Healthcare",
                    "AI Algorithms",
                    "Cloud Computing",
                ],
                "elective": [],
                "lab": [],
            },

            4: {
                "core": [
                    "Capstone Project",
                    "AI in Business",
                    "Thesis Writing",
                    "AI for Autonomous Systems",
                    "Research Methodology",
                ],
                "elective": [
                    "AI in Business",
                    "AI for Autonomous Systems",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },
        }
    },


    # =====================================================
    # CYBERSECURITY
    # =====================================================

    "Cybersecurity": {

        "PG": {

            1: {
                "core": [
                    "Introduction to Cybersecurity",
                    "Cryptography",
                    "Network Security",
                    "Ethical Hacking",
                    "Information Security Management",
                ],
                "elective": [],
                "lab": [
                    "Cryptography",
                    "Network Security",
                ],
            },

            2: {
                "core": [
                    "Digital Forensics",
                    "Security Auditing",
                    "Cyber Threats",
                    "Cloud Security",
                    "Advanced Cryptography",
                ],
                "elective": [],
                "lab": [
                    "Digital Forensics",
                    "Advanced Cryptography",
                ],
            },

            3: {
                "core": [
                    "Malware Analysis",
                    "Penetration Testing",
                    "Security Policies",
                    "Cyber Laws",
                    "Incident Response",
                ],
                "elective": [],
                "lab": [
                    "Penetration Testing",
                    "Malware Analysis",
                ],
            },

            4: {
                "core": [
                    "Capstone Project",
                    "Security Research",
                    "Advanced Network Security",
                    "Security Risk Management",
                    "Thesis Writing",
                ],
                "elective": [
                    "Security Research",
                    "Advanced Network Security",
                ],
                "lab": [
                    "Capstone Project"
                ],
            },
        }
    },


    # =====================================================
    # MASTER OF ARCHITECTURE
    # =====================================================

    "Master of Architecture": {

        "PG": {

            1: {
                "core": [
                    "Architectural Design",
                    "Building Materials",
                    "Construction Techniques",
                    "Structural Systems",
                    "Environmental Design",
                ],
                "elective": [],
                "lab": [
                    "Architectural Design"
                ],
            },

            2: {
                "core": [
                    "History of Architecture",
                    "Urban Design",
                    "Landscape Architecture",
                    "Building Systems",
                    "Sustainability in Architecture",
                ],
                "elective": [],
                "lab": [],
            },

            3: {
                "core": [
                    "Advanced Structural Design",
                    "Urban Planning",
                    "Architectural Planning",
                    "Building Information Modeling",
                    "Architecture Theory",
                ],
                "elective": [],
                "lab": [
                    "Building Information Modeling"
                ],
            },

            4: {
                "core": [
                    "Capstone Project",
                    "Research Methodology",
                    "Thesis Writing",
                    "Advanced Environmental Design",
                    "Architectural Practice",
                ],
                "elective": [],
                "lab": [
                    "Capstone Project"
                ],
            },
        }
    },
}


# =========================================================
# BUILD SUBJECTS FOR ONE SEMESTER
# =========================================================

def build_subjects_for_semester(course, semester):
    """
    Build the subjects for one course and semester.

    Important:
    - A subject can appear in the curriculum's core list
      and also be designated as a Lab.
    - Lab gets priority.
    - Elective gets priority over Core.
    - Remaining subjects are Core.
    """

    course_curriculum = SUBJECT_LIST.get(
        course.course_name
    )

    if not course_curriculum:

        raise ValueError(
            f"No curriculum found for course: "
            f"{course.course_name}"
        )

    level_curriculum = course_curriculum.get(
        course.program_level
    )

    if not level_curriculum:

        raise ValueError(
            f"No curriculum found for "
            f"{course.course_name} "
            f"({course.program_level})"
        )

    semester_data = level_curriculum.get(
        semester
    )

    if not semester_data:

        raise ValueError(
            f"No subjects defined for "
            f"{course.course_name} "
            f"({course.program_level}) "
            f"semester {semester}"
        )

    core_subjects = list(
        semester_data.get("core", [])
    )

    elective_subjects = list(
        semester_data.get("elective", [])
    )

    lab_subjects = list(
        semester_data.get("lab", [])
    )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    if len(core_subjects) < 2:

        raise ValueError(
            f"{course.course_name} "
            f"semester {semester} "
            f"has fewer than 2 core subjects."
        )

    # -----------------------------------------------------
    # Select Lab
    # -----------------------------------------------------

    lab_subject = None

    if lab_subjects:

        # Deterministic selection.
        # Because random selection can change curriculum
        # every time the generator is executed.
        lab_subject = lab_subjects[0]

    # -----------------------------------------------------
    # Select Elective
    # -----------------------------------------------------

    elective_subject = None

    if elective_subjects:

        # Deterministic selection.
        elective_subject = elective_subjects[0]

    # -----------------------------------------------------
    # Build final subject list
    # -----------------------------------------------------

    subjects = []

    # Lab
    if lab_subject:

        subjects.append(
            (
                lab_subject,
                "Lab"
            )
        )

    # Elective
    if elective_subject:

        subjects.append(
            (
                elective_subject,
                "Elective"
            )
        )

    # Core
    for subject_name in core_subjects:

        # If already used as Lab
        if subject_name == lab_subject:
            continue

        # If already used as Elective
        if subject_name == elective_subject:
            continue

        subjects.append(
            (
                subject_name,
                "Core"
            )
        )

    return subjects


# =========================================================
# GENERATE SUBJECT CODE
# =========================================================

def generate_subject_code(
    course,
    semester,
    number
):
    """
    Generate a unique and readable subject code.

    Example:

        CSEM-S01-01
        CSEM-S01-02
        CSEM-S01-03

        CSEA-S01-01
        CSEA-S01-02

    Because the course abbreviation is included,
    morning and afternoon course records get
    different subject codes.
    """

    abbreviation = (
        course.course_abbreviation
        .upper()
        .replace(" ", "")
    )

    return (
        f"{abbreviation}"
        f"-S{semester:02d}"
        f"-{number:02d}"
    )


# =========================================================
# CREATE SUBJECTS
# =========================================================

def create_subjects():

    random.seed(RANDOM_SEED)

    # -----------------------------------------------------
    # GET ACTIVE COURSES
    # -----------------------------------------------------

    courses = (
        Course.query
        .filter_by(is_active=True)
        .order_by(Course.course_code)
        .all()
    )

    if not courses:

        print()
        print(
            "ERROR: No active courses found."
        )

        print(
            "Run the course generator first."
        )

        return

    print()
    print("=" * 100)
    print("ExamNexus - Demo Subject Generator")
    print("=" * 100)
    print()

    print(
        f"Active courses found: {len(courses)}"
    )

    print()

    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    created = 0
    skipped = 0

    # -----------------------------------------------------
    # PROCESS EVERY COURSE
    # -----------------------------------------------------

    for course in courses:

        print("-" * 100)

        print(
            f"{course.course_code} | "
            f"{course.course_name}"
        )

        print(
            f"Program Level : {course.program_level}"
        )

        print(
            f"Abbreviation  : "
            f"{course.course_abbreviation}"
        )

        print(
            f"Semesters     : "
            f"{course.total_semesters}"
        )

        print(
            f"Shift         : "
            f"{course.study_shift}"
        )

        print(
            f"Session       : "
            f"{course.session}"
        )

        print()

        # -------------------------------------------------
        # VALIDATE CURRICULUM
        # -------------------------------------------------

        course_curriculum = SUBJECT_LIST.get(
            course.course_name
        )

        if not course_curriculum:

            raise ValueError(
                f"No curriculum found for "
                f"{course.course_name}"
            )

        level_curriculum = course_curriculum.get(
            course.program_level
        )

        if not level_curriculum:

            raise ValueError(
                f"No {course.program_level} curriculum "
                f"found for {course.course_name}"
            )

        # -------------------------------------------------
        # CHECK ALL SEMESTERS
        # -------------------------------------------------

        for semester in range(
            1,
            course.total_semesters + 1
        ):

            # -------------------------------------------------
            # BUILD SUBJECTS
            # -------------------------------------------------

            semester_subjects = (
                build_subjects_for_semester(
                    course,
                    semester
                )
            )

            if not semester_subjects:

                raise ValueError(
                    f"No subjects generated for "
                    f"{course.course_code} "
                    f"semester {semester}"
                )

            # -------------------------------------------------
            # CREATE EACH SUBJECT
            # -------------------------------------------------

            for number, (
                subject_name,
                subject_type
            ) in enumerate(
                semester_subjects,
                start=1
            ):

                subject_code = (
                    generate_subject_code(
                        course=course,
                        semester=semester,
                        number=number
                    )
                )

                # ---------------------------------------------
                # CHECK EXISTING SUBJECT
                # ---------------------------------------------

                existing = (
                    Subject.query
                    .filter_by(
                        subject_code=subject_code
                    )
                    .first()
                )

                if existing:

                    skipped += 1

                    print(
                        f"  SKIP | "
                        f"S{semester:<2} | "
                        f"{subject_code:<20} | "
                        f"{subject_type:<9} | "
                        f"{subject_name}"
                    )

                    continue

                # ---------------------------------------------
                # CREATE SUBJECT
                # ---------------------------------------------

                subject = Subject(
                    subject_code=subject_code,
                    subject_name=subject_name,
                    course_id=course.id,
                    semester=semester,
                    subject_type=subject_type,
                    is_active=True,
                )

                db.session.add(subject)

                created += 1

                print(
                    f"  ADD  | "
                    f"S{semester:<2} | "
                    f"{subject_code:<20} | "
                    f"{subject_type:<9} | "
                    f"{subject_name}"
                )

        print()

    # -----------------------------------------------------
    # COMMIT
    # -----------------------------------------------------

    try:

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print()
        print("=" * 100)
        print("ERROR: SUBJECT GENERATION FAILED")
        print("=" * 100)
        print(error)

        raise

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    print()
    print("=" * 100)
    print("SUBJECT GENERATION COMPLETE")
    print("=" * 100)

    print(
        f"Subjects created       : {created}"
    )

    print(
        f"Subjects already exist : {skipped}"
    )

    print(
        f"Total subjects         : "
        f"{Subject.query.count()}"
    )

    print("=" * 100)


# =========================================================
# SHOW SUBJECT SUMMARY
# =========================================================

def show_subject_summary():

    subjects = (
        Subject.query
        .join(Course)
        .order_by(
            Course.course_code,
            Subject.semester,
            Subject.subject_code
        )
        .all()
    )

    print()
    print("=" * 100)
    print("SUBJECT VERIFICATION")
    print("=" * 100)

    current_course = None
    current_semester = None

    for subject in subjects:

        course = subject.course

        # -------------------------------------------------
        # COURSE HEADER
        # -------------------------------------------------

        if course.course_code != current_course:

            current_course = course.course_code
            current_semester = None

            print()
            print("-" * 100)

            print(
                f"{course.course_code} | "
                f"{course.course_name} | "
                f"{course.program_level}"
            )

        # -------------------------------------------------
        # SEMESTER HEADER
        # -------------------------------------------------

        if subject.semester != current_semester:

            current_semester = subject.semester

            print()
            print(
                f"  Semester {subject.semester}"
            )

        # -------------------------------------------------
        # SUBJECT
        # -------------------------------------------------

        print(
            f"    {subject.subject_code:<20} | "
            f"{subject.subject_type:<9} | "
            f"{subject.subject_name}"
        )

    print()
    print("=" * 100)

    print(
        f"Total subjects: {len(subjects)}"
    )

    print("=" * 100)


# =========================================================
# MAIN
# =========================================================

def main():

    app = create_app()

    with app.app_context():

        create_subjects()

        show_subject_summary()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
