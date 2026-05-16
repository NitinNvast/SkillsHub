"""Employee + project + certification I/O schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.skill import EmployeeSkillOut


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    technologies: list[str] = []


class CertificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    issuer: str | None = None
    year: int | None = None


class EmployeeListItem(BaseModel):
    """Lightweight directory row."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    title: str | None = None
    location: str | None = None
    total_years_exp: Decimal | None = None
    availability: str
    top_skills: list[str] = []  # populated by service layer (5 names)


class EmployeeDetail(BaseModel):
    """Full profile view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    title: str | None = None
    location: str | None = None
    summary: str | None = None
    total_years_exp: Decimal | None = None
    current_project: str | None = None
    last_project_end_date: date | None = None
    availability: str
    created_at: datetime
    updated_at: datetime

    skills: list[EmployeeSkillOut] = []
    projects: list[ProjectOut] = []
    certifications: list[CertificationOut] = []


class EmployeeUpdate(BaseModel):
    """Partial update — HR for anyone, employee for their own profile."""

    name: str | None = None
    title: str | None = None
    location: str | None = None
    summary: str | None = None
    current_project: str | None = None
    last_project_end_date: date | None = None
    availability: str | None = None


class CreateEmployeeRequest(BaseModel):
    """HR creates a new employee account."""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6)
    title: str | None = None
    location: str | None = None


class GitHubSyncRequest(BaseModel):
    github_username: str = Field(min_length=1, max_length=100)
