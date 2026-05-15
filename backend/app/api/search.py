"""Semantic search endpoint — the HR-facing centerpiece."""

from fastapi import APIRouter, Depends, HTTPException

from app.ai.pipelines.search import run_semantic_search
from app.ai.providers.base import ProviderError, RateLimitError
from app.core.deps import SessionDep, require_hr
from app.schemas.search import ParsedQuery, SearchRequest, SearchResponse, SearchResultItem

router = APIRouter()


@router.post("", response_model=SearchResponse, dependencies=[Depends(require_hr)])
async def search(payload: SearchRequest, session: SessionDep) -> SearchResponse:
    """
    Natural-language HR search.

    Accepts a full-sentence query, returns ranked candidates with
    match scores and plain-English reasoning per result.

    Example queries:
      "Who can lead a React project that also needs WebSocket experience?"
      "Find a backend dev in Pune with 3+ years of Java and payment integration."
      "Senior frontend engineers who haven't been on a new project recently."
    """
    try:
        raw = await run_semantic_search(session, payload.query, limit=payload.limit)
    except RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=f"AI provider rate limited — please wait a moment and try again. ({exc})",
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"AI provider unavailable: {exc}") from exc

    parsed = ParsedQuery(
        semantic_text=raw["parsed_query"].get("semantic_text", payload.query),
        required_skills=raw["parsed_query"].get("required_skills", []),
        min_years_per_skill=raw["parsed_query"].get("min_years_per_skill", {}),
        location=raw["parsed_query"].get("location"),
        availability=raw["parsed_query"].get("availability", []),
        seniority_hint=raw["parsed_query"].get("seniority_hint"),
    )

    results = [SearchResultItem(**r) for r in raw["results"]]

    return SearchResponse(
        query=payload.query,
        parsed_query=parsed,
        results=results,
        total_candidates_retrieved=raw["total_candidates_retrieved"],
    )
