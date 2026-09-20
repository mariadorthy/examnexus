from app import db

from app.models.allocation import Allocation
from app.models.examination import Examination
from app.models.hall import Hall
from app.services.eligibility import get_eligible_students


def halls_conflict(hall_id, examination):
    """
    Check whether a hall is already being used by
    another examination at an overlapping date/time.
    """

    existing_allocations = Allocation.query.filter_by(
        hall_id=hall_id
    ).all()

    for allocation in existing_allocations:

        # Same examination is not a conflict.
        if allocation.examination_id == examination.id:
            continue

        existing_exam = allocation.examination

        if not existing_exam:
            continue

        if existing_exam.exam_date != examination.exam_date:
            continue

        if (
            existing_exam.start_time < examination.end_time
            and existing_exam.end_time > examination.start_time
        ):
            return True

    return False


def generate_seat_number(seat_index):
    """
    Generate a simple seat number.

    Examples:
        1  -> A01
        2  -> A02
        10 -> A10
        99 -> A99
        100 -> B01
    """

    seats_per_row = 99

    row_index = (seat_index - 1) // seats_per_row
    seat_in_row = ((seat_index - 1) % seats_per_row) + 1

    row_letter = chr(
        ord("A") + row_index
    )

    return f"{row_letter}{seat_in_row:02d}"


def generate_allocation(examination_id):
    """
    Generate hall and seat allocations for an examination.
    """

    examination = Examination.query.get(examination_id)

    if not examination:
        return {
            "success": False,
            "message": "Examination not found"
        }

    # ---------------------------------------------------------
    # Prevent duplicate generation
    # ---------------------------------------------------------

    existing_allocation = Allocation.query.filter_by(
        examination_id=examination_id
    ).first()

    if existing_allocation:
        return {
            "success": False,
            "message": "Allocation already exists for this examination",
            "allocated_count": Allocation.query.filter_by(
                examination_id=examination_id
            ).count()
        }

    # ---------------------------------------------------------
    # Get eligible students
    # ---------------------------------------------------------

    students = get_eligible_students(
        examination_id
    )

    if not students:
        return {
            "success": False,
            "message": "No eligible registered students found",
            "allocated_count": 0,
            "unallocated_students": []
        }

    # ---------------------------------------------------------
    # Get usable halls
    # ---------------------------------------------------------

    halls = Hall.query.filter_by(
        is_active=True,
        is_available=True,
        is_under_maintenance=False
    ).filter(
        Hall.examination_capacity > 0
    ).order_by(
        Hall.examination_capacity.desc()
    ).all()

    available_halls = [
        hall
        for hall in halls
        if not halls_conflict(
            hall.id,
            examination
        )
    ]

    if not available_halls:
        return {
            "success": False,
            "message": "No available halls for this examination",
            "registered_students": len(students),
            "available_capacity": 0,
            "unallocated_students": [
                student.student_id
                for student in students
            ]
        }

    # ---------------------------------------------------------
    # Calculate accessible capacity
    #
    # We first calculate whether enough capacity exists
    # for all students.
    # ---------------------------------------------------------

    normal_capacity = sum(
        hall.examination_capacity
        for hall in available_halls
    )

    if normal_capacity < len(students):

        shortage = (
            len(students)
            - normal_capacity
        )

        return {
            "success": False,
            "message": "Insufficient hall capacity",
            "registered_students": len(students),
            "available_capacity": normal_capacity,
            "shortage": shortage,
            "unallocated_students": [
                student.student_id
                for student in students
            ]
        }

    # ---------------------------------------------------------
    # Separate students requiring accessibility support.
    # ---------------------------------------------------------

    students_requiring_accessibility = [
        student
        for student in students
        if student.disability
    ]

    normal_students = [
        student
        for student in students
        if not student.disability
    ]

    # Accessible halls first for students requiring support.
    accessible_halls = [
        hall
        for hall in available_halls
        if hall.is_accessible
    ]

    inaccessible_halls = [
        hall
        for hall in available_halls
        if not hall.is_accessible
    ]

    accessible_capacity = sum(
        hall.examination_capacity
        for hall in accessible_halls
    )

    if (
        len(students_requiring_accessibility)
        > accessible_capacity
    ):
        return {
            "success": False,
            "message": (
                "Insufficient accessible hall capacity "
                "for students requiring accessibility support"
            ),
            "registered_students": len(students),
            "students_requiring_accessibility": len(
                students_requiring_accessibility
            ),
            "accessible_capacity": accessible_capacity,
            "shortage": (
                len(students_requiring_accessibility)
                - accessible_capacity
            ),
            "unallocated_students": [
                student.student_id
                for student in students_requiring_accessibility
            ]
        }

    # ---------------------------------------------------------
    # Allocate students
    # ---------------------------------------------------------

    allocations = []
    used_halls = set()

    def allocate_students_to_halls(
        student_list,
        hall_list
    ):
        """
        Allocate a list of students to a list of halls.
        """

        student_index = 0

        for hall in hall_list:

            if student_index >= len(student_list):
                break

            for seat_index in range(
                1,
                hall.examination_capacity + 1
            ):

                if student_index >= len(student_list):
                    break

                student = student_list[
                    student_index
                ]

                allocation = Allocation(
                    student_id=student.id,
                    examination_id=examination.id,
                    hall_id=hall.id,
                    seat_number=generate_seat_number(
                        seat_index
                    ),
                    status="GENERATED"
                )

                allocations.append(
                    allocation
                )

                used_halls.add(
                    hall.id
                )

                student_index += 1

        return student_index

    # ---------------------------------------------------------
    # First allocate students requiring accessibility support.
    # ---------------------------------------------------------

    allocated_accessibility = allocate_students_to_halls(
        students_requiring_accessibility,
        accessible_halls
    )

    # ---------------------------------------------------------
    # Then allocate normal students.
    #
    # Accessible halls can still be used if capacity remains.
    # ---------------------------------------------------------

    remaining_accessible_halls = []

    for hall in accessible_halls:

        allocated_in_hall = sum(
            1
            for allocation in allocations
            if allocation.hall_id == hall.id
        )

        if allocated_in_hall < hall.examination_capacity:
            remaining_accessible_halls.append(
                hall
            )

    remaining_halls = (
        remaining_accessible_halls
        + inaccessible_halls
    )

    allocated_normal = allocate_students_to_halls(
        normal_students,
        remaining_halls
    )

    total_allocated = (
        allocated_accessibility
        + allocated_normal
    )

    # ---------------------------------------------------------
    # Safety check
    # ---------------------------------------------------------

    if total_allocated < len(students):

        allocated_student_ids = {
            allocation.student_id
            for allocation in allocations
        }

        unallocated_students = [
            student.student_id
            for student in students
            if student.id not in allocated_student_ids
        ]

        db.session.rollback()

        return {
            "success": False,
            "message": "Insufficient suitable hall capacity",
            "registered_students": len(students),
            "allocated_count": total_allocated,
            "unallocated_students": unallocated_students
        }

    # ---------------------------------------------------------
    # Save allocations
    # ---------------------------------------------------------

    try:

        db.session.add_all(
            allocations
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to save allocations",
            "error": str(error)
        }

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    return {
        "success": True,
        "message": "Allocation generated successfully",
        "examination_id": examination.id,
        "registered_students": len(students),
        "allocated_count": len(allocations),
        "halls_used": len(used_halls),
        "unallocated_students": []
    }
