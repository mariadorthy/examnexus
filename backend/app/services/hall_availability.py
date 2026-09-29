from app.models.hall import Hall


def get_available_halls():
    """
    Return halls that are currently usable for examination allocation.

    Date/session conflict handling is intentionally not performed here
    because the current Hall model does not contain date/session
    availability records.
    """

    halls = Hall.query.filter(
        Hall.is_active.is_(True),
        Hall.is_available.is_(True),
        Hall.is_under_maintenance.is_(False),
        Hall.examination_capacity > 0
    ).order_by(
        Hall.examination_capacity.desc()
    ).all()

    return halls


def get_hall_readiness():
    """
    Return examination-ready hall information.
    """

    halls = get_available_halls()

    total_capacity = sum(
        hall.examination_capacity
        for hall in halls
    )

    accessible_capacity = sum(
        hall.examination_capacity
        for hall in halls
        if hall.is_accessible
    )

    return {
        "available_halls": halls,
        "available_hall_count": len(halls),
        "total_available_capacity": total_capacity,
        "accessible_hall_count": sum(
            1
            for hall in halls
            if hall.is_accessible
        ),
        "accessible_capacity": accessible_capacity
    }