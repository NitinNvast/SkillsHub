"""Employee↔Skill association with metadata: proficiency, years, source, confidence, evidence."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.employee import Employee
    from app.db.models.skill import Skill


class ProficiencyLevel(str, Enum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class SkillSource(str, Enum):
    EXTRACTED = "extracted"  # Pulled directly from resume by Claude
    INFERRED = "inferred"  # Derived (e.g., Next.js→React) by Haiku
    MANUAL = "manual"  # Added/edited by employee or HR


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    __table_args__ = (UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skills_catalog.id", ondelete="CASCADE"), nullable=False
    )

    proficiency: Mapped[str] = mapped_column(String(20), nullable=False)  # ProficiencyLevel
    years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # SkillSource
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))  # 0.00–1.00
    evidence: Mapped[str | None] = mapped_column(Text)  # LLM rationale snippet

    employee: Mapped[Employee] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(lazy="joined")
