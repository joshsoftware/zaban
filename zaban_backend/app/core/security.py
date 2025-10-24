import os
import time
import jwt
from typing import Optional


JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "30"))

# ⚠️  WARNING: In-memory token denylist - NOT SUITABLE FOR PRODUCTION! ⚠️
# TODO: Replace with Redis or database storage before production deployment
# This implementation will not persist across server restarts and won't work in multi-instance deployments
_denylist: set[str] = set()


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    exp_minutes = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRES_MIN
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + exp_minutes * 60}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token


def verify_token(token: str) -> Optional[str]:
    # ⚠️  WARNING: Using in-memory denylist - replace with Redis/DB for production
    if token in _denylist:
        return None
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return str(data.get("sub")) if data.get("sub") is not None else None
    except jwt.PyJWTError:
        return None


def logout_token(token: str) -> None:
    # ⚠️  WARNING: Using in-memory denylist - replace with Redis/DB for production
    _denylist.add(token)


