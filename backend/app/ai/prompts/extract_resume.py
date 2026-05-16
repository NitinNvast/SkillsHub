"""
Extraction prompt + tool schema (provider-neutral).

Design goals:
  - Precise proficiency rules → reproducible novice/intermediate/expert labels
  - Evidence extraction → every skill has a quoted source from the resume
  - Confidence scoring → flags uncertain extractions for human review
  - Canonical name mapping → reduces normalization work post-extraction
  - Prompt caching → enabled via ChatRequest.cache_system_prompt; providers
    that don't support caching (OpenAI/Groq/Gemini) silently ignore the hint.
"""

from __future__ import annotations

from app.ai.providers import ToolSpec

# ─── Tool schema ─────────────────────────────────────────────────────────────
# The model "calls" this tool with the extracted profile as its arguments.
# Tool-use forces structured output — no free-text wrapping, no partial JSON.

_EXTRACT_PROFILE_INPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Full name"},
        "email": {"type": "string"},
        "location": {"type": "string", "description": "City, Country or similar"},
        "title": {"type": "string", "description": "Current or most recent job title"},
        "total_years_exp": {
            "type": "number",
            "description": "Best estimate of total professional years. Infer from career start date if not explicit.",
        },
        "summary": {
            "type": "string",
            "description": "2–3 sentence professional summary written in third person.",
        },
        "skills": {
            "type": "array",
            "description": "Every distinct technical skill mentioned or clearly implied. One entry per skill.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Canonical skill name. Map variants: 'JS'→'JavaScript', 'ReactJS'→'React', etc.",
                    },
                    "proficiency": {
                        "type": "string",
                        "enum": ["novice", "intermediate", "expert"],
                        "description": (
                            "Use these rules strictly:\n"
                            "  expert: 4+ years OR led/architected/principal/senior mention OR built production systems at scale\n"
                            "  intermediate: 1.5–4 years OR 'experience with' OR worked on real projects\n"
                            "  novice: <1.5 years OR 'familiar with' / 'learning' / 'exposure to' / side-project only"
                        ),
                    },
                    "years": {
                        "type": "number",
                        "description": "Years of experience. Estimate from dates if not stated.",
                    },
                    "evidence": {
                        "type": "string",
                        "description": (
                            "Verbatim or close-paraphrase from the resume that justifies this skill and proficiency. "
                            "Keep it to 1–2 sentences."
                        ),
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "0.0–1.0. Use 0.95 if explicitly stated with years. "
                            "0.80 if clearly present but years unstated. "
                            "0.65 if inferred from project context."
                        ),
                    },
                },
                "required": ["name", "proficiency", "confidence"],
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "description": {
                        "type": "string",
                        "description": "2–4 sentences: what was built, technologies used, scale/impact.",
                    },
                    "start_date": {"type": "string", "description": "YYYY-MM or YYYY"},
                    "end_date": {
                        "type": "string",
                        "description": "YYYY-MM, YYYY, or null if current",
                    },
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Technologies explicitly mentioned for this project.",
                    },
                },
                "required": ["name", "description", "technologies"],
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "year": {"type": "integer"},
                },
                "required": ["name"],
            },
        },
    },
    "required": ["name", "skills", "projects", "certifications"],
}


EXTRACT_PROFILE_TOOL = ToolSpec(
    name="extract_profile",
    description=(
        "Extract a complete structured professional profile from a resume or LinkedIn export. "
        "Call this tool exactly once with all extracted information."
    ),
    input_schema=_EXTRACT_PROFILE_INPUT_SCHEMA,
)


# ─── System prompt ────────────────────────────────────────────────────────────
# This block is large and static — the manager applies prompt caching when
# the provider supports it (e.g. Anthropic). The canonical skill list is
# injected at call time via build_system_prompt().

