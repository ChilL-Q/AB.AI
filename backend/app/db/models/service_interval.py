"""Service interval model + deterministic reminder engine.

ServiceInterval defines recurring maintenance (oil change every 10000 km / 6 months).
The reminder engine finds cars that are due for a service and enriches the
outreach prompt with that information.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

IntervalUnit = Enum("km", "days", "months", name="interval_unit")


class ServiceInterval(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "service_intervals"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    interval_value: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_unit: Mapped[str] = mapped_column(IntervalUnit, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)