"""Search request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.skill import EmployeeSkillOut


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    limit: int = Field(default=8, ge=1, le=20)


class ParsedQuery(BaseModel):
    """Structured interpretation of the NL query — shown in UI for transparency."""

    semantic_text: str
    required_skills: list[str] = []
    min_years_per_skill: dict[str, float] = {}
    location: str | None = None
    availability: list[str] = []
    seniority_hint: str | None = None


class SearchResultItem(BaseModel):
    employee_id: UUID
    name: str
    title: str | None = None
    location: str | None = None
    availability: str
    total_years_exp: float | None = None
    match_score: int = Field(ge=0, le=100, description="0–100 match percentage")
    reasoning: str = Field(description="Plain-English explanation of why this candidate matches")
    strengths: list[str] = Field(default_factory=list, description="Specific matching strengths")
    gaps: list[str] = Field(default_factory=list, description="Missing or weak requirements")
    top_skills: list[EmployeeSkillOut] = Field(default_factory=list)
    similarity: float = Field(description="Raw cosine similarity score from pgvector")


class SearchResponse(BaseModel):
    query: str
    parsed_query: ParsedQuery
    results: list[SearchResultItem]
    total_candidates_retrieved: int
