import os
from fastapi import APIRouter, HTTPException, status, Header, Depends
from ..schemas.auth import (
    SSOLogin,
    TokenResponse,
    LogoutResponse,
    SignupRequest,
    SignupResponse,
    SigninRequest,
)
from passlib.context import CryptContext
from ..services.google_oauth2 import google_oauth2_client
from ..core.security import create_access_token, verify_token, logout_token
from ..core.api_key_auth import generate_api_key
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.user import User
from ..db.database import get_db


router = APIRouter()

# Password hashing context: prefer Argon2, keep bcrypt as fallback to verify older hashes
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def _domain_allowed(email: str) -> bool:
    allowed_env = os.getenv("ALLOWED_SSO_DOMAINS", "joshsoftware.com")
    if not allowed_env:
        return True
    allowed = [d.strip().lower() for d in allowed_env.split(",") if d.strip()]
    e = email.lower()
    return any(e.endswith(f"@{d}") for d in allowed)


@router.post("/google/login", response_model=TokenResponse)
async def google_login(payload: SSOLogin, db: Session = Depends(get_db)) -> TokenResponse:
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
    # Optionally generate and store an API key for this user here
    # raw_key, key_hash = generate_api_key()
    # Persist ApiKey with user link (requires user table linkage)
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



@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    # Basic validation
    email = payload.email.lower()

    # check existing user using SQLAlchemy select
    existing = db.execute(select(User.id).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already in use")

    try:
        hashed = pwd_context.hash(payload.password)
    except Exception as e:
        # Hashing failed for some reason. Return a generic server error
        # (do not expose algorithm-specific limitations like bcrypt's 72-byte limit).
        raise HTTPException(status_code=500, detail="Password hashing failed") from e

    # Create user via ORM
    user = User(
        email=email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=hashed,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        created_at=user.created_at.isoformat() if user.created_at is not None else None,
    )



@router.post("/signin", response_model=TokenResponse)
def signin(payload: SigninRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Sign in with email and password. Returns a JWT access token on success."""
    email = payload.email.lower()

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not getattr(user, "hashed_password", None):
        # Do not reveal whether the account exists
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        valid = pwd_context.verify(payload.password, user.hashed_password)
    except Exception:   
        raise HTTPException(status_code=500, detail="Password verification failed")

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token(subject=email)
    return TokenResponse(access_token=token, token_type="bearer")


