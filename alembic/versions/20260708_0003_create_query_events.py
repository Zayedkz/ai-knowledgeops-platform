"""create query events

Revision ID: 20260708_0003
Revises: 20260701_0002
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260708_0003"
down_revision: str | None = "20260701_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "query_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("metadata_filter", sa.JSON(), nullable=True),
        sa.Column("selected_chunk_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("citation_scores", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_query_events_created_at", "query_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_query_events_created_at", table_name="query_events")
    op.drop_table("query_events")