_SYSTEM_BASE = """\
You are a senior technical recruiter and software engineer. Your task is to extract \
a complete, accurate structured profile from a developer resume or LinkedIn export.

## INPUT FORMAT

The input may be any of the following — handle each correctly:

- **Traditional resume (PDF text)** — chronological or functional layout with sections like
  Work Experience, Skills, Education, Certifications.
- **LinkedIn profile copy-paste** — text copied directly from a LinkedIn profile page.
  Typical layout: name + headline → About → Experience (job title, company, dates, bullets) →
  Education → Skills (with endorsement counts) → Licenses & Certifications →
  Accomplishments. Ignore UI chrome like "Connect", "Message", "500+ connections",
  "LinkedIn Member since", follower counts, and "Show all X" buttons.
- **LinkedIn PDF export** — LinkedIn's "Save to PDF" output. Sections are well-structured
  but may repeat the name/headline at the top of each page.
- **LinkedIn data export text** — CSV or structured text from LinkedIn's "Get a copy of
  your data" download. Skills appear as a comma-separated list; positions include
  start/end dates in ISO format.

## EXTRACTION RULES

1. **Extract every skill** — languages, frameworks, platforms, tools, and domain expertise.
   Do not omit skills just because they appear only in project descriptions.
   For LinkedIn profiles, the "Skills" section with endorsement counts is a primary source —
   high endorsement counts (50+) are a signal of genuine expertise.

2. **Proficiency is determined by evidence, not by what the candidate claims.** Follow the \
   explicit rules in the tool schema — do not use "expert" unless there are 4+ years or a \
   clear senior/lead/architect signal.

3. **Evidence is mandatory for confidence ≥ 0.80.** Quote or closely paraphrase the part of \
   the resume that proves each skill. This is shown to HR during review.

4. **Canonical skill names** — normalize to common spellings:
   JavaScript (not JS/Javascript), TypeScript (not TS), React (not ReactJS/React.js),
   Next.js (not NextJS), Node.js (not NodeJS), PostgreSQL (not Postgres), etc.

5. **Total years** — calculate from the earliest job start date to today. If dates are absent,
   infer from the level of seniority described. LinkedIn dates like "Jan 2019 – Present" or
   "2019 – 2022 · 3 yrs 2 mos" are authoritative — use them directly.

6. **Projects** — extract each role/job as a project. Use the company + title as the project
   name when a project name is not given. Include side projects and open source if mentioned.

7. **Do not hallucinate.** If information is absent, omit it or set it to null. Never invent
   skills, projects, or certifications. Ignore LinkedIn UI boilerplate.

8. **Confidence calibration:**
   - 0.95 — explicitly stated with year count ("5 years of React") or high endorsements (50+)
   - 0.85 — clearly present, used on multiple projects, or moderate endorsements (10–49)
   - 0.70 — mentioned once, context is thin, or low endorsements (<10)
   - 0.55 — inferred from adjacent technology (reserve for the inference step)

Call the `extract_profile` tool exactly once with the complete extracted profile.\
"""


def build_system_prompt(canonical_skills: list[str] | None = None) -> str:
    """Return the provider-neutral system prompt.

    Injecting canonical_skills here improves normalization without inflating
    every user message. The caller passes `cache_system_prompt=True` on the
    ChatRequest — providers that support prompt caching (Anthropic) cache this
    block; others ignore the hint.
    """
    content = _SYSTEM_BASE
    if canonical_skills:
        skill_list = ", ".join(canonical_skills[:120])  # cap at 120 to keep tokens reasonable
        content += f"\n\n## Canonical Skill Names (normalize to these where possible)\n{skill_list}"
    return content


_LINKEDIN_SIGNALS = (
    "linkedin.com/in/",
    "connections",
    "· 1st",
    "· 2nd",
    "endorsements",
    "licenses & certifications",
    "licenses & certi",
    "show all",
    "top skills",
    "open to work",
)


def _detect_linkedin(text: str) -> bool:
    lower = text.lower()
    return sum(1 for s in _LINKEDIN_SIGNALS if s in lower) >= 2


def build_user_message(raw_text: str) -> str:
    is_linkedin = _detect_linkedin(raw_text)
    source_hint = (
        "LinkedIn profile export"
        if is_linkedin
        else "resume"
    )
    linkedin_note = (
        "\n\nNote: this is a LinkedIn profile copy-paste. "
        "Ignore navigation chrome ('Connect', 'Message', 'Show all N', follower/connection counts). "
        "The Skills section lists skills with endorsement counts — extract all of them. "
        "Each Experience entry maps to a project."
        if is_linkedin
        else ""
    )
    return (
        f"Please extract the structured profile from the following {source_hint}:"
        f"{linkedin_note}\n\n"
        f"---\n{raw_text[:12000]}\n---\n\n"
        f"Call the extract_profile tool with the complete extracted data."
    )
