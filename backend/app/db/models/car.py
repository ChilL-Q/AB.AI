import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Car(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "cars"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )

    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_plate: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, index=True)

    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_service_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_service_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="cars")  # noqa: F821
    visits: Mapped[list["Visit"]] = relationship(back_populates="car")  # noqa: F821
