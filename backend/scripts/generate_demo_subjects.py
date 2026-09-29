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
#           -> project
#
# Subject Type stored in database:
#
#   Core
#   Elective
#   Lab
#   Project
#
# =========================================================

SUBJECT_LIST = {

    # =====================================================
# BACHELOR OF ARTS - ENGLISH
# =====================================================

"Bachelor of Arts - English": {

    "UG": {

        1: {
            "core": [
                "English Literature I",
                "British Literature I",
                "English Grammar",
                "Communication Skills",
                "Introduction to Literature",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "English Literature II",
                "British Literature II",
                "Indian Writing in English",
                "Literary Criticism I",
                "Academic Writing",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "American Literature",
                "World Literature",
                "Literary Criticism II",
                "Shakespeare Studies",
                "Language and Linguistics",
            ],
            "elective": [
                "American Literature",
                "World Literature",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "Modern English Literature",
                "Postcolonial Literature",
                "Indian Literature",
                "Translation Studies",
                "Literary Theory",
            ],
            "elective": [
                "Translation Studies",
                "Literary Theory",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Contemporary Literature",
                "Women and Literature",
                "Drama Studies",
                "Digital Humanities",
                "Creative Writing",
            ],
            "elective": [
                "Creative Writing",
                "Digital Humanities",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Research Methodology",
                "Professional Communication",
                "Literary Research",
            ],
            "elective": [
                "Film and Literature",
                "Comparative Literature",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},

# =====================================================
# BACHELOR OF ARTS - TAMIL
# =====================================================

"Bachelor of Arts - Tamil": {

    "UG": {

        1: {
            "core": [
                "Tamil Literature I",
                "Tamil Grammar I",
                "Classical Tamil Literature",
                "Communication Tamil",
                "Introduction to Tamil Studies",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "Tamil Literature II",
                "Tamil Grammar II",
                "Sangam Literature",
                "Modern Tamil Literature",
                "Tamil Prose",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "Medieval Tamil Literature",
                "Tamil Poetry",
                "Tamil Short Stories",
                "Tamil Linguistics",
                "Literary Criticism",
            ],
            "elective": [
                "Tamil Poetry",
                "Tamil Short Stories",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "Tamil Epics",
                "Modern Tamil Poetry",
                "Tamil Drama",
                "Folklore Studies",
                "Comparative Literature",
            ],
            "elective": [
                "Folklore Studies",
                "Comparative Literature",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Contemporary Tamil Literature",
                "Tamil Journalism",
                "Translation Studies",
                "Tamil Cultural Studies",
                "Research Methods in Tamil",
            ],
            "elective": [
                "Tamil Journalism",
                "Translation Studies",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Advanced Tamil Studies",
                "Literary Research",
                "Professional Tamil",
            ],
            "elective": [
                "Digital Tamil",
                "Comparative Tamil Literature",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},

# =====================================================
# BACHELOR OF ARTS - HISTORY
# =====================================================

"Bachelor of Arts - History": {

    "UG": {

        1: {
            "core": [
                "Ancient Indian History",
                "World History I",
                "Introduction to History",
                "Indian Culture and Heritage",
                "Archaeology Basics",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "Medieval Indian History",
                "World History II",
                "South Indian History",
                "Historical Methods",
                "Indian Art and Architecture",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "Modern Indian History I",
                "European History",
                "History of Tamil Nadu",
                "Economic History",
                "Political History",
            ],
            "elective": [
                "History of Tamil Nadu",
                "Economic History",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "Modern Indian History II",
                "History of Colonialism",
                "History of the Indian National Movement",
                "Social and Cultural History",
                "Historiography",
            ],
            "elective": [
                "Social and Cultural History",
                "Historiography",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Contemporary World History",
                "Indian Constitution and Political History",
                "History of International Relations",
                "Heritage Management",
                "Museology",
            ],
            "elective": [
                "Heritage Management",
                "Museology",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Historical Research Methods",
                "Archives and Documentation",
                "Contemporary Indian History",
            ],
            "elective": [
                "Public History",
                "Digital History",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},

# =====================================================
# BACHELOR OF ARTS - ECONOMICS
# =====================================================

"Bachelor of Arts - Economics": {

    "UG": {

        1: {
            "core": [
                "Microeconomics I",
                "Macroeconomics I",
                "Mathematics for Economics",
                "Statistics for Economics",
                "Indian Economy",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "Microeconomics II",
                "Macroeconomics II",
                "Economic Statistics",
                "Public Finance",
                "Money and Banking",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "Development Economics",
                "International Economics",
                "Econometrics I",
                "Agricultural Economics",
                "Industrial Economics",
            ],
            "elective": [
                "Agricultural Economics",
                "Industrial Economics",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "Econometrics II",
                "Monetary Economics",
                "Public Economics",
                "Environmental Economics",
                "Labour Economics",
            ],
            "elective": [
                "Environmental Economics",
                "Labour Economics",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Financial Economics",
                "International Trade",
                "Economic Policy",
                "Business Economics",
                "Research Methodology",
            ],
            "elective": [
                "Financial Economics",
                "Business Economics",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Advanced Economic Analysis",
                "Indian Economic Policy",
                "Applied Econometrics",
            ],
            "elective": [
                "Development Policy",
                "Financial Markets",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},

# =====================================================
# BACHELOR OF ARTS - POLITICAL SCIENCE
# =====================================================

"Bachelor of Arts - Political Science": {

    "UG": {

        1: {
            "core": [
                "Introduction to Political Science",
                "Political Theory I",
                "Indian Government and Politics I",
                "Public Administration",
                "Political Institutions",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "Political Theory II",
                "Indian Government and Politics II",
                "Comparative Politics",
                "International Relations I",
                "Constitutional Studies",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "International Relations II",
                "Public Policy",
                "Political Sociology",
                "Indian Political Thought",
                "Western Political Thought",
            ],
            "elective": [
                "Political Sociology",
                "Public Policy",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "International Organizations",
                "Human Rights",
                "Indian Foreign Policy",
                "Political Economy",
                "Electoral Politics",
            ],
            "elective": [
                "Human Rights",
                "Electoral Politics",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Governance and Administration",
                "Political Parties and Elections",
                "Conflict and Peace Studies",
                "Local Government",
                "Contemporary Political Issues",
            ],
            "elective": [
                "Conflict and Peace Studies",
                "Local Government",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Research Methodology",
                "Contemporary Political Theory",
                "Public Policy Analysis",
            ],
            "elective": [
                "International Security",
                "Political Communication",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},
# =====================================================
# BACHELOR OF ARTS - SOCIOLOGY
# =====================================================

"Bachelor of Arts - Sociology": {

    "UG": {

        1: {
            "core": [
                "Introduction to Sociology",
                "Sociological Concepts",
                "Indian Society",
                "Social Institutions",
                "Social Psychology",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        2: {
            "core": [
                "Sociological Thinkers I",
                "Rural Sociology",
                "Urban Sociology",
                "Social Stratification",
                "Population Studies",
            ],
            "elective": [],
            "lab": [],
            "project": [],
        },

        3: {
            "core": [
                "Sociological Thinkers II",
                "Research Methods in Sociology",
                "Gender Studies",
                "Sociology of Education",
                "Industrial Sociology",
            ],
            "elective": [
                "Gender Studies",
                "Industrial Sociology",
            ],
            "lab": [],
            "project": [],
        },

        4: {
            "core": [
                "Political Sociology",
                "Economic Sociology",
                "Family and Marriage",
                "Sociology of Religion",
                "Social Change",
            ],
            "elective": [
                "Economic Sociology",
                "Sociology of Religion",
            ],
            "lab": [],
            "project": [],
        },

        5: {
            "core": [
                "Development Sociology",
                "Medical Sociology",
                "Environmental Sociology",
                "Criminology",
                "Human Rights",
            ],
            "elective": [
                "Medical Sociology",
                "Criminology",
            ],
            "lab": [],
            "project": [],
        },

        6: {
            "core": [
                "Contemporary Sociological Issues",
                "Applied Sociology",
                "Advanced Research Methods",
            ],
            "elective": [
                "Digital Sociology",
                "Sociology of Media",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},
# =====================================================
# BACHELOR OF ARTS - PSYCHOLOGY
# =====================================================

"Bachelor of Arts - Psychology": {

    "UG": {

        1: {
            "core": [
                "Introduction to Psychology",
                "General Psychology",
                "Developmental Psychology I",
                "Social Psychology I",
                "Biological Psychology",
            ],
            "elective": [],
            "lab": [
                "Psychology Practical I"
            ],
            "project": [],
        },

        2: {
            "core": [
                "Developmental Psychology II",
                "Social Psychology II",
                "Cognitive Psychology",
                "Personality Psychology",
                "Psychological Statistics",
            ],
            "elective": [],
            "lab": [
                "Psychology Practical II"
            ],
            "project": [],
        },

        3: {
            "core": [
                "Abnormal Psychology",
                "Educational Psychology",
                "Organizational Psychology",
                "Research Methods in Psychology",
                "Counselling Psychology",
            ],
            "elective": [
                "Educational Psychology",
                "Organizational Psychology",
            ],
            "lab": [
                "Psychological Assessment"
            ],
            "project": [],
        },

        4: {
            "core": [
                "Clinical Psychology",
                "Health Psychology",
                "Consumer Psychology",
                "Positive Psychology",
                "Forensic Psychology",
            ],
            "elective": [
                "Health Psychology",
                "Forensic Psychology",
            ],
            "lab": [
                "Clinical Psychology Practical"
            ],
            "project": [],
        },

        5: {
            "core": [
                "Counselling Techniques",
                "Child Psychology",
                "Neuropsychology",
                "Community Psychology",
                "Industrial Psychology",
            ],
            "elective": [
                "Neuropsychology",
                "Community Psychology",
            ],
            "lab": [
                "Counselling Practical"
            ],
            "project": [],
        },

        6: {
            "core": [
                "Advanced Psychological Research",
                "Contemporary Psychology",
                "Professional Psychology",
            ],
            "elective": [
                "Cyber Psychology",
                "Sports Psychology",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},
# =====================================================
# BACHELOR OF ARTS - JOURNALISM AND MASS COMMUNICATION
# =====================================================

"Bachelor of Arts - Journalism and Mass Communication": {

    "UG": {

        1: {
            "core": [
                "Introduction to Journalism",
                "Communication Theory",
                "News Writing",
                "Media Studies",
                "Language and Communication",
            ],
            "elective": [],
            "lab": [
                "Journalism Practical I"
            ],
            "project": [],
        },

        2: {
            "core": [
                "Print Journalism",
                "Broadcast Journalism",
                "Editing Techniques",
                "Media Ethics",
                "Reporting Techniques",
            ],
            "elective": [],
            "lab": [
                "News Reporting Practical"
            ],
            "project": [],
        },

        3: {
            "core": [
                "Television Production",
                "Radio Broadcasting",
                "Photojournalism",
                "Digital Journalism",
                "Advertising and Public Relations",
            ],
            "elective": [
                "Photojournalism",
                "Digital Journalism",
            ],
            "lab": [
                "Television Production Practical"
            ],
            "project": [],
        },

        4: {
            "core": [
                "Film Studies",
                "Media Management",
                "Online Media",
                "Communication Research",
                "Media Law",
            ],
            "elective": [
                "Film Studies",
                "Online Media",
            ],
            "lab": [
                "Digital Media Production"
            ],
            "project": [],
        },

        5: {
            "core": [
                "Investigative Journalism",
                "Corporate Communication",
                "Social Media Communication",
                "Documentary Production",
                "Media Marketing",
            ],
            "elective": [
                "Investigative Journalism",
                "Documentary Production",
            ],
            "lab": [
                "Documentary Production Practical"
            ],
            "project": [],
        },

        6: {
            "core": [
                "Advanced Media Research",
                "Media Entrepreneurship",
                "Professional Journalism",
            ],
            "elective": [
                "Digital Content Creation",
                "Media Analytics",
            ],
            "lab": [],
            "project": [
                "Major Project"
            ],
        },
    }
},

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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Research Methods",
                    "Advanced Algorithms",
                    "Distributed Systems",
                    "Cyber-Physical Systems",
                ],
                "elective": [
                    "Distributed Systems",
                    "Cyber-Physical Systems",
                ],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "Project Management",
                    "Research Seminar",
                    "Technical Entrepreneurship",
                    "Professional Ethics",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Industrial Training",
                    "Operations Research",
                    "Engineering Management",
                    "Advanced Mechanics",
                ],
                "elective": [],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "Professional Practice",
                    "Engineering Management",
                    "Research Seminar",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Research Methodology",
                    "Professional Practice",
                    "Construction Technology",
                    "Infrastructure Development",
                ],
                "elective": [],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "Professional Practice",
                    "Construction Management",
                    "Research Seminar",
                    "Engineering Economics",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Advanced Networking",
                    "Research Methods",
                    "Cyber-Physical Systems",
                    "Distributed Systems",
                ],
                "elective": [
                    "Distributed Systems",
                    "Cyber-Physical Systems",
                ],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "IT Governance",
                    "Research Seminar",
                    "Professional Ethics",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Industrial Training",
                    "Research Methodology",
                    "Power System Protection",
                    "Smart Grids",
                ],
                "elective": [
                    "Smart Grids"
                ],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "Professional Practice",
                    "Research Seminar",
                    "Engineering Management",
                    "Technical Entrepreneurship",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            6: {
                "core": [
                    "Industrial Training",
                    "Research Methods",
                    "IoT and Embedded Systems",
                    "Advanced Electronics",
                ],
                "elective": [
                    "IoT and Embedded Systems",
                    "Advanced Electronics",
                ],
                "lab": [],
                "project": [
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
                "lab": [],
                "project": [],
            },

            8: {
                "core": [
                    "Research Seminar",
                    "Professional Practice",
                    "Technical Entrepreneurship",
                    "Engineering Management",
                ],
                "elective": [],
                "lab": [],
                "project": [
                    "Major Project"
                ],
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            4: {
                "core": [
                    "Business Ethics",
                    "Corporate Governance",
                    "Supply Chain Management",
                    "Leadership in Organizations",
                ],
                "elective": [],
                "lab": [],
                "project": [
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            4: {
                "core": [
                    "Software Development Life Cycle",
                    "Research Methodology",
                    "Distributed Computing",
                ],
                "elective": [
                    "Advanced Databases",
                    "Distributed Computing",
                ],
                "lab": [],
                "project": [
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            4: {
                "core": [
                    "Thesis Writing",
                    "Research Methodology",
                ],
                "elective": [
                    "AI in Business",
                    "AI for Autonomous Systems",
                ],
                "lab": [],
                "project": [
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            4: {
                "core": [
                    "Security Risk Management",
                    "Thesis Writing",
                ],
                "elective": [
                    "Security Research",
                    "Advanced Network Security",
                ],
                "lab": [],
                "project": [
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
                "project": [],
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
                "project": [],
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
                "project": [],
            },

            4: {
                "core": [
                    "Research Methodology",
                    "Thesis Writing",
                    "Advanced Environmental Design",
                    "Architectural Practice",
                ],
                "elective": [],
                "lab": [],
                "project": [
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
    - Project gets priority over Core.
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

    project_subjects = list(
        semester_data.get("project", [])
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
    # Select Project
    # -----------------------------------------------------

    project_subject = None

    if project_subjects:

        # Deterministic selection.
        project_subject = project_subjects[0]
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

    # Project
    if project_subject:

        subjects.append(
            (
                project_subject,
                "Project"
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
        # If already used as Project
        if subject_name == project_subject:
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
