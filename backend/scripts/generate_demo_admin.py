import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


# ---------------------------------------------------------
# MAKE BACKEND AVAILABLE TO PYTHON
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app import create_app, db
from app.models.admin import Admin


# ---------------------------------------------------------
# DEMO ADMIN DETAILS
# ---------------------------------------------------------

ADMIN_NAME = "System Administrator"

ADMIN_EMAIL = "admin@examnexus.edu"

ADMIN_PASSWORD = "Admin@123"


# ---------------------------------------------------------
# CREATE ADMIN
# ---------------------------------------------------------

def create_demo_admin():

    app = create_app()

    with app.app_context():

        print()
        print("=" * 70)
        print("ExamNexus - Demo Admin Creation")
        print("=" * 70)
        print()

        # -------------------------------------------------
        # CHECK EXISTING ADMIN
        # -------------------------------------------------

        existing_admin = Admin.query.filter_by(
            email=ADMIN_EMAIL
        ).first()

        if existing_admin:

            print(
                "Admin already exists."
            )

            print(
                f"Email: {ADMIN_EMAIL}"
            )

            print()

            return

        # -------------------------------------------------
        # HASH PASSWORD
        # -------------------------------------------------

        password_hash = generate_password_hash(
            ADMIN_PASSWORD
        )

        # -------------------------------------------------
        # CREATE ADMIN
        # -------------------------------------------------

        admin = Admin(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            is_active=True
        )

        db.session.add(admin)

        try:

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "ERROR while creating admin:"
            )

            print(error)

            return

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        print(
            "Admin created successfully."
        )

        print()

        print(
            f"Name     : {ADMIN_NAME}"
        )

        print(
            f"Email    : {ADMIN_EMAIL}"
        )

        print(
            f"Password : {ADMIN_PASSWORD}"
        )

        print()

        print(
            "The password is stored as a hash "
            "in the database."
        )

        print()

        print("=" * 70)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":

    create_demo_admin()
