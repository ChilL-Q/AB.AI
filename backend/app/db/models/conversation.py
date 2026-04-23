import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey

ConversationChannel = Enum("whatsapp", "telegram", "sms", name="conversation_channel")
ConversationStatus = Enum("active", "resolved", "escalated", name="conversation_status")


class Conversation(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "conversations"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )

    channel: Mapped[str] = mapped_column(ConversationChannel, nullable=False)
    status: Mapped[str] = mapped_column(ConversationStatus, default="active")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "messages.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_conversations_last_read_message_id_messages",
        ),
        nullable=True,
    )

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="conversations")  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        back_populates="conversation",
        foreign_keys="Message.conversation_id",
    )
