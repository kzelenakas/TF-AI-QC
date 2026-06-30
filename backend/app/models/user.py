import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid


class UserRole(str, enum.Enum):
    appraiser = "appraiser"
    reviewer = "reviewer"
    admin = "admin"


class User(Base, TimestampMixin):
    """
    Mirrors the user record from the True Footage Bubble OMS.
    bubble_user_id is the authoritative identifier from Bubble auth tokens.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    bubble_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.appraiser
    )
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="uploader", foreign_keys="Report.uploader_id")
    revisions_requested: Mapped[list["Revision"]] = relationship("Revision", back_populates="requested_by")

    def __repr__(self) -> str:
        return f"<User {self.bubble_user_id} role={self.role}>"
