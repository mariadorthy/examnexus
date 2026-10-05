"""
Post-Phase 7 — Examination lifecycle.

DRAFT → GENERATED → VALIDATED → REVIEW → APPROVED → PUBLISHED.
Forward-only. Server-enforced. Publish re-validates.
"""

from app import db
from app.models.examination import Examination
from app.services.lifecycle import transition_status


def _reload(examination_id):
    return db.session.get(Examination, examination_id)


def _prepare_generated_state(examination_id):
    """
    Prepare the examination for lifecycle validation.

    Allocation and invigilator generation are performed before
    entering the lifecycle so GENERATED → VALIDATED → REVIEW
    → APPROVED → PUBLISHED can use the real lifecycle service.
    """
    from app.services.allocation import generate_allocation
    from app.services.invigilator_allocation import (
        generate_invigilator_allocation,
    )

    examination = _reload(examination_id)
    examination.status = "DRAFT"
    db.session.commit()

    allocation_result = generate_allocation(
        examination_id,
        force=True,
    )
    assert allocation_result.get("success") is True, allocation_result

    invigilator_result = generate_invigilator_allocation(
        examination_id,
        force=True,
    )
    assert invigilator_result.get("success") is True, invigilator_result

    db.session.refresh(examination)
    assert examination.status == "DRAFT"


def _advance_to(examination_id, target):
    order = [
        "DRAFT",
        "GENERATED",
        "VALIDATED",
        "REVIEW",
        "APPROVED",
        "PUBLISHED",
    ]

    current = _reload(examination_id).status
    current_index = order.index(current)
    target_index = order.index(target)

    assert target_index >= current_index

    for index in range(current_index + 1, target_index + 1):
        result = transition_status(
            examination_id,
            order[index],
        )
        assert result.get("success") is True, result

# ============================================================
# 8B.1 — Illegal first jump
# ============================================================

def test_draft_to_approved_is_rejected(
    app_context, examination_id
):
    examination = _reload(examination_id)
    original_status = examination.status

    try:
        examination.status = "DRAFT"
        db.session.commit()

        result = transition_status(
            examination_id,
            "APPROVED",
        )

        assert result.get("success") is False
    finally:
        examination.status = original_status
        db.session.commit()

# ============================================================
# 8B.2 — DRAFT → GENERATED
# ============================================================

# ============================================================
# 8B.3 — GENERATED → VALIDATED
# ============================================================

# ============================================================
# 8B.4 — VALIDATED → APPROVED skip is rejected
# ============================================================
def test_validated_to_approved_skip_is_rejected(
    app_context, examination_id
):
    examination = _reload(examination_id)
    original_status = examination.status

    try:
        examination.status = "VALIDATED"
        db.session.commit()

        result = transition_status(
            examination_id,
            "APPROVED",
        )

        assert result.get("success") is False
    finally:
        examination.status = original_status
        db.session.commit()


# ============================================================
# 8B.5 — VALIDATED → REVIEW
# ============================================================

# ============================================================
# 8B.6 — REVIEW → APPROVED
# ============================================================

# ============================================================
# 8B.8 — APPROVED → PUBLISHED
# ============================================================

def test_complete_forward_lifecycle_succeeds(
    app_context, examination_id
):
    _prepare_generated_state(examination_id)

    _advance_to(examination_id, "GENERATED")
    assert _reload(examination_id).status == "GENERATED"

    _advance_to(examination_id, "VALIDATED")
    assert _reload(examination_id).status == "VALIDATED"

    _advance_to(examination_id, "REVIEW")
    assert _reload(examination_id).status == "REVIEW"

    _advance_to(examination_id, "APPROVED")
    assert _reload(examination_id).status == "APPROVED"

    _advance_to(examination_id, "PUBLISHED")
    assert _reload(examination_id).status == "PUBLISHED"

# ============================================================
# 8B.9 — Cannot go backward
# ============================================================

def test_published_to_approved_is_rejected(
    app_context, examination_id
):
    examination = _reload(examination_id)
    original_status = examination.status

    try:
        examination.status = "PUBLISHED"
        db.session.commit()

        result = transition_status(
            examination_id,
            "APPROVED",
        )

        assert result.get("success") is False
    finally:
        examination.status = original_status
        db.session.commit()

# ============================================================
# 8B.10 — Cannot skip to PUBLISHED
# ============================================================

def test_draft_to_published_is_rejected(
    app_context, examination_id
):
    examination = _reload(examination_id)

    original_status = examination.status
    try:
        examination.status = "DRAFT"
        db.session.commit()

        result = transition_status(examination_id, "PUBLISHED")
        assert result.get("success") is False
    finally:
        # Restore a valid forward-chain state for downstream tests
        examination = _reload(examination_id)
        examination.status = original_status
        db.session.commit()