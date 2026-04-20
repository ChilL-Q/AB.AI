import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

VisitSource = Enum("manual", "onec", "stocrm", name="visit_source")


class Visit(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "visits"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cars.id"), nullable=True
    )
    mechanic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    services: Mapped[list] = mapped_column(JSONB, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(VisitSource, default="manual")

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="visits")  # noqa: F821
    car: Mapped["Car | None"] = relationship(back_populates="visits")  # noqa: F821
