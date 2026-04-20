import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

WhatsAppTemplateStatus = Enum("pending", "approved", "rejected", name="whatsapp_template_status")


class Template(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "templates"

    # NULL = global system template
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channels: Mapped[list] = mapped_column(JSON, default=list)

    whatsapp_template_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp_status: Mapped[str | None] = mapped_column(WhatsAppTemplateStatus, nullable=True)
