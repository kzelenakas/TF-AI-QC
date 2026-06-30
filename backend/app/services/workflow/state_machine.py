"""Report Lifecycle State Machine

Valid transitions:
  submitted        → qc_running          (system)
  qc_running       → qc_complete         (system)
  qc_running       → submitted           (system — error recovery)
  qc_complete      → approved            (reviewer, admin)
  qc_complete      → revision_requested  (reviewer, admin)
  revision_requested → resubmitted       (enforced by process_resubmission)
  resubmitted      → qc_running          (system)

Does NOT commit — caller commits.
"""
from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from app.core.auth import CurrentUser
from app.models.report import Report, ReportStatus
from app.models.revision import Revision, RevisionResponse, RevisionStatus

logger = logging.getLogger(__name__)

_TRANSITIONS: dict[tuple[str, str], list[str] | None] = {
    ("submitted",          "qc_running"):          None,
    ("qc_running",         "qc_complete"):          None,
    ("qc_running",         "submitted"):            None,
    ("qc_complete",        "approved"):             ["reviewer", "admin"],
    ("qc_complete",        "revision_requested"):   ["reviewer", "admin"],
    ("revision_requested", "resubmitted"):          None,
    ("resubmitted",        "qc_running"):           None,
}


class TransitionError(Exception):
    pass


def _apply_transition(report: Report, target: ReportStatus, actor: CurrentUser | None, db: Session) -> None:
    key = (report.status.value, target.value)
    allowed_roles = _TRANSITIONS.get(key)
    if key not in _TRANSITIONS:
        raise TransitionError(f"Invalid transition: {report.status.value} → {target.value} for report {report.id}")
    if allowed_roles is not None:
        if actor is None:
            raise TransitionError(f"Transition {key} requires an authenticated user")
        if actor.role not in allowed_roles:
            raise TransitionError(f"Role '{actor.role}' is not allowed to perform {key}. Allowed: {allowed_roles}")
    old_status = report.status.value
    report.status = target
    logger.info("Report status transition", extra={"report_id": report.id, "from_status": old_status, "to_status": target.value, "actor_id": actor.user_id if actor else "system", "actor_role": actor.role if actor else "system"})


def approve_report(report: Report, actor: CurrentUser, db: Session) -> None:
    _apply_transition(report, ReportStatus.approved, actor, db)
    open_revisions = db.query(Revision).filter(Revision.report_id == report.id, Revision.status == RevisionStatus.open).all()
    for rev in open_revisions:
        rev.status = RevisionStatus.closed
    if open_revisions:
        logger.info("Closed open revisions on approval", extra={"report_id": report.id, "revision_count": len(open_revisions)})


def request_revision(report: Report, actor: CurrentUser, notes: str, db: Session) -> Revision:
    if not notes or not notes.strip():
        raise TransitionError("Revision notes are required")
    _apply_transition(report, ReportStatus.revision_requested, actor, db)
    from app.models.user import User
    reviewer = db.query(User).filter(User.bubble_user_id == actor.user_id).first()
    if not reviewer:
        raise TransitionError(f"Reviewer user record not found for bubble_user_id={actor.user_id}")
    revision = Revision(report_id=report.id, requested_by_id=reviewer.id, run_number=report.run_number, notes=notes.strip(), status=RevisionStatus.open)
    db.add(revision)
    logger.info("Revision requested", extra={"report_id": report.id, "reviewer_id": reviewer.id, "run_number": report.run_number})
    return revision


def add_revision_response(revision: Revision, actor: CurrentUser, response_text: str, db: Session) -> RevisionResponse:
    if revision.status != RevisionStatus.open:
        raise TransitionError(f"Cannot respond to revision in '{revision.status.value}' status — must be open")
    if not response_text or not response_text.strip():
        raise TransitionError("Response text is required")
    from app.models.user import User
    responder = db.query(User).filter(User.bubble_user_id == actor.user_id).first()
    if not responder:
        raise TransitionError(f"Responder user record not found for bubble_user_id={actor.user_id}")
    response = RevisionResponse(revision_id=revision.id, responder_id=responder.id, response_text=response_text.strip())
    db.add(response)
    revision.status = RevisionStatus.responded
    logger.info("Revision response added", extra={"revision_id": revision.id, "report_id": revision.report_id, "responder_id": responder.id})
    return response
