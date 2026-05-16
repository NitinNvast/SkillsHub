"""Skill inference pipeline — two-stage approach.

Stage 1 — Deterministic rules (free, instant):
  Hard-coded parent/sibling relationships that are always true.
  e.g. Next.js → React (0.97), React → JavaScript (0.88).

Stage 2 — LLM call (fast, cheap):
  Context-aware domain inferences rules can't capture.
  e.g. Stripe + Node.js + payment project → "Payment Integration" domain.
  Routed through task='inference' — defaults to a fast Haiku-class model
  but is fully provider-agnostic (any chat provider works).

Both stages skip skills already in the extracted set.
Results are tagged source='inferred' with confidence scores and reasoning.
"""

from __future__ import annotations

import logging

from app.schemas.extraction import ExtractedSkill

log = logging.getLogger(__name__)


# ─── Stage 1: Deterministic rules ─────────────────────────────────────────────
# Format: trigger_skill_lower → [(inferred_name, confidence, proficiency_rule, years_fraction)]
# proficiency_rule: "same" | "one_below" | "novice" | "intermediate"
# years_fraction: multiplier applied to trigger skill's years

_RULES: list[tuple[str, str, float, str, float]] = [
    # (trigger_lower, inferred_name, confidence, proficiency_rule, years_fraction)
    # JavaScript ecosystem
    ("next.js", "React", 0.97, "same", 1.0),
    ("next.js", "JavaScript", 0.90, "same", 1.0),
    ("next.js", "TypeScript", 0.72, "one_below", 0.7),
    ("react native", "React", 0.95, "same", 1.0),
    ("react native", "JavaScript", 0.90, "same", 1.0),
    ("react native", "Mobile Development", 0.88, "same", 1.0),
    ("react", "JavaScript", 0.88, "same", 1.0),
    ("vue.js", "JavaScript", 0.92, "same", 1.0),
    ("angular", "TypeScript", 0.92, "same", 1.0),
    ("angular", "JavaScript", 0.85, "same", 1.0),
    ("svelte", "JavaScript", 0.90, "same", 1.0),
    ("typescript", "JavaScript", 0.92, "same", 1.0),
    ("nestjs", "Node.js", 0.95, "same", 1.0),
    ("nestjs", "TypeScript", 0.88, "same", 1.0),
    ("express.js", "Node.js", 0.95, "same", 1.0),
    ("express.js", "JavaScript", 0.90, "same", 1.0),
    ("node.js", "JavaScript", 0.92, "same", 1.0),
    # Python ecosystem
    ("django", "Python", 0.97, "same", 1.0),
    ("flask", "Python", 0.97, "same", 1.0),
    ("fastapi", "Python", 0.97, "same", 1.0),
    ("tensorflow", "Python", 0.90, "same", 1.0),
    ("tensorflow", "Machine Learning", 0.85, "same", 1.0),
    ("pytorch", "Python", 0.90, "same", 1.0),
    ("pytorch", "Machine Learning", 0.85, "same", 1.0),
    ("langchain", "Python", 0.85, "same", 1.0),
    ("langchain", "LLM Engineering", 0.82, "same", 1.0),
    # JVM
    ("spring boot", "Java", 0.97, "same", 1.0),
    ("spring boot", "Backend Development", 0.82, "same", 1.0),
    # Ruby
    ("ruby on rails", "Ruby", 0.97, "same", 1.0),
    # AWS sub-services → AWS
    ("aws lambda", "AWS", 0.92, "same", 1.0),
    ("aws s3", "AWS", 0.92, "same", 1.0),
    ("aws ec2", "AWS", 0.92, "same", 1.0),
    # Databases → SQL
    ("postgresql", "SQL", 0.90, "same", 0.9),
    ("mysql", "SQL", 0.90, "same", 0.9),
    # Container orchestration
    ("kubernetes", "Docker", 0.85, "one_below", 0.8),
    # Socket.IO → domain
    ("socket.io", "Real-time Systems", 0.88, "same", 1.0),
    ("socket.io", "WebSocket", 0.90, "same", 1.0),
    ("websocket", "Real-time Systems", 0.85, "same", 1.0),
]


