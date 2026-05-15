"""Re-rank + reasoning prompt — Claude Sonnet scores and explains each candidate.

This is the demo money-shot. The reasoning string is what judges will read and
what makes the product feel genuinely intelligent vs. a keyword search.

Design requirements:
  - Specific: cite actual years, project names, and technologies from the profile
  - Honest: acknowledge gaps, not just strengths
  - Varied: each reasoning is unique to that candidate
  - Scored: 0–100 with principled deductions for gaps
  - Fast: single API call for all candidates (batched)
"""

RERANK_TOOL: dict = {
    "name": "rank_candidates",
    "description": "Rank and explain a list of candidate profiles against an HR search query.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ranked": {
                "type": "array",
                "description": "Candidates in descending order of match quality.",
                "items": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "Exactly as provided in input — do not modify."
                        },
                        "match_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                            "description": (
                                "Score 0–100. Start at 100, deduct:\n"
                                "  -15  per explicitly required skill that's missing\n"
                                "  -10  if years requirement not met\n"
                                "  -8   if seniority is lower than requested\n"
                                "  -5   if location doesn't match\n"
                                "  -5   if currently allocated when availability was required\n"
                                "  +0–5 bonus for exceptional relevant experience beyond the ask"
                            )
                        },
                        "reasoning": {
                            "type": "string",
                            "description": (
                                "1–2 sentences. Must be specific to this candidate — cite years, project names, "
                                "or technologies from their profile. Format: 'Strong match: [specific evidence]. [one gap or bonus if applicable].'"
                                "\nExample: 'Expert in React (5 yrs), led 2 real-time apps using Socket.IO — "
                                "exactly what this role needs. Currently unallocated and available immediately.'"
                            )
                        },
                        "strengths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "2–4 bullet points of specific matching evidence. Be concrete."
                        },
                        "gaps": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "0–3 specific gaps or caveats. Empty array if no meaningful gaps."
                        }
                    },
                    "required": ["employee_id", "match_score", "reasoning", "strengths", "gaps"]
                }
            }
        },
        "required": ["ranked"]
    }
}

RERANK_SYSTEM = """\
You are a senior technical recruiter evaluating candidates for an HR search.

Your output will be shown directly to the HR team — it must be:
  - Accurate: base every claim on what the profile actually says
  - Specific: mention real skills, years, project names, companies from the profile
  - Honest: if a required skill is missing, say so in gaps
  - Varied: each candidate's reasoning must be unique and personal to them

Scoring rules are in the tool schema. Apply them consistently.

The HR team values quality over flattery. A 65% match with honest gaps is
more useful than a 95% match that glosses over missing requirements.

Call rank_candidates once with ALL candidates ranked.\
"""


def build_rerank_message(query: str, candidates: list[dict]) -> str:
    """
    Builds the user message with:
    - The original HR query
    - All candidate summaries (numbered for easy reference)
    """
    lines = [
        f'HR Search Query: "{query}"',
        "",
        "Candidate Profiles:",
        "",
    ]
    for i, c in enumerate(candidates, 1):
        lines.append(f"--- Candidate {i} (ID: {c['employee_id']}) ---")
        lines.append(c["summary_text"])
        lines.append("")

    lines.append(
        "Rank these candidates against the query. "
        "Call rank_candidates with all of them in ranked order."
    )
    return "\n".join(lines)
