"""GitHub skills sync — infers active skills from recent commit file analysis."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import PurePosixPath
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

log = logging.getLogger(__name__)

# File extension → (skill_name, category)
_EXT_TO_SKILL: dict[str, tuple[str, str]] = {
    ".py":     ("Python",     "language"),
    ".ipynb":  ("Python",     "language"),
    ".ts":     ("TypeScript", "language"),
    ".tsx":    ("TypeScript", "language"),
    ".js":     ("JavaScript", "language"),
    ".jsx":    ("JavaScript", "language"),
    ".java":   ("Java",       "language"),
    ".go":     ("Go",         "language"),
    ".rs":     ("Rust",       "language"),
    ".rb":     ("Ruby",       "language"),
    ".php":    ("PHP",        "language"),
    ".kt":     ("Kotlin",     "language"),
    ".swift":  ("Swift",      "language"),
    ".dart":   ("Flutter",    "framework"),
    ".cs":     ("C#",         "language"),
    ".cpp":    ("C++",        "language"),
    ".cc":     ("C++",        "language"),
    ".c":      ("C",          "language"),
    ".h":      ("C",          "language"),
    ".scala":  ("Scala",      "language"),
    ".r":      ("R",          "language"),
    ".tf":     ("Terraform",  "tool"),
    ".sql":    ("SQL",        "domain"),
    ".vue":    ("Vue.js",     "framework"),
    ".svelte": ("Svelte",     "framework"),
    ".sh":     ("Bash",       "tool"),
    ".bash":   ("Bash",       "tool"),
    ".yaml":   ("YAML",       "tool"),
    ".yml":    ("YAML",       "tool"),
}

# Special filenames (no extension) → (skill_name, category)
_FILENAME_TO_SKILL: dict[str, tuple[str, str]] = {
    "dockerfile":         ("Docker",     "tool"),
    "docker-compose.yml": ("Docker",     "tool"),
    "docker-compose.yaml":("Docker",     "tool"),
    "cargo.toml":         ("Rust",       "language"),
    "go.mod":             ("Go",         "language"),
    "requirements.txt":   ("Python",     "language"),
    "pyproject.toml":     ("Python",     "language"),
    "package.json":       ("Node.js",    "platform"),
    "gemfile":            ("Ruby",       "language"),
    "build.gradle":       ("Java",       "language"),
    "pom.xml":            ("Java",       "language"),
    "pubspec.yaml":       ("Flutter",    "framework"),
    "*.tf":               ("Terraform",  "tool"),
    "helmfile.yaml":      ("Kubernetes", "platform"),
    "chart.yaml":         ("Kubernetes", "platform"),
}

# File extension combos that imply additional framework skills
_INFER_EXTRA: dict[str, list[tuple[str, str]]] = {
    ".tsx": [("React", "framework")],
    ".jsx": [("React", "framework")],
}

# Repo topics → (skill_name, category)
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
    "kubernetes": ("Kubernetes", "platform"),
    "k8s": ("Kubernetes", "platform"),
    "docker": ("Docker", "tool"),
    "terraform": ("Terraform", "tool"),
    "postgresql": ("PostgreSQL", "platform"),
    "mongodb": ("MongoDB", "platform"),
    "redis": ("Redis", "platform"),
    "graphql": ("GraphQL", "tool"),
    "machine-learning": ("Machine Learning", "domain"),
    "deep-learning": ("Deep Learning", "domain"),
    "pytorch": ("PyTorch", "framework"),
    "tensorflow": ("TensorFlow", "framework"),
    "aws": ("AWS", "platform"),
    "gcp": ("Google Cloud", "platform"),
    "azure": ("Azure", "platform"),
    "github-actions": ("GitHub Actions", "tool"),
    "flutter": ("Flutter", "framework"),
    "react-native": ("React Native", "framework"),
    "tailwindcss": ("Tailwind CSS", "framework"),
    "svelte": ("Svelte", "framework"),
    "langchain": ("LangChain", "framework"),
    "llm": ("LLM Engineering", "domain"),
    "airflow": ("Apache Airflow", "tool"),
    "kafka": ("Apache Kafka", "platform"),
    "elasticsearch": ("Elasticsearch", "platform"),
}

_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _ext_skill(filename: str) -> list[tuple[str, str]]:
    """Return (skill, category) pairs for a changed filename."""
    name_lower = PurePosixPath(filename).name.lower()
    if name_lower in _FILENAME_TO_SKILL:
        return [_FILENAME_TO_SKILL[name_lower]]
    ext = PurePosixPath(filename).suffix.lower()
    hits = []
    if ext in _EXT_TO_SKILL:
        hits.append(_EXT_TO_SKILL[ext])
    for extra in _INFER_EXTRA.get(ext, []):
        hits.append(extra)
    return hits


def _proficiency(commit_count: int) -> tuple[str, Decimal]:
    if commit_count >= 10:
        return "expert", Decimal("3.0")
    if commit_count >= 3:
        return "intermediate", Decimal("1.5")
    return "novice", Decimal("0.5")


async def fetch_github_skills(github_username: str) -> list[dict]:
    """
    Three-layer skill inference from a GitHub user's public activity:

    1. **Commit file analysis** (highest fidelity) — fetches up to 20 recent commit
       diffs and maps changed file extensions to skills. .tsx implies React,
       Dockerfile implies Docker, go.mod implies Go, etc.
    2. **Repo topics** — catches frameworks/tools that don't appear in file extensions
       (React, FastAPI, Kubernetes, etc. declared in repo metadata).
    3. **Language byte fallback** — for skills not seen in recent commits, language
       bytes from the most recently-pushed repos provide a historical baseline.
    """
    headers = dict(_HEADERS)
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    cutoff = datetime.now(UTC) - timedelta(days=90)

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:

        # ── 1. Fetch user repos ────────────────────────────────────────────────
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

        # Collect repo topics
        topic_hits: set[str] = set()
        for repo in repos:
            if not repo.get("fork"):
                for t in repo.get("topics", []):
                    topic_hits.add(t.lower())

        # ── 2. Events → recently-active repos ─────────────────────────────────
        # PushEvent payloads often have 0 commits for org repos, so we collect
        # the *repo names* from events and query commit history directly.
        recent_repos_ordered: list[str] = []   # repo full names, most-recent first
        seen_repos: set[str] = set()

        try:
            ev_resp = await client.get(
                f"https://api.github.com/users/{github_username}/events",
                params={"per_page": 100},
            )
            if ev_resp.status_code == 200:
                for event in ev_resp.json():
                    if event.get("type") not in ("PushEvent", "CreateEvent"):
                        continue
                    raw_ts = event.get("created_at", "")
                    try:
                        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if ts < cutoff:
                        continue
                    repo_full = event["repo"]["name"]
                    if repo_full not in seen_repos:
                        seen_repos.add(repo_full)
                        recent_repos_ordered.append(repo_full)
        except Exception as exc:
            log.warning("github: events fetch failed for %s: %s", github_username, exc)

        log.info(
            "github: %s — %d repos, %d recently-active repos",
            github_username, len(repos), len(recent_repos_ordered),
        )

        # ── 3. Per-repo: fetch recent commits by author → file diffs ──────────
        # For each recently-active repo (up to 5), get the last 5 commits by
        # this author and collect changed file extensions.
        commit_skill_counts: dict[str, int] = {}   # skill_name -> commit count
        commit_skill_meta: dict[str, str] = {}      # skill_name -> category
        commits_analyzed = 0

        for repo_full in recent_repos_ordered[:5]:
            try:
                since_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
                commits_resp = await client.get(
                    f"https://api.github.com/repos/{repo_full}/commits",
                    params={"author": github_username, "since": since_str, "per_page": 5},
                )
                if commits_resp.status_code not in (200, 206):
                    continue
                commit_list = commits_resp.json()
                if not isinstance(commit_list, list):
                    continue

                for commit_stub in commit_list[:5]:
                    sha = commit_stub.get("sha", "")
                    if not sha:
                        continue
                    try:
                        c_resp = await client.get(
                            f"https://api.github.com/repos/{repo_full}/commits/{sha}",
                        )
                        if c_resp.status_code != 200:
                            continue
                        commit_data = c_resp.json()
                        skills_in_commit: set[str] = set()
                        for f in commit_data.get("files", []):
                            for skill_name, category in _ext_skill(f.get("filename", "")):
                                skills_in_commit.add(skill_name)
                                commit_skill_meta[skill_name] = category
                        for skill_name in skills_in_commit:
                            commit_skill_counts[skill_name] = (
                                commit_skill_counts.get(skill_name, 0) + 1
                            )
                        commits_analyzed += 1
                    except Exception as exc:
                        log.debug("github: diff fetch failed %s@%s: %s", repo_full, sha[:7], exc)
            except Exception as exc:
                log.debug("github: commits list failed for %s: %s", repo_full, exc)

        log.info("github: analyzed %d commits across %d repos", commits_analyzed, len(recent_repos_ordered[:5]))

        # ── 4. Language bytes fallback (top 5 recently-pushed repos) ──────────
        lang_bytes: dict[str, int] = {}
        for repo in repos[:5]:
            if repo.get("fork"):
                continue
            try:
                lr = await client.get(repo["languages_url"])
                if lr.status_code == 200:
                    for lang, nb in lr.json().items():
                        lang_bytes[lang] = lang_bytes.get(lang, 0) + nb
            except Exception:
                pass

    # ── Build skill list ───────────────────────────────────────────────────────
    skills: dict[str, dict] = {}

    # Layer 1: commit-derived skills (highest confidence)
    for skill_name, count in commit_skill_counts.items():
        proficiency, years = _proficiency(count)
        skills[skill_name] = {
            "name": skill_name,
            "category": commit_skill_meta.get(skill_name, "language"),
            "proficiency": proficiency,
            "years": years,
            "confidence": Decimal("0.85"),
            "evidence": (
                f"Actively coded in {count} commit{'s' if count != 1 else ''} "
                f"in the last 90 days"
            ),
        }

    # Layer 2: topic-derived skills (medium confidence — framework/tool discovery)
    for topic in topic_hits:
        if topic not in _TOPIC_TO_SKILL:
            continue
        skill_name, category = _TOPIC_TO_SKILL[topic]
        if skill_name in skills:
            # Upgrade category if topic provides a more specific one
            skills[skill_name]["category"] = category
            continue
        skills[skill_name] = {
            "name": skill_name,
            "category": category,
            "proficiency": "novice",
            "years": Decimal("0.5"),
            "confidence": Decimal("0.60"),
            "evidence": "Found in GitHub repo topics",
        }

    # Layer 3: language bytes fallback (lower confidence — historical baseline)
    _lang_map = {
        "Python": "Python", "JavaScript": "JavaScript", "TypeScript": "TypeScript",
        "Java": "Java", "Go": "Go", "Rust": "Rust", "C++": "C++", "C#": "C#",
        "Ruby": "Ruby", "PHP": "PHP", "Swift": "Swift", "Kotlin": "Kotlin",
        "Scala": "Scala", "Shell": "Bash", "HCL": "Terraform", "Dockerfile": "Docker",
        "Dart": "Flutter", "Vue": "Vue.js", "Jupyter Notebook": "Python", "R": "R",
    }
    for lang, nbytes in lang_bytes.items():
        skill_name = _lang_map.get(lang, lang)
        if skill_name in skills:
            continue  # already covered by commits or topics
        if nbytes > 500_000:
            proficiency, years = "expert", Decimal("3.0")
        elif nbytes > 100_000:
            proficiency, years = "intermediate", Decimal("1.5")
        else:
            proficiency, years = "novice", Decimal("0.5")
        skills[skill_name] = {
            "name": skill_name,
            "category": "language",
            "proficiency": proficiency,
            "years": years,
            "confidence": Decimal("0.55"),
            "evidence": f"{nbytes:,} bytes in recently-pushed repos (historical)",
        }

    # Sort: commit-derived first (conf 0.85), then topics (0.60), then bytes (0.55)
    # Within each tier: expert > intermediate > novice
    ordered = sorted(
        skills.values(),
        key=lambda s: (
            -float(s["confidence"]),
            {"expert": 0, "intermediate": 1, "novice": 2}[s["proficiency"]],
        ),
    )

    log.info(
        "github: %s — %d skills (commits:%d, topics:%d, bytes:%d)",
        github_username,
        len(ordered),
        sum(1 for s in ordered if float(s["confidence"]) >= 0.85),
        sum(1 for s in ordered if float(s["confidence"]) == 0.60),
        sum(1 for s in ordered if float(s["confidence"]) <= 0.55),
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
