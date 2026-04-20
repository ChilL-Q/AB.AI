import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

SubscriptionPlan = Enum("start", "pro", "business", "enterprise", name="subscription_plan")
SubscriptionStatus = Enum("trialing", "active", "past_due", "canceled", name="subscription_status")
PaymentProvider = Enum("stripe", "kaspi", "halyk", "yukassa", name="payment_provider")


class Subscription(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "subscriptions"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, unique=True
    )

    plan: Mapped[str] = mapped_column(SubscriptionPlan, default="start")
    status: Mapped[str] = mapped_column(SubscriptionStatus, default="trialing")

    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payment_provider: Mapped[str | None] = mapped_column(PaymentProvider, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="subscription")  # noqa: F821
