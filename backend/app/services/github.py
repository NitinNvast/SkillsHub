"""GitHub skills sync service."""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

log = logging.getLogger(__name__)

_LANG_TO_SKILL: dict[str, str] = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Java": "Java",
    "Go": "Go",
    "Rust": "Rust",
    "C++": "C++",
    "C#": "C#",
    "Ruby": "Ruby",
    "PHP": "PHP",
    "Swift": "Swift",
    "Kotlin": "Kotlin",
    "Scala": "Scala",
    "Shell": "Bash",
    "HCL": "Terraform",
    "Dockerfile": "Docker",
}

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_github_skills(github_username: str) -> list[dict]:
    """Fetch repos, aggregate language bytes, map to skill dicts."""
    headers = dict(_HEADERS)
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        resp = await client.get(
            f"https://api.github.com/users/{github_username}/repos",
            params={"per_page": 30, "sort": "updated", "type": "owner"},
        )
        if resp.status_code == 404:
            raise ValueError(f"GitHub user '{github_username}' not found")
        if resp.status_code == 403:
            raise ValueError("GitHub API rate limited — add a GITHUB_TOKEN to increase limits")
        resp.raise_for_status()
        repos = resp.json()

        # Aggregate language bytes across top 10 non-fork repos
        lang_bytes: dict[str, int] = {}
        for repo in repos[:10]:
            if repo.get("fork"):
                continue
            try:
                lang_resp = await client.get(repo["languages_url"])
                if lang_resp.status_code == 200:
                    for lang, nbytes in lang_resp.json().items():
                        lang_bytes[lang] = lang_bytes.get(lang, 0) + nbytes
            except Exception:
                pass

    skills = []
    for lang, nbytes in sorted(lang_bytes.items(), key=lambda x: -x[1]):
        skill_name = _LANG_TO_SKILL.get(lang, lang)
        if nbytes > 500_000:
            proficiency, years = "expert", Decimal("3.0")
        elif nbytes > 100_000:
            proficiency, years = "intermediate", Decimal("1.5")
        else:
            proficiency, years = "novice", Decimal("0.5")
        skills.append(
            {
                "name": skill_name,
                "proficiency": proficiency,
                "years": years,
                "confidence": Decimal("0.70"),
                "evidence": f"{nbytes:,} bytes across public repositories",
            }
        )

    return skills


async def sync_github_skills(
    session: AsyncSession, employee_id: UUID, github_username: str
) -> None:
    """Fetch GitHub skills and upsert into employee_skills."""
    from app.db.models import Employee, EmployeeSkill
    from app.db.models.employee_skill import SkillSource
    from app.db.models.skill import Skill

    skills_data = await fetch_github_skills(github_username)
    if not skills_data:
        return

    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if emp is None:
        raise ValueError("Employee not found")
    emp.github_username = github_username

    skill_names = [s["name"] for s in skills_data]
    catalog_result = await session.execute(select(Skill).where(Skill.name.in_(skill_names)))
    catalog: dict[str, Skill] = {s.name: s for s in catalog_result.scalars().all()}

    for sd in skills_data:
        skill = catalog.get(sd["name"])
        if skill is None:
            skill = Skill(name=sd["name"], category="language")
            session.add(skill)
            await session.flush()
            catalog[sd["name"]] = skill

        existing = await session.execute(
            select(EmployeeSkill).where(
                EmployeeSkill.employee_id == employee_id,
                EmployeeSkill.skill_id == skill.id,
            )
        )
        emp_skill = existing.scalar_one_or_none()
        if emp_skill is None:
            session.add(
                EmployeeSkill(
                    employee_id=employee_id,
                    skill_id=skill.id,
                    proficiency=sd["proficiency"],
                    years=sd["years"],
                    source=SkillSource.GITHUB.value,
                    confidence=sd["confidence"],
                    evidence=sd["evidence"],
                )
            )
        else:
            emp_skill.proficiency = sd["proficiency"]
            emp_skill.years = sd["years"]
            emp_skill.source = SkillSource.GITHUB.value
            emp_skill.confidence = sd["confidence"]
            emp_skill.evidence = sd["evidence"]

    await session.commit()
