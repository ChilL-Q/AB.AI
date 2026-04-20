import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

CampaignType = Enum("one_time", "recurring", "triggered", name="campaign_type")
CampaignStatus = Enum("draft", "running", "paused", "completed", "archived", name="campaign_status")


class Campaign(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "campaigns"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(CampaignType, nullable=False)
    status: Mapped[str] = mapped_column(CampaignStatus, default="draft")

    trigger: Mapped[dict] = mapped_column(JSONB, default=dict)
    channels: Mapped[list] = mapped_column(JSON, default=list)
    schedule: Mapped[dict] = mapped_column(JSONB, default=dict)

    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True
    )

    stats: Mapped[dict] = mapped_column(JSONB, default=dict)
    ab_test_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
