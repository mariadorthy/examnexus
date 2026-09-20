from app import create_app, db


def main():
    app = create_app()

    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()

        print("Creating all tables from current models...")
        db.create_all()

        print("Database reset complete.")


if __name__ == "__main__":
    main()