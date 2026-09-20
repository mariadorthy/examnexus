from app import create_app
from app.services.eligibility import get_eligible_students
from app.services.allocation import generate_allocation
from app.services.validation import validate_allocation

app = create_app()

with app.app_context():
    students = get_eligible_students(1)

    print("Eligible students:")
    print([student.student_id for student in students])

    result = generate_allocation(1)

    print("\nAllocation:")
    print(result)

    validation = validate_allocation(1)

    print("\nValidation:")
    print(validation)