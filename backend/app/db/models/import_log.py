import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

ImportSource = Enum("csv", "xlsx", "onec", "stocrm", name="import_source")
ImportStatus = Enum("processing", "completed", "failed", "rolled_back", name="import_status")


class ImportLog(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "imports"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    source: Mapped[str] = mapped_column(ImportSource, nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0)
    rows_skipped: Mapped[int] = mapped_column(Integer, default=0)

    errors: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(ImportStatus, default="processing")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
