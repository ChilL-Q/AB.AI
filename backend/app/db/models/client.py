import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

ClientSource = Enum("manual", "import", "self_register", name="client_source")


class Client(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clients"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    telegram_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    whatsapp_opted_in: Mapped[bool] = mapped_column(Boolean, default=False)

    total_visits: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[str] = mapped_column(ClientSource, default="manual")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Unique per team
    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("team_id", "phone", name="uq_client_team_phone"),
    )

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="clients")  # noqa: F821
    cars: Mapped[list["Car"]] = relationship(back_populates="client")  # noqa: F821
    visits: Mapped[list["Visit"]] = relationship(back_populates="client")  # noqa: F821
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="client")  # noqa: F821
