"""GitHub skills sync service — infers active skills from recent commits and repo topics."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
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
    "YAML": "YAML",
    "Jupyter Notebook": "Python",
    "R": "R",
    "Dart": "Flutter",
    "Vue": "Vue.js",
}

# Topics in GitHub repos → skill name + category
_TOPIC_TO_SKILL: dict[str, tuple[str, str]] = {
    "react": ("React", "framework"),
    "reactjs": ("React", "framework"),
    "nextjs": ("Next.js", "framework"),
    "next-js": ("Next.js", "framework"),
    "vue": ("Vue.js", "framework"),
    "vuejs": ("Vue.js", "framework"),
    "angular": ("Angular", "framework"),
    "django": ("Django", "framework"),
    "fastapi": ("FastAPI", "framework"),
    "flask": ("Flask", "framework"),
    "spring": ("Spring", "framework"),
    "spring-boot": ("Spring Boot", "framework"),
    "express": ("Express.js", "framework"),
    "nestjs": ("NestJS", "framework"),
    "nodejs": ("Node.js", "platform"),
    "node": ("Node.js", "platform"),
    "kubernetes": ("Kubernetes", "platform"),
    "k8s": ("Kubernetes", "platform"),
    "docker": ("Docker", "tool"),
    "terraform": ("Terraform", "tool"),
    "postgresql": ("PostgreSQL", "platform"),
    "postgres": ("PostgreSQL", "platform"),
    "mysql": ("MySQL", "platform"),
    "mongodb": ("MongoDB", "platform"),
    "redis": ("Redis", "platform"),
    "elasticsearch": ("Elasticsearch", "platform"),
    "kafka": ("Apache Kafka", "platform"),
    "graphql": ("GraphQL", "tool"),
    "rest-api": ("REST APIs", "domain"),
    "machine-learning": ("Machine Learning", "domain"),
    "deep-learning": ("Deep Learning", "domain"),
    "pytorch": ("PyTorch", "framework"),
    "tensorflow": ("TensorFlow", "framework"),
    "scikit-learn": ("Scikit-learn", "framework"),
    "aws": ("AWS", "platform"),
    "gcp": ("Google Cloud", "platform"),
    "azure": ("Azure", "platform"),
    "github-actions": ("GitHub Actions", "tool"),
    "ci-cd": ("CI/CD", "tool"),
    "flutter": ("Flutter", "framework"),
    "react-native": ("React Native", "framework"),
    "android": ("Android", "platform"),
    "ios": ("iOS", "platform"),
    "tailwindcss": ("Tailwind CSS", "framework"),
    "tailwind": ("Tailwind CSS", "framework"),
    "svelte": ("Svelte", "framework"),
    "nuxt": ("Nuxt.js", "framework"),
    "airflow": ("Apache Airflow", "tool"),
    "langchain": ("LangChain", "framework"),
    "llm": ("LLM Engineering", "domain"),
    "openai": ("LLM Engineering", "domain"),
}

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _proficiency_from_bytes(nbytes: int) -> tuple[str, Decimal]:
    if nbytes > 500_000:
        return "expert", Decimal("3.0")
    if nbytes > 100_000:
        return "intermediate", Decimal("1.5")
    return "novice", Decimal("0.5")


def _proficiency_from_commits(commit_count: int, is_recent: bool) -> tuple[str, Decimal]:
    """Map commit count to proficiency; recent activity boosts the estimate."""
    if commit_count >= 50 or (is_recent and commit_count >= 20):
        return "expert", Decimal("3.0")
    if commit_count >= 15 or (is_recent and commit_count >= 5):
        return "intermediate", Decimal("1.5")
    return "novice", Decimal("0.5")


async def fetch_github_skills(github_username: str) -> list[dict]:
    """
    Infer active skills from a GitHub user's public repos:
    1. Repos sorted by recent push — recently-active repos weighted 3x in language bytes
    2. Repo topics → framework/tool/platform skills
    3. Events API — identifies repos pushed in last 90 days (recency signal)
    """
    headers = dict(_HEADERS)
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    cutoff = datetime.now(UTC) - timedelta(days=90)

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        # 1. Fetch user repos
        resp = await client.get(
            f"https://api.github.com/users/{github_username}/repos",
            params={"per_page": 30, "sort": "updated", "type": "owner"},
        )
        if resp.status_code == 404:
            raise ValueError(f"GitHub user '{github_username}' not found")
        if resp.status_code == 403:
            raise ValueError("GitHub API rate limited — add a GITHUB_TOKEN to increase limits")
        resp.raise_for_status()
        repos: list[dict] = resp.json()

        # 2. Fetch recent push events to identify recently-active repos
        recent_repos: set[str] = set()
        try:
            ev_resp = await client.get(
                f"https://api.github.com/users/{github_username}/events",
                params={"per_page": 100},
            )
            if ev_resp.status_code == 200:
                for event in ev_resp.json():
                    if event.get("type") != "PushEvent":
                        continue
                    created_at = event.get("created_at", "")
                    try:
                        ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if ts >= cutoff:
                            recent_repos.add(event["repo"]["name"].split("/")[-1])
                    except Exception:
                        pass
        except Exception:
            pass

        log.info("github: %s — %d repos, %d recently active", github_username, len(repos), len(recent_repos))

        # 3. Aggregate language bytes (weighted by recency) + topics
        lang_bytes: dict[str, int] = {}
        topic_hits: set[str] = set()
        repos_analyzed = 0

        for repo in repos[:15]:
            if repo.get("fork"):
                continue
            repos_analyzed += 1
            repo_name = repo.get("name", "")
            is_recent = repo_name in recent_repos
            weight = 3 if is_recent else 1

            # Collect topics
            for topic in repo.get("topics", []):
                topic_hits.add(topic.lower())

            # Collect language bytes
            try:
                lang_resp = await client.get(repo["languages_url"])
                if lang_resp.status_code == 200:
                    for lang, nbytes in lang_resp.json().items():
                        lang_bytes[lang] = lang_bytes.get(lang, 0) + nbytes * weight
            except Exception:
                pass

    # 4. Build skill list
    skills: dict[str, dict] = {}

    # Language-derived skills (from weighted byte counts)
    for lang, nbytes in lang_bytes.items():
        skill_name = _LANG_TO_SKILL.get(lang, lang)
        proficiency, years = _proficiency_from_bytes(nbytes)
        if skill_name not in skills:
            skills[skill_name] = {
                "name": skill_name,
                "category": "language",
                "proficiency": proficiency,
                "years": years,
                "confidence": Decimal("0.70"),
                "evidence": f"{nbytes:,} weighted bytes across public repositories",
            }
        else:
            # Keep highest proficiency seen
            existing = skills[skill_name]
            if proficiency == "expert" or (proficiency == "intermediate" and existing["proficiency"] == "novice"):
                existing["proficiency"] = proficiency
                existing["years"] = years

    # Topic-derived skills (frameworks, tools, platforms)
    for topic in topic_hits:
        if topic not in _TOPIC_TO_SKILL:
            continue
        skill_name, category = _TOPIC_TO_SKILL[topic]
        is_recent_topic = any(
            r.get("name", "") in recent_repos for r in repos if topic in r.get("topics", [])
        )
        proficiency = "intermediate" if is_recent_topic else "novice"
        years = Decimal("1.5") if is_recent_topic else Decimal("0.5")

        if skill_name not in skills:
            skills[skill_name] = {
                "name": skill_name,
                "category": category,
                "proficiency": proficiency,
                "years": years,
                "confidence": Decimal("0.65"),
                "evidence": f"Found in GitHub repo topics (recent activity: {is_recent_topic})",
            }
        else:
            # Topic signals upgrade novice language skills to intermediate
            existing = skills[skill_name]
            existing["category"] = category  # More specific category wins
            if existing["proficiency"] == "novice" and proficiency == "intermediate":
                existing["proficiency"] = "intermediate"
                existing["years"] = Decimal("1.5")

    # Sort: expert first, then intermediate, then novice; secondary: confidence desc
    ordered = sorted(
        skills.values(),
        key=lambda s: (
            {"expert": 0, "intermediate": 1, "novice": 2}[s["proficiency"]],
            -float(s["confidence"]),
        ),
    )

    log.info(
        "github: %s — %d skills extracted (%d from langs, %d from topics)",
        github_username, len(ordered),
        sum(1 for s in ordered if "bytes" in s.get("evidence", "")),
        sum(1 for s in ordered if "topics" in s.get("evidence", "")),
    )

    return ordered


async def sync_github_skills(
    session: AsyncSession, employee_id: UUID, github_username: str
) -> None:
    """Fetch GitHub skills and upsert into employee_skills."""
    from app.db.models import Employee, EmployeeSkill
    from app.db.models.employee_skill import SkillSource
    from app.db.models.skill import Skill

    skills_data = await fetch_github_skills(github_username)
    if not skills_data:
        log.warning("github: no skills found for user '%s'", github_username)
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
            skill = Skill(name=sd["name"], category=sd.get("category", "language"))
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
    log.info("github: synced %d skills for employee %s", len(skills_data), employee_id)
