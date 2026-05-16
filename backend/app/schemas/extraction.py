"""Pydantic models for the LLM extraction output (StructuredProfile).

These are the shapes the LLM returns via tool_use. They are NOT the same as
the DB models — they're the raw AI output before normalization and persistence.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedSkill(BaseModel):
    name: str = Field(description="Skill name, normalized to the canonical taxonomy where possible")
    proficiency: str = Field(description="One of: novice | intermediate | expert")
    years: float | None = Field(None, description="Years of experience with this skill")
    evidence: str | None = Field(
        None, description="Verbatim or close-paraphrase quote from the resume proving this skill"
    )
    confidence: float = Field(description="0.0–1.0 — how confident the extraction is")


class ExtractedProject(BaseModel):
    name: str
    role: str | None = None
    description: str = Field(description="2–4 sentence summary of what was built and the impact")
    start_date: str | None = Field(None, description="YYYY-MM or YYYY")
    end_date: str | None = Field(None, description="YYYY-MM, YYYY, or null if current")
    technologies: list[str] = Field(default_factory=list)


class ExtractedCertification(BaseModel):
    name: str
    issuer: str | None = None
    year: int | None = None


class StructuredProfile(BaseModel):
    """The complete structured output from the extraction pipeline."""

    name: str
    email: str | None = None
    location: str | None = None
    title: str | None = Field(None, description="Current or most recent job title")
    total_years_exp: float | None = Field(None, description="Estimated total professional years")
    summary: str | None = Field(None, description="2–3 sentence professional summary")
    skills: list[ExtractedSkill] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    certifications: list[ExtractedCertification] = Field(default_factory=list)
