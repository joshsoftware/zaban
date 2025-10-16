import os
from fastapi import APIRouter, HTTPException, status, Header, Depends
from ..schemas.auth import SSOLogin, TokenResponse, LogoutResponse
from ..services.google_oauth2 import google_oauth2_client
from ..core.security import create_access_token, verify_token, logout_token


router = APIRouter()


def _domain_allowed(email: str) -> bool:
    allowed_env = os.getenv("ALLOWED_SSO_DOMAINS", "joshsoftware.com")
    if not allowed_env:
        return True
    allowed = [d.strip().lower() for d in allowed_env.split(",") if d.strip()]
    e = email.lower()
    return any(e.endswith(f"@{d}") for d in allowed)


@router.post("/google/login", response_model=TokenResponse)
async def google_login(payload: SSOLogin) -> TokenResponse:
    access_token = await google_oauth2_client.get_access_token(
        payload.code, payload.redirect_uri
    )
    user_info = await google_oauth2_client.get_user_info(access_token)

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google user info missing email")
    if not _domain_allowed(email):
        raise HTTPException(status_code=403, detail="Email domain not allowed for SSO")

    # Issue JWT (in a real app, link/create user in DB and use its id)
    token = create_access_token(subject=email)
    return TokenResponse(access_token=token, token_type="bearer", expires_in=None)


@router.get("/me")
async def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    sub = verify_token(token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    # In a real app, fetch user by id/email
    return {"subject": sub}


@router.post("/logout", response_model=LogoutResponse)
async def logout(authorization: str | None = Header(default=None)) -> LogoutResponse:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    logout_token(token)
    return LogoutResponse(detail="Logged out")


