"""Inference prompt (provider-neutral).

Purpose: given a developer's explicitly extracted skills, infer related skills
they almost certainly have but didn't mention on their resume.

This is the "bonus" the problem statement calls out explicitly:
  "someone with 4 years of Next.js clearly knows React"

Two-stage approach:
  1. Deterministic rules (free, instant) — canonical parent/sibling relationships
  2. LLM call — context-aware domain inferences that rules can't capture

The LLM call is short and cheap — defaults to a fast model (Haiku) but is
routed through the inference task (LLM_PROVIDER / INFERENCE_MODEL).
"""

from __future__ import annotations

from app.ai.providers import ToolSpec

_INFER_SKILLS_INPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "inferred": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The inferred skill name (use canonical spelling)",
                    },
                    "proficiency": {
                        "type": "string",
                        "enum": ["novice", "intermediate", "expert"],
                        "description": "One level below the triggering skill's proficiency unless clearly warranted",
                    },
                    "years": {
                        "type": "number",
                        "description": "Conservative estimate; usually same as or less than the triggering skill",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "0.0–1.0. Max 0.95 for inferred skills. Use 0.60–0.80 for domain inferences.",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "One sentence: why this skill is implied, referencing the triggering skill(s)",
                    },
                    "triggered_by": {
                        "type": "string",
                        "description": "The extracted skill(s) that imply this one",
                    },
                },
                "required": ["name", "proficiency", "confidence", "reasoning", "triggered_by"],
            },
        }
    },
    "required": ["inferred"],
}


INFER_SKILLS_TOOL = ToolSpec(
    name="infer_skills",
    description=(
        "Given a list of explicitly extracted skills, infer additional skills the developer "
        "almost certainly possesses but did not mention. Only infer with high confidence."
    ),
    input_schema=_INFER_SKILLS_INPUT_SCHEMA,
)


INFER_SYSTEM_PROMPT = """\
You are a senior engineering hiring manager who deeply understands technology relationships.

Your task: given a developer's extracted skill list, identify skills they almost certainly have
but didn't explicitly mention.

## Rules

1. **Only infer skills with high confidence.** If in doubt, omit.
2. **Never re-infer a skill already in the extracted list** (even if spelled differently).
3. **Focus on parent/ecosystem skills** implied by specific ones:
   - Framework → its primary language (Next.js → React → JavaScript)
   - Platform-specific → general platform (AWS Lambda → AWS, AWS S3 → AWS)
   - ORM → underlying DB (Prisma → PostgreSQL is plausible but lower confidence)
4. **Infer domain expertise** when multiple related skills converge:
   - React + Socket.IO + real-time project → "Real-time Systems" domain
   - Stripe/Razorpay/payment project → "Payment Integration" domain
   - 3+ ML frameworks → "Machine Learning" domain
5. **Do not infer soft skills, management skills, or vague terms** unless the resume
   has explicit seniority markers (Tech Lead title → "Team Leadership").
6. **Confidence caps:**
   - Deterministic parent skill (Next.js → React): up to 0.95
   - Domain inference from convergent signals: 0.65–0.80
   - Speculative leap: do not include

Call the `infer_skills` tool once with all your inferences. Return an empty list if nothing qualifies.\
"""

INFER_USER_TEMPLATE = """\
Extracted skills from this developer's resume:

{skill_list}

Infer any additional skills they almost certainly have but didn't mention.
Do NOT include: {already_extracted_lower}
"""


def build_infer_message(
    extracted_skills: list[dict],
    already_extracted_names: set[str],
) -> str:
    lines = []
    for s in extracted_skills:
        line = f"  • {s['name']} — {s['proficiency']}"
        if s.get("years"):
            line += f" ({s['years']} yrs)"
        lines.append(line)

    skill_list = "\n".join(lines) if lines else "  (none)"
    already = ", ".join(sorted(already_extracted_names)[:40])  # cap to keep prompt short
    return INFER_USER_TEMPLATE.format(skill_list=skill_list, already_extracted_lower=already)
