"""Team builder request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TeamBuilderRequest(BaseModel):
    description: str = Field(min_length=20, max_length=2000)
    team_size: int = Field(default=4, ge=2, le=8)
    duration_weeks: int = Field(default=8, ge=1, le=52)


class TeamMemberProposal(BaseModel):
    employee_id: UUID
    name: str
    title: str | None = None
    role_in_project: str
    match_score: int = Field(ge=0, le=100)
    rationale: str
    top_skills: list[str] = []


class TeamProposal(BaseModel):
    team: list[TeamMemberProposal]
    team_rationale: str
    gaps: list[str] = []
    alternatives: list[TeamMemberProposal] = []


class TeamBuilderResponse(BaseModel):
    description: str
    proposal: TeamProposal
    total_candidates_considered: int
