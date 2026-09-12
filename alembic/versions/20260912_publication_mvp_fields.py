"""add publication MVP fields

Revision ID: 20260912_publication_mvp_fields
Revises:
Create Date: 2026-09-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260912_publication_mvp_fields"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE publications ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500)"
    )
    op.execute(
        "ALTER TABLE publications "
        "ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE publications DROP COLUMN IF EXISTS is_published")
    op.execute("ALTER TABLE publications DROP COLUMN IF EXISTS thumbnail_url")
