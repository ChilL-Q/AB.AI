import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

AgentMode = Enum("auto", "semi_auto", "manual", name="agent_mode")


class AIAgentConfig(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "ai_agent_configs"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, unique=True
    )

    mode: Mapped[str] = mapped_column(AgentMode, default="semi_auto")
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(Text, default="friendly")
    knowledge_base: Mapped[dict] = mapped_column(JSONB, default=dict)
    forbidden_topics: Mapped[list] = mapped_column(JSON, default=list)
    escalation_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
