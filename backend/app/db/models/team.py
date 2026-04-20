import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Team(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Almaty")
    locale: Mapped[str] = mapped_column(String(10), default="ru")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="team")  # noqa: F821
    clients: Mapped[list["Client"]] = relationship(back_populates="team")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship(back_populates="team")  # noqa: F821
