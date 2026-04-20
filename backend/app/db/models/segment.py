import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Segment(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "segments"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    clients_count: Mapped[int] = mapped_column(Integer, default=0)
