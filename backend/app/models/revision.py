import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid


class RevisionStatus(str, enum.Enum):
    open = "open"
    responded = "responded"
    closed = "closed"


class Revision(Base, TimestampMixin):
    """Revision request issued by a reviewer. Only reviewers/admins can create."""

    __tablename__ = "revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[RevisionStatus] = mapped_column(
        Enum(RevisionStatus, name="revision_status"),
        nullable=False,
        default=RevisionStatus.open,
    )

    report: Mapped["Report"] = relationship("Report", back_populates="revisions")
    requested_by: Mapped["User"] = relationship("User", back_populates="revisions_requested")
    responses: Mapped[list["RevisionResponse"]] = relationship(
        "RevisionResponse", back_populates="revision", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Revision {self.id} report={self.report_id} status={self.status}>"


class RevisionResponse(Base, TimestampMixin):
    """Appraiser's response to a revision request."""

    __tablename__ = "revision_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    responder_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    response_text: Mapped[str] = mapped_column(Text, nullable=False)

    revision: Mapped["Revision"] = relationship("Revision", back_populates="responses")
    responder: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<RevisionResponse {self.id} revision={self.revision_id}>"
