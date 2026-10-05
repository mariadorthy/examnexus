from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    # -----------------------------------------------------
    # IMPORT MODELS
    # -----------------------------------------------------

    from app import models

    # -----------------------------------------------------
    # IMPORT ROUTES
    # -----------------------------------------------------
    from app.routes.dashboard import dashboard_bp
    from app.routes.departments import departments_bp
    from app.routes.courses import courses_bp
    from app.routes.students import students_bp
    from app.routes.subjects import subjects_bp
    from app.routes.examinations import examinations_bp
    from app.routes.exam_registrations import exam_registrations_bp
    from app.routes.halls import halls_bp
    from app.routes.staff import staff_bp
    from app.routes.allocations import allocations_bp
    from app.routes.auth import auth_bp
    from app.routes.timetable import timetable_bp
    from app.routes.readiness import readiness_bp
    from app.routes.imports import imports_bp
    from app.routes.hall_tickets import hall_tickets_bp
    from app.routes.reports import reports_bp
    from app.models.seat_allocation import SeatAllocation
    # -----------------------------------------------------
    # REGISTER BLUEPRINTS
    # -----------------------------------------------------

    app.register_blueprint(
    dashboard_bp,
    url_prefix="/api/dashboard"
)

    app.register_blueprint(
        departments_bp,
        url_prefix="/api/departments"
    )

    app.register_blueprint(
        courses_bp,
        url_prefix="/api/courses"
    )

    app.register_blueprint(
        students_bp,
        url_prefix="/api/students"
    )

    app.register_blueprint(
        subjects_bp,
        url_prefix="/api/subjects"
    )

    app.register_blueprint(
        examinations_bp,
        url_prefix="/api/examinations"
    )

    app.register_blueprint(
        exam_registrations_bp,
        url_prefix="/api/exam-registrations"
    )

    app.register_blueprint(
        halls_bp,
        url_prefix="/api/halls"
    )

    app.register_blueprint(
        staff_bp,
        url_prefix="/api/staff"
    )

    app.register_blueprint(
        allocations_bp,
        url_prefix="/api/allocations"
    )

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )
    app.register_blueprint(
    timetable_bp,
    url_prefix="/api/timetable"
)
    app.register_blueprint(
    readiness_bp,
    url_prefix="/api/readiness"
)
    app.register_blueprint(
    imports_bp,
    url_prefix="/api/import"
)
    app.register_blueprint(
    hall_tickets_bp,
    url_prefix="/api/hall-tickets"
)
    app.register_blueprint(
    reports_bp,
    url_prefix="/api/reports"
)

    # -----------------------------------------------------
    # CREATE DATABASE TABLES
    # -----------------------------------------------------

  # Database schema is managed by Flask-Migrate.

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    @app.route("/")
    def home():

        return {
            "message": "ExamNexus backend is running"
        }

    return app