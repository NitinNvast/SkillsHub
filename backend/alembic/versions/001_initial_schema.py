"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Extensions ────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ─── users ─────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ─── employees ─────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("title", sa.String(255)),
        sa.Column("summary", sa.Text),
        sa.Column("total_years_exp", sa.Numeric(4, 1)),
        sa.Column("current_project", sa.String(500)),
        sa.Column("last_project_end_date", sa.Date),
        sa.Column("availability", sa.String(20), nullable=False, server_default="available"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("email", name="uq_employees_email"),
    )
    op.create_index("ix_employees_email", "employees", ["email"], unique=True)

    # ─── skills_catalog ────────────────────────────────────
    op.create_table(
        "skills_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.UniqueConstraint("name", name="uq_skills_catalog_name"),
    )
    op.create_index("ix_skills_catalog_name", "skills_catalog", ["name"], unique=True)
    op.execute(
        "CREATE INDEX ix_skills_catalog_name_trgm ON skills_catalog USING gin (name gin_trgm_ops)"
    )

    # ─── employee_skills ───────────────────────────────────
    op.create_table(
        "employee_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("proficiency", sa.String(20), nullable=False),
        sa.Column("years", sa.Numeric(4, 1)),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2)),
        sa.Column("evidence", sa.Text),
        sa.UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),
    )
    op.create_index("ix_employee_skills_employee_id", "employee_skills", ["employee_id"])
    op.create_index("ix_employee_skills_skill_id", "employee_skills", ["skill_id"])

    # ─── projects ──────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("technologies", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
    )
    op.create_index("ix_projects_employee_id", "projects", ["employee_id"])

    # ─── certifications ────────────────────────────────────
    op.create_table(
        "certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255)),
        sa.Column("year", sa.Integer),
    )
    op.create_index("ix_certifications_employee_id", "certifications", ["employee_id"])

    # ─── resume_uploads ────────────────────────────────────
    op.create_table(
        "resume_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(1024)),
        sa.Column("raw_text", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="processing"),
        sa.Column("extracted_payload", postgresql.JSONB),
        sa.Column("notes", sa.Text),
        sa.Column("error", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_resume_uploads_status", "resume_uploads", ["status"])
    op.create_index("ix_resume_uploads_employee_id", "resume_uploads", ["employee_id"])

    # ─── employee_embeddings (pgvector) ────────────────────
    op.create_table(
        "employee_embeddings",
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("vector", Vector(1024), nullable=False),
        sa.Column("summary_text", sa.Text, nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.execute(
        "CREATE INDEX ix_employee_embeddings_vector_hnsw "
        "ON employee_embeddings USING hnsw (vector vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_table("employee_embeddings")
    op.drop_table("resume_uploads")
    op.drop_table("certifications")
    op.drop_table("projects")
    op.drop_table("employee_skills")
    op.drop_table("skills_catalog")
    op.drop_table("employees")
    op.drop_table("users")
