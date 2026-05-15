"""Auth endpoints — JSON-based login (matches the frontend) + /me."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import CurrentUser, SessionDep
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth import authenticate, issue_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login_json(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    user = await authenticate(session, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return TokenResponse(access_token=issue_token(user), user=UserOut.model_validate(user))


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> TokenResponse:
    """Form-encoded login — kept so the Swagger UI Authorize button works."""
    user = await authenticate(session, form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=issue_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
