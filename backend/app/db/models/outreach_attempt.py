import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

OutreachStatus = Enum("pending", "sent", "replied", "escalated", "failed", name="outreach_status")


class OutreachAttempt(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "outreach_attempts"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(OutreachStatus, default="pending")
    reason: Mapped[dict] = mapped_column(JSONB, default=dict)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    resulted_in_visit: Mapped[bool] = mapped_column(default=False)
    resulted_in_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    client: Mapped["Client"] = relationship(back_populates="outreach_attempts")  # noqa: F821
