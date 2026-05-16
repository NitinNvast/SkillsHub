"""add github_username to employees

Revision ID: 002
Revises: 001
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("github_username", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("employees", "github_username")
