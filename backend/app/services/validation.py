from collections import defaultdict

from app.models.allocation import Allocation
from app.models.examination import Examination
from app.models.exam_registration import ExamRegistration


def validate_allocation(examination_id):

    examination = Examination.query.get(
        examination_id
    )

    if not examination:

        return {
            "status": "INVALID",
            "message": "Examination not found",
            "hard_violations": [],
            "allocated_students": 0,
            "registered_students": 0,
            "unallocated_students": 0,
            "halls_used": 0
        }

    # ---------------------------------------------------------
    # Get registered students
    # ---------------------------------------------------------

    registrations = ExamRegistration.query.filter_by(
        examination_id=examination_id,
        status="REGISTERED"
    ).all()

    registered_student_ids = {
        registration.student_id
        for registration in registrations
    }

    # ---------------------------------------------------------
    # Get allocations
    # ---------------------------------------------------------

    allocations = Allocation.query.filter_by(
        examination_id=examination_id
    ).all()

    hard_violations = []

    # ---------------------------------------------------------
    # Check every allocation
    # ---------------------------------------------------------

    hall_counts = defaultdict(int)
    hall_seats = defaultdict(list)
    allocation_student_ids = []

    for allocation in allocations:

        student = allocation.student
        hall = allocation.hall

        allocation_student_ids.append(
            allocation.student_id
        )

        # -----------------------------------------------------
        # Student validation
        # -----------------------------------------------------

        if not student:

            hard_violations.append(
                f"Allocation {allocation.id}: student not found"
            )

            continue

        if not student.is_active:

            hard_violations.append(
                f"Student {student.student_id} is inactive"
            )

        # Student must be registered.
        if student.id not in registered_student_ids:

            hard_violations.append(
                f"Student {student.student_id} is not registered "
                "for this examination"
            )

        # -----------------------------------------------------
        # Hall validation
        # -----------------------------------------------------

        if not hall:

            hard_violations.append(
                f"Allocation {allocation.id}: hall not found"
            )

            continue

        if not hall.is_active:

            hard_violations.append(
                f"Hall {hall.name} is inactive"
            )

        if not hall.is_available:

            hard_violations.append(
                f"Hall {hall.name} is unavailable"
            )

        if hall.is_under_maintenance:

            hard_violations.append(
                f"Hall {hall.name} is under maintenance"
            )

        # -----------------------------------------------------
        # Accessibility
        # -----------------------------------------------------

        if (
            student.disability
            and not hall.is_accessible
        ):

            hard_violations.append(
                f"Student {student.student_id} requires "
                f"accessibility support but hall "
                f"{hall.name} is not accessible"
            )

        # -----------------------------------------------------
        # Hall count
        # -----------------------------------------------------

        hall_counts[hall.id] += 1

        # -----------------------------------------------------
        # Seat number
        # -----------------------------------------------------

        if not allocation.seat_number:

            hard_violations.append(
                f"Allocation {allocation.id} has no seat number"
            )

        else:

            hall_seats[hall.id].append(
                allocation.seat_number
            )

    # ---------------------------------------------------------
    # Check hall capacity
    # ---------------------------------------------------------

    for hall_id, count in hall_counts.items():

        hall = next(
            (
                allocation.hall
                for allocation in allocations
                if allocation.hall_id == hall_id
            ),
            None
        )

        if not hall:
            continue

        if count > hall.examination_capacity:

            hard_violations.append(
                f"Hall {hall.name} exceeds examination capacity "
                f"of {hall.examination_capacity}"
            )

    # ---------------------------------------------------------
    # Check duplicate seat numbers
    # ---------------------------------------------------------

    for hall_id, seats in hall_seats.items():

        if len(seats) != len(set(seats)):

            hall = next(
                (
                    allocation.hall
                    for allocation in allocations
                    if allocation.hall_id == hall_id
                ),
                None
            )

            hall_name = (
                hall.name
                if hall
                else str(hall_id)
            )

            hard_violations.append(
                f"Duplicate seat numbers detected in "
                f"hall {hall_name}"
            )

    # ---------------------------------------------------------
    # Check duplicate student allocations
    # ---------------------------------------------------------

    if len(allocation_student_ids) != len(
        set(allocation_student_ids)
    ):

        hard_violations.append(
            "A student has been allocated more than once"
        )

    # ---------------------------------------------------------
    # Check missing allocations
    # ---------------------------------------------------------

    allocated_student_ids = set(
        allocation_student_ids
    )

    missing_student_ids = (
        registered_student_ids
        - allocated_student_ids
    )

    if missing_student_ids:

        hard_violations.append(
            f"{len(missing_student_ids)} registered student(s) "
            "do not have an allocation"
        )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    allocated_students = len(
        allocations
    )

    registered_students = len(
        registered_student_ids
    )

    unallocated_students = len(
        missing_student_ids
    )

    halls_used = len(
        hall_counts
    )

    # ---------------------------------------------------------
    # Final status
    # ---------------------------------------------------------

    if hard_violations:

        status = "INVALID"
        message = "Allocation validation failed"

    else:

        status = "VALID"
        message = "Allocation is valid"

    return {
        "status": status,
        "message": message,
        "hard_violations": hard_violations,
        "examination_id": examination.id,
        "registered_students": registered_students,
        "allocated_students": allocated_students,
        "unallocated_students": unallocated_students,
        "halls_used": halls_used
    }
