"""add embedding job leases

Revision ID: 20260701_0002
Revises: 20260629_0001
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260701_0002"
down_revision: str | None = "20260629_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "embedding_jobs",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "embedding_jobs",
        sa.Column("locked_by", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_embedding_jobs_locked_at", "embedding_jobs", ["locked_at"])


def downgrade() -> None:
    op.drop_index("ix_embedding_jobs_locked_at", table_name="embedding_jobs")
    op.drop_column("embedding_jobs", "locked_by")
    op.drop_column("embedding_jobs", "locked_at")
