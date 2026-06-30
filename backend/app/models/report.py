import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid


class FileType(str, enum.Enum):
    xml = "xml"
    pdf = "pdf"


class ReportStatus(str, enum.Enum):
    submitted = "submitted"
    qc_running = "qc_running"
    qc_complete = "qc_complete"
    approved = "approved"
    revision_requested = "revision_requested"
    resubmitted = "resubmitted"


class Report(Base, TimestampMixin):
    """
    Represents one uploaded appraisal report (URAR / UAD 3.6).

    file_url is the R2 object key — NEVER a signed URL.
    Generate signed URLs at request time via storage.generate_presigned_url().

    property_address is stored for display in the reviewer UI only.
    It is NEVER written to application logs (GLBA NPI).
    """

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    uploader_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type"), nullable=False
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"),
        nullable=False,
        default=ReportStatus.submitted,
        index=True,
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    property_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    borrower_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    uploader: Mapped["User"] = relationship("User", back_populates="reports", foreign_keys=[uploader_id])
    qc_results: Mapped[list["QCResult"]] = relationship("QCResult", back_populates="report", cascade="all, delete-orphan")
    revisions: Mapped[list["Revision"]] = relationship("Revision", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Report {self.id} status={self.status} run={self.run_number}>"
