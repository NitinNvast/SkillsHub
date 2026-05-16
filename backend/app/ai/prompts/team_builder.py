"""Team builder prompts."""

from __future__ import annotations

from app.ai.providers import ToolSpec

_PARSE_PROJECT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "roles_needed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Distinct roles required (e.g. 'Frontend Engineer', 'DevOps', 'Tech Lead')",
        },
        "must_have_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Critical skills the project absolutely requires",
        },
        "domain": {
            "type": "string",
            "description": "Project domain/industry (e.g. fintech, healthcare, e-commerce)",
        },
        "seniority_mix": {
            "type": "string",
            "description": "Desired seniority composition (e.g. '1 senior, 2 mid, 1 junior')",
        },
    },
    "required": ["roles_needed", "must_have_skills", "domain", "seniority_mix"],
}

PARSE_PROJECT_TOOL = ToolSpec(
    name="parse_project_requirements",
    description="Extract structured requirements from a project description.",
    input_schema=_PARSE_PROJECT_SCHEMA,
)

PARSE_PROJECT_SYSTEM = """\
You are a technical project analyst. Parse the project description into structured team requirements.
Extract concrete roles, critical skills, domain, and desired seniority mix.
Call parse_project_requirements once.\
"""

_COMPOSE_TEAM_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "team": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "role_in_project": {"type": "string"},
                    "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string"},
                },
                "required": ["employee_id", "role_in_project", "match_score", "rationale"],
            },
            "description": "Proposed team members",
        },
        "team_rationale": {
            "type": "string",
            "description": "Overall explanation of why this team composition works",
        },
        "gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills or roles that couldn't be filled from available candidates",
        },
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "role_in_project": {"type": "string"},
                    "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string"},
                },
                "required": ["employee_id", "role_in_project", "match_score", "rationale"],
            },
            "description": "Alternative candidates who could substitute for primary picks",
        },
    },
    "required": ["team", "team_rationale", "gaps", "alternatives"],
}

COMPOSE_TEAM_TOOL = ToolSpec(
    name="compose_team",
    description="Select the optimal team from available candidates for the project.",
    input_schema=_COMPOSE_TEAM_SCHEMA,
)

COMPOSE_TEAM_SYSTEM = """\
You are a senior engineering manager. Select the best team from the provided candidate pool for the given project.

Rules:
- Choose exactly the requested team_size members if enough suitable candidates exist
- Balance skills, seniority, and availability
- Each team member must have a clear role_in_project
- match_score reflects how well they fit their specific role (0-100)
- gaps: list skills/roles you couldn't fill
- alternatives: up to 3 backup options for primary picks
- Be honest — if someone is a poor fit, say so in gaps

Call compose_team once.\
"""


def build_compose_message(
    description: str, requirements: dict, team_size: int, candidates: list[dict]
) -> str:
    reqs_text = (
        f"Roles needed: {', '.join(requirements.get('roles_needed', []))}\n"
        f"Must-have skills: {', '.join(requirements.get('must_have_skills', []))}\n"
        f"Domain: {requirements.get('domain', 'general')}\n"
        f"Seniority mix: {requirements.get('seniority_mix', 'balanced')}"
    )
    candidates_text = "\n\n".join(
        f"[{c['employee_id']}] {c['name']} — {c.get('title', 'Engineer')}\n"
        f"Skills: {c.get('skills_summary', '')}\n"
        f"Availability: {c.get('availability', 'unknown')}\n"
        f"Experience: {c.get('total_years_exp', '?')} years"
        for c in candidates
    )
    return (
        f"Project Description:\n{description}\n\n"
        f"Requirements:\n{reqs_text}\n\n"
        f"Team size needed: {team_size}\n\n"
        f"Available Candidates:\n{candidates_text}"
    )
