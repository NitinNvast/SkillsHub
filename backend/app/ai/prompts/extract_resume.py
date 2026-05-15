"""
Extraction prompt + tool schema for Claude Sonnet.

Design goals:
  - Precise proficiency rules → reproducible novice/intermediate/expert labels
  - Evidence extraction → every skill has a quoted source from the resume
  - Confidence scoring → flags uncertain extractions for human review
  - Canonical name mapping → reduces normalization work post-extraction
  - Prompt caching → system block is marked cache_control=ephemeral
"""
from __future__ import annotations

# ─── Tool schema ─────────────────────────────────────────────────────────────
# Claude will "call" this tool with the extracted profile as its arguments.
# tool_use forces structured output — no free-text wrapping, no partial JSON.

EXTRACT_PROFILE_TOOL: dict = {
    "name": "extract_profile",
    "description": (
        "Extract a complete structured professional profile from a resume or LinkedIn export. "
        "Call this tool exactly once with all extracted information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name"},
            "email": {"type": "string"},
            "location": {"type": "string", "description": "City, Country or similar"},
            "title": {"type": "string", "description": "Current or most recent job title"},
            "total_years_exp": {
                "type": "number",
                "description": "Best estimate of total professional years. Infer from career start date if not explicit."
            },
            "summary": {
                "type": "string",
                "description": "2–3 sentence professional summary written in third person."
            },
            "skills": {
                "type": "array",
                "description": "Every distinct technical skill mentioned or clearly implied. One entry per skill.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Canonical skill name. Map variants: 'JS'→'JavaScript', 'ReactJS'→'React', etc."
                        },
                        "proficiency": {
                            "type": "string",
                            "enum": ["novice", "intermediate", "expert"],
                            "description": (
                                "Use these rules strictly:\n"
                                "  expert: 4+ years OR led/architected/principal/senior mention OR built production systems at scale\n"
                                "  intermediate: 1.5–4 years OR 'experience with' OR worked on real projects\n"
                                "  novice: <1.5 years OR 'familiar with' / 'learning' / 'exposure to' / side-project only"
                            )
                        },
                        "years": {
                            "type": "number",
                            "description": "Years of experience. Estimate from dates if not stated."
                        },
                        "evidence": {
                            "type": "string",
                            "description": (
                                "Verbatim or close-paraphrase from the resume that justifies this skill and proficiency. "
                                "Keep it to 1–2 sentences."
                            )
                        },
                        "confidence": {
                            "type": "number",
                            "description": (
                                "0.0–1.0. Use 0.95 if explicitly stated with years. "
                                "0.80 if clearly present but years unstated. "
                                "0.65 if inferred from project context."
                            )
                        }
                    },
                    "required": ["name", "proficiency", "confidence"]
                }
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
                            "description": "2–4 sentences: what was built, technologies used, scale/impact."
                        },
                        "start_date": {"type": "string", "description": "YYYY-MM or YYYY"},
                        "end_date": {"type": "string", "description": "YYYY-MM, YYYY, or null if current"},
                        "technologies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Technologies explicitly mentioned for this project."
                        }
                    },
                    "required": ["name", "description", "technologies"]
                }
            },
            "certifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "issuer": {"type": "string"},
                        "year": {"type": "integer"}
                    },
                    "required": ["name"]
                }
            }
        },
        "required": ["name", "skills", "projects", "certifications"]
    }
}

# ─── System prompt ────────────────────────────────────────────────────────────
# Marked for prompt caching — this block is large and static.
# The canonical skill list is injected at call time via build_system_prompt().

_SYSTEM_BASE = """\
You are a senior technical recruiter and software engineer. Your task is to extract \
a complete, accurate structured profile from a developer resume or LinkedIn export.

## IMPORTANT RULES

1. **Extract every skill** — languages, frameworks, platforms, tools, and domain expertise.
   Do not omit skills just because they appear only in project descriptions.

2. **Proficiency is determined by evidence, not by what the candidate claims.** Follow the \
   explicit rules in the tool schema — do not use "expert" unless there are 4+ years or a \
   clear senior/lead/architect signal.

3. **Evidence is mandatory for confidence ≥ 0.80.** Quote or closely paraphrase the part of \
   the resume that proves each skill. This is shown to HR during review.

4. **Canonical skill names** — normalize to common spellings:
   JavaScript (not JS/Javascript), TypeScript (not TS), React (not ReactJS/React.js),
   Next.js (not NextJS), Node.js (not NodeJS), PostgreSQL (not Postgres), etc.

5. **Total years** — calculate from the earliest job start date to today. If dates are absent,
   infer from the level of seniority described.

6. **Projects** — extract each role/job as a project. Include client projects, side projects,
   and open source contributions if mentioned.

7. **Do not hallucinate.** If information is absent, omit it or set it to null. Never invent
   skills, projects, or certifications.

8. **Confidence calibration:**
   - 0.95 — explicitly stated with year count ("5 years of React")
   - 0.85 — clearly present, used on multiple projects, no year count
   - 0.70 — mentioned once, context is thin
   - 0.55 — inferred from adjacent technology (do not use this for primary extraction — \
     reserve for the inference step)

Call the `extract_profile` tool exactly once with the complete extracted profile.\
"""


def build_system_prompt(canonical_skills: list[str] | None = None) -> list[dict]:
    """
    Returns the messages-API system block with prompt caching enabled.
    Injecting canonical_skills into the system prompt improves normalization
    without inflating every user message.
    """
    content = _SYSTEM_BASE
    if canonical_skills:
        skill_list = ", ".join(canonical_skills[:120])  # cap at 120 to keep tokens reasonable
        content += f"\n\n## Canonical Skill Names (normalize to these where possible)\n{skill_list}"

    return [
        {
            "type": "text",
            "text": content,
            # Prompt caching — this large static block is cached after the first call.
            # Saves ~80% of input tokens on repeated extractions during the demo.
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_user_message(raw_text: str) -> str:
    return (
        f"Please extract the structured profile from the following resume:\n\n"
        f"---\n{raw_text[:12000]}\n---\n\n"  # cap at 12k chars (~3k tokens) — ample for any resume
        f"Call the extract_profile tool with the complete extracted data."
    )
