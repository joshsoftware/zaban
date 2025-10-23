import os
import hmac
import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.api_key import ApiKey


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_key(raw_key: str) -> str:
    # Use an application-level secret to HMAC the raw key before storing
    pepper = os.getenv("API_KEY_PEPPER", "")
    return hmac.new(pepper.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Generate a raw API key and its hash for storage.

    Returns (raw_key, key_hash)
    """
    # Generate key with "sk-" prefix
    random_part = secrets.token_urlsafe(48)
    raw = f"sk-{random_part}"
    return raw, _hash_key(raw)


def verify_api_key(db: Session, presented_key: str) -> Optional[ApiKey]:
    if not presented_key:
        return None
    hashed = _hash_key(presented_key)
    record: Optional[ApiKey] = db.query(ApiKey).filter(ApiKey.key_hash == hashed, ApiKey.is_active == True).first()
    return record


async def require_api_key(x_api_key: Optional[str] = Depends(API_KEY_HEADER), db: Session = Depends(get_db)) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key header missing")
    record = verify_api_key(db, x_api_key)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")
    return record



