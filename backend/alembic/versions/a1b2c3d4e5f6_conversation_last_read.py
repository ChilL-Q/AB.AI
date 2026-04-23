"""add last_read_message_id to conversations

Revision ID: a1b2c3d4e5f6
Revises: 27ef250bcb2a
Create Date: 2026-04-23 17:30:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "27ef250bcb2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("last_read_message_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversations_last_read_message_id_messages",
        "conversations",
        "messages",
        ["last_read_message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_conversations_last_read_message_id_messages",
        "conversations",
        type_="foreignkey",
    )
    op.drop_column("conversations", "last_read_message_id")
