"""Skill I/O schemas."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str
    aliases: list[str] = []


class EmployeeSkillOut(BaseModel):
    """A skill as it appears on an employee's profile."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    name: str               # flattened from skill.name
    category: str           # flattened from skill.category
    proficiency: str
    years: Decimal | None = None
    source: str             # 'extracted' | 'inferred' | 'manual'
    confidence: Decimal | None = None
    evidence: str | None = None

    @classmethod
    def from_orm_row(cls, es) -> "EmployeeSkillOut":
        return cls(
            id=es.id,
            skill_id=es.skill_id,
            name=es.skill.name,
            category=es.skill.category,
            proficiency=es.proficiency,
            years=es.years,
            source=es.source,
            confidence=es.confidence,
            evidence=es.evidence,
        )


class SkillGapItem(BaseModel):
    name: str
    category: str
    employee_count: int = Field(description="Number of employees who have this skill (extracted/manual)")
    expert_count: int = Field(description="Employees with expert-level proficiency")
    gap_severity: str = Field(description="critical | warning | healthy")
