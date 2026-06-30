import enum

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid


class RuleCategory(str, enum.Enum):
    uad_format = "uad_format"
    gse = "gse"
    uspap = "uspap"
    quality = "quality"


class RuleSeverity(str, enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"


class Rule(Base, TimestampMixin):
    """
    QC rule definition. Stored in DB so admins can toggle rules and adjust
    thresholds (via config JSONB) without a deploy.

    code: short unique identifier, e.g. "UAD-001", "FNMA-045", "USPAP-SR1"
    config: adjustable thresholds, e.g. {"max_net_adjustment_pct": 15}
    """

    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    category: Mapped[RuleCategory] = mapped_column(
        Enum(RuleCategory, name="rule_category"), nullable=False, index=True
    )
    severity: Mapped[RuleSeverity] = mapped_column(
        Enum(RuleSeverity, name="rule_severity"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<Rule {self.code} [{self.category}] enabled={self.enabled}>"
