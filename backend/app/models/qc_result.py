import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid


class FlagSeverity(str, enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"


class QCResult(Base, TimestampMixin):
    """
    Output of one QC engine run against a report.
    One row per run_number — full audit trail.

    raw_flags: complete JSONB output from the rule engine.
    score_breakdown: {"comparables": 28, "adjustments": 22, "market_analysis": 17,
                      "narrative": 13, "reconciliation": 9}
    """

    __tablename__ = "qc_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pass_fail: Mapped[bool] = mapped_column(Boolean, nullable=False)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    report: Mapped["Report"] = relationship("Report", back_populates="qc_results")
    flags: Mapped[list["QCFlag"]] = relationship("QCFlag", back_populates="qc_result", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<QCResult report={self.report_id} run={self.run_number} pass={self.pass_fail} score={self.quality_score}>"


class QCFlag(Base, TimestampMixin):
    """Individual flag from the rule engine."""

    __tablename__ = "qc_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    qc_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("qc_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rules.id", ondelete="SET NULL"), nullable=True
    )
    severity: Mapped[FlagSeverity] = mapped_column(
        Enum(FlagSeverity, name="flag_severity"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    value_found: Mapped[str | None] = mapped_column(String(512), nullable=True)
    value_expected: Mapped[str | None] = mapped_column(String(512), nullable=True)

    qc_result: Mapped["QCResult"] = relationship("QCResult", back_populates="flags")
    rule: Mapped["Rule | None"] = relationship("Rule")

    def __repr__(self) -> str:
        return f"<QCFlag {self.severity} {self.field_name}: {self.message[:60]}>"
