"""Team builder pipeline."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Employee, EmployeeSkill

log = logging.getLogger(__name__)


async def _parse_project(description: str) -> dict:
    from app.ai.prompts.team_builder import PARSE_PROJECT_SYSTEM, PARSE_PROJECT_TOOL
    from app.ai.providers import ChatRequest, ai_manager
    from app.ai.providers.base import ProviderError

    request = ChatRequest(
        system=PARSE_PROJECT_SYSTEM,
        messages=[{"role": "user", "content": f"Parse this project description:\n\n{description}"}],
        tools=[PARSE_PROJECT_TOOL],
        tool_choice="any",
        max_tokens=512,
    )
    try:
        resp = await ai_manager.chat(request, task="parsing")
    except ProviderError as exc:
        log.warning("Project parsing failed (%s), using defaults", exc)
        return {
            "roles_needed": [],
            "must_have_skills": [],
            "domain": "general",
            "seniority_mix": "balanced",
        }

    call = resp.first_tool_call()
    if call is None:
        return {
            "roles_needed": [],
            "must_have_skills": [],
            "domain": "general",
            "seniority_mix": "balanced",
        }
    return call.arguments if isinstance(call.arguments, dict) else {}


async def _compose_team(
    description: str, requirements: dict, team_size: int, candidates: list[dict]
) -> dict:
    from app.ai.prompts.team_builder import (
        COMPOSE_TEAM_SYSTEM,
        COMPOSE_TEAM_TOOL,
        build_compose_message,
    )
    from app.ai.providers import ChatRequest, ai_manager
    from app.ai.providers.base import ProviderError

    user_msg = build_compose_message(description, requirements, team_size, candidates)
    request = ChatRequest(
        system=COMPOSE_TEAM_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        tools=[COMPOSE_TEAM_TOOL],
        tool_choice="any",
        max_tokens=4096,
    )
    try:
        resp = await ai_manager.chat(request, task="rerank")
    except ProviderError as exc:
        log.warning("Team composition failed (%s)", exc)
        return {
            "team": [],
            "team_rationale": "Unable to compose team due to AI provider error.",
            "gaps": [],
            "alternatives": [],
        }

    call = resp.first_tool_call()
    if call is None:
        return {
            "team": [],
            "team_rationale": "No team proposal generated.",
            "gaps": [],
            "alternatives": [],
        }
    return call.arguments if isinstance(call.arguments, dict) else {}


async def run_team_builder(
    session: AsyncSession, description: str, team_size: int, duration_weeks: int
) -> dict:
    # 1. Parse project requirements
    requirements = await _parse_project(description)
    log.info("Project requirements: %s", requirements)

    # 2. Load all approved employees
    result = await session.execute(
        select(Employee).options(
            selectinload(Employee.skills).joinedload(EmployeeSkill.skill),
        )
    )
    employees = result.scalars().all()

    # 3. Build candidate summaries
    candidates = []
    for emp in employees:
        top_skills = sorted(
            emp.skills,
            key=lambda s: (
                {"expert": 0, "intermediate": 1, "novice": 2}.get(s.proficiency, 1),
                -(float(s.years) if s.years else 0),
            ),
        )[:8]
        skills_summary = ", ".join(
            f"{s.skill.name}({s.proficiency[:3]})" for s in top_skills if s.skill
        )
        candidates.append(
            {
                "employee_id": str(emp.id),
                "name": emp.name,
                "title": emp.title,
                "availability": emp.availability,
                "total_years_exp": float(emp.total_years_exp) if emp.total_years_exp else None,
                "skills_summary": skills_summary,
                "skills_raw": top_skills,
            }
        )

    if not candidates:
        return {
            "description": description,
            "proposal": {
                "team": [],
                "team_rationale": "No employees found in the system.",
                "gaps": ["No candidates available"],
                "alternatives": [],
            },
            "total_candidates_considered": 0,
        }

    # 4. Compose team via Sonnet
    composition = await _compose_team(description, requirements, team_size, candidates)

    # 5. Build final response shape
    id_to_candidate = {c["employee_id"]: c for c in candidates}
    id_to_employee = {str(e.id): e for e in employees}

    def build_member(raw: dict) -> dict | None:
        eid = raw.get("employee_id", "")
        cand = id_to_candidate.get(eid)
        emp = id_to_employee.get(eid)
        if cand is None or emp is None:
            return None
        top_skills = [s.skill.name for s in cand.get("skills_raw", []) if s.skill][:5]
        return {
            "employee_id": UUID(eid),
            "name": emp.name,
            "title": emp.title,
            "role_in_project": raw.get("role_in_project", "Team Member"),
            "match_score": max(0, min(100, int(raw.get("match_score", 50)))),
            "rationale": raw.get("rationale", ""),
            "top_skills": top_skills,
        }

    team_members = [
        m for raw in composition.get("team", []) if (m := build_member(raw)) is not None
    ]
    alternatives = [
        m for raw in composition.get("alternatives", []) if (m := build_member(raw)) is not None
    ]

    return {
        "description": description,
        "proposal": {
            "team": team_members,
            "team_rationale": composition.get("team_rationale", ""),
            "gaps": composition.get("gaps", []),
            "alternatives": alternatives,
        },
        "total_candidates_considered": len(candidates),
    }
