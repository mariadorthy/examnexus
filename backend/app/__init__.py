from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()


def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

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

    # -----------------------------------------------------
    # CREATE DATABASE TABLES
    # -----------------------------------------------------

    with app.app_context():

        db.create_all()

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    @app.route("/")
    def home():

        return {
            "message": "ExamNexus backend is running"
        }

    return app