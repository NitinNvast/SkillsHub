"""Employee model — the central entity. One employee may map to one User account."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.certification import Certification
    from app.db.models.embedding import EmployeeEmbedding
    from app.db.models.employee_skill import EmployeeSkill
    from app.db.models.project import Project


class Availability(str, Enum):
    ALLOCATED = "allocated"
    AVAILABLE = "available"
    PARTIAL = "partial"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    total_years_exp: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))

    # Staffing fields (for queries like "haven't been on a new project in last quarter")
    current_project: Mapped[str | None] = mapped_column(String(500))
    last_project_end_date: Mapped[date | None] = mapped_column(Date)
    availability: Mapped[str] = mapped_column(String(20), default="available", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ─── Relationships ─────────────────────────────────────
    skills: Mapped[list[EmployeeSkill]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    certifications: Mapped[list[Certification]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    embedding: Mapped[EmployeeEmbedding | None] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        uselist=False,
    )