def _apply_proficiency_rule(trigger_prof: str, rule: str) -> str:
    order = ["novice", "intermediate", "expert"]
    if rule == "same":
        return trigger_prof
    if rule == "one_below":
        idx = order.index(trigger_prof) if trigger_prof in order else 1
        return order[max(0, idx - 1)]
    return rule  # "novice" or "intermediate" literal


def _deterministic_inferences(extracted: list[ExtractedSkill]) -> list[dict]:
    extracted_lower = {s.name.lower() for s in extracted}
    inferred_names_lower: set[str] = set()
    results: list[dict] = []

    for skill in extracted:
        trigger = skill.name.lower()
        for trig, inferred_name, confidence, prof_rule, years_frac in _RULES:
            if trig != trigger:
                continue
            if inferred_name.lower() in extracted_lower:
                continue
            if inferred_name.lower() in inferred_names_lower:
                continue

            years = round(float(skill.years) * years_frac, 1) if skill.years else None
            proficiency = _apply_proficiency_rule(skill.proficiency, prof_rule)
            inferred_names_lower.add(inferred_name.lower())

            results.append(
                {
                    "name": inferred_name,
                    "proficiency": proficiency,
                    "years": years,
                    "confidence": confidence,
                    "reasoning": f"Implied by {skill.name} ({skill.proficiency})",
                    "triggered_by": skill.name,
                }
            )

    return results


# ─── Stage 2: Groq llama-3.1-8b-instant ──────────────────────────────────────


async def _llm_inferences(
    extracted: list[ExtractedSkill],
    already_inferred_names: set[str],
) -> list[dict]:
    """Run the configured inference model to catch domain/contextual inferences
    that deterministic rules miss. Routed via task='inference'."""
    from app.ai.prompts.infer_skills import (
        INFER_SKILLS_TOOL,
        INFER_SYSTEM_PROMPT,
        build_infer_message,
    )
    from app.ai.providers import ChatRequest, ai_manager

    if len(extracted) < 2:
        return []

    already = {s.name.lower() for s in extracted} | {n.lower() for n in already_inferred_names}

    user_msg = build_infer_message(
        [{"name": s.name, "proficiency": s.proficiency, "years": s.years} for s in extracted],
        already,
    )

    request = ChatRequest(
        system=INFER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
        tools=[INFER_SKILLS_TOOL],
        tool_choice="any",
        max_tokens=1024,
    )
    resp = await ai_manager.chat(request, task="inference")
    call = resp.first_tool_call()
    if call is None:
        return []
    candidates = call.arguments.get("inferred", []) if isinstance(call.arguments, dict) else []

    # Filter out anything already present
    results = []
    for c in candidates:
        if not c.get("name"):
            continue
        if c["name"].lower() in already:
            continue
        # Confidence floor for Haiku inferences
        c["confidence"] = min(float(c.get("confidence", 0.70)), 0.92)
        results.append(c)

    return results


# ─── Public entry point ───────────────────────────────────────────────────────


async def run_inference(extracted_skills: list[ExtractedSkill]) -> list[dict]:
    """
    Main entry point called by extraction.py.

    Returns a list of inferred skill dicts (same shape as ExtractedSkill but
    with 'reasoning' and 'triggered_by' extras) for persistence.
    """
    if not extracted_skills:
        return []

    # Stage 1: free, deterministic
    stage1 = _deterministic_inferences(extracted_skills)
    log.info("Inference stage 1: %d rules-based inferences", len(stage1))

    # Stage 2: LLM call (routed via task='inference')
    already_from_stage1 = {r["name"].lower() for r in stage1}
    try:
        stage2 = await _llm_inferences(extracted_skills, already_from_stage1)
        log.info("Inference stage 2: %d LLM inferences", len(stage2))
    except Exception as exc:
        log.warning("LLM inference failed, using rules-only: %s", exc)
        stage2 = []

    all_inferred = stage1 + stage2

    # Final dedup by name (keep highest confidence)
    seen: dict[str, dict] = {}
    for inf in all_inferred:
        key = inf["name"].lower()
        if key not in seen or inf["confidence"] > seen[key]["confidence"]:
            seen[key] = inf

    result = list(seen.values())
    log.info("Inference total: %d inferred skills for this profile", len(result))
    return result
