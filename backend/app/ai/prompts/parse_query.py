"""Query parsing prompt (provider-neutral).

Goal: extract structured constraints from a free-form HR query so we can:
  1. Apply hard filters in SQL (location, availability, min skill years)
  2. Embed a cleaner semantic_text (without filter noise) for cosine search
  3. Show the parsed intent in the UI ("Searching for: senior React engineer in Pune")

Routed through the "parsing" task — typically a fast/cheap model (Haiku-class).
"""

from __future__ import annotations

from app.ai.providers import ToolSpec

_PARSE_QUERY_INPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "semantic_text": {
            "type": "string",
            "description": (
                "A clean, embedding-optimised version of the query. "
                "Expand abbreviations, remove location/availability constraints (those are filters), "
                "add relevant synonyms. Keep it 1–3 sentences. "
                "Example: 'experienced React engineer with real-time WebSocket experience capable of leading a team'"
            ),
        },
        "required_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills explicitly required. Use canonical names (React not ReactJS, JavaScript not JS).",
        },
        "min_years_per_skill": {
            "type": "object",
            "additionalProperties": {"type": "number"},
            "description": 'Minimum years required per skill. e.g. {"Java": 3.0}. Only populate when explicitly stated.',
        },
        "location": {
            "type": "string",
            "description": "City or region filter if mentioned. null otherwise.",
        },
        "availability": {
            "type": "array",
            "items": {"type": "string", "enum": ["available", "partial", "allocated"]},
            "description": "Filter by availability. If query mentions 'unallocated' or 'available' → [\"available\"]. If 'haven't been on a project' → [\"available\", \"partial\"].",
        },
        "seniority_hint": {
            "type": "string",
            "description": "Detected seniority signal: 'junior', 'mid', 'senior', 'lead', 'principal'. null if not mentioned.",
        },
    },
    "required": ["semantic_text", "required_skills", "min_years_per_skill", "availability"],
}


PARSE_QUERY_TOOL = ToolSpec(
    name="parse_search_query",
    description=(
        "Parse a natural language HR search query into structured filters and a clean "
        "semantic search text."
    ),
    input_schema=_PARSE_QUERY_INPUT_SCHEMA,
)


PARSE_QUERY_SYSTEM = """\
You are an HR search assistant. Parse the incoming search query into structured components.

Rules:
- semantic_text should be a rich, synonymous restatement of the INTENT — optimised for semantic similarity.
  Add related terms: "WebSocket" → "real-time systems, socket programming, live data"; "lead" → "tech lead, senior, architect"
- required_skills: only skills explicitly named in the query. Do not add inferred skills here.
- min_years_per_skill: ONLY populate when the query says "at least N years" or "N+ years".
- availability: leave empty [] unless the query specifically mentions availability/allocation.
- location: null unless a specific city/region is mentioned.
- Be conservative — under-extract filters rather than over-restrict results.

Call parse_search_query once.\
"""


def build_parse_message(query: str) -> str:
    return f'Parse this HR search query:\n\n"{query}"'
