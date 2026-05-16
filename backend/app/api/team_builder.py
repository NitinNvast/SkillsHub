"""Team builder endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from app.ai.pipelines.team_builder import run_team_builder
from app.ai.providers.base import ProviderError, RateLimitError
from app.core.deps import SessionDep, require_hr
from app.schemas.team_builder import (
    TeamBuilderRequest,
    TeamBuilderResponse,
    TeamMemberProposal,
    TeamProposal,
)

router = APIRouter()


@router.post("", response_model=TeamBuilderResponse, dependencies=[Depends(require_hr)])
async def build_team(payload: TeamBuilderRequest, session: SessionDep) -> TeamBuilderResponse:
    """AI-powered team composition for a project description."""
    try:
        raw = await run_team_builder(
            session, payload.description, payload.team_size, payload.duration_weeks
        )
    except RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=f"AI provider rate limited — please wait a moment. ({exc})",
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"AI provider unavailable: {exc}") from exc

    proposal_raw = raw["proposal"]
    team = [TeamMemberProposal(**m) for m in proposal_raw["team"]]
    alternatives = [TeamMemberProposal(**m) for m in proposal_raw.get("alternatives", [])]
    proposal = TeamProposal(
        team=team,
        team_rationale=proposal_raw["team_rationale"],
        gaps=proposal_raw.get("gaps", []),
        alternatives=alternatives,
    )
    return TeamBuilderResponse(
        description=raw["description"],
        proposal=proposal,
        total_candidates_considered=raw["total_candidates_considered"],
    )
