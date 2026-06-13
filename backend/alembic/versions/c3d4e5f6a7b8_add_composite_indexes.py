"""add composite indexes for message queries and conversation reads

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-13 20:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Composite index for message list queries: conversation_id + direction + created_at DESC
    # Improves performance of list_messages() operations when filtering by conversation and direction
    op.create_index(
        "ix_messages_conversation_direction_created",
        "messages",
        ["conversation_id", "direction", "created_at"],
        unique=False,
    )

    # Index for conversation last_read_message_id lookups
    # Improves performance of unread count aggregation queries
    op.create_index(
        "ix_conversations_last_read_message_id",
        "conversations",
        ["last_read_message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_last_read_message_id", table_name="conversations")
    op.drop_index("ix_messages_conversation_direction_created", table_name="messages")
