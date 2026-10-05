from flask import Blueprint

from app.auth.decorators import roles_required

from app.services.reports import (
    allocation_report,
    student_allocation_report,
    hall_utilization_report,
    invigilator_workload_report
)


reports_bp = Blueprint("reports", __name__)


@reports_bp.route(
    "/allocation/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def allocation(examination_id):

    return allocation_report(examination_id), 200


@reports_bp.route(
    "/students/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def students(examination_id):

    return student_allocation_report(examination_id), 200


@reports_bp.route(
    "/halls/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def halls(examination_id):

    return hall_utilization_report(examination_id), 200


@reports_bp.route(
    "/invigilators/<int:examination_id>",
    methods=["GET"]
)
@roles_required("admin")
def invigilators(examination_id):

    return invigilator_workload_report(examination_id), 200