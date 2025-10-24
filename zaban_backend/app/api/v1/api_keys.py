from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from ...db.database import get_db
from ...core.api_key_auth import generate_api_key
from ...models.api_key import ApiKey
from ...models.user import User
from ...core.security import verify_token


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateApiKeyRequest(BaseModel):
    name: Optional[str] = None


class CreateApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    secret_key: str  # raw key returned once


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    is_active: bool
    created_at: str
    revoked_at: Optional[str] = None
    secret_key_prefix: str = "sk-***"  # Show prefix format without exposing actual key


class ApiKeyListResponse(BaseModel):
    api_keys: list[ApiKeyResponse]
    total: int


def _get_current_subject(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    sub = verify_token(token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    return sub


def _get_or_create_user(db: Session, email: str) -> User:
    user: User | None = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, first_name=None, last_name=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("", response_model=CreateApiKeyResponse)
def create_api_key(payload: CreateApiKeyRequest, db: Session = Depends(get_db), subject: str = Depends(_get_current_subject)):
    user = _get_or_create_user(db, subject)
    raw, key_hash = generate_api_key()
    record = ApiKey(user_id=user.id, name=payload.name, key_hash=key_hash, is_active=True)
    db.add(record)
    db.commit()
    db.refresh(record)
    return CreateApiKeyResponse(id=record.id, name=record.name, secret_key=raw)


@router.get("", response_model=ApiKeyListResponse)
def list_api_keys(db: Session = Depends(get_db), subject: str = Depends(_get_current_subject)):
    """List all API keys for the current user"""
    user = _get_or_create_user(db, subject)
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc()).all()
    
    api_keys = []
    for key in keys:
        api_keys.append(ApiKeyResponse(
            id=key.id,
            name=key.name,
            is_active=key.is_active,
            created_at=key.created_at.isoformat(),
            revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
            secret_key_prefix="sk-***"
        ))
    
    return ApiKeyListResponse(api_keys=api_keys, total=len(api_keys))


@router.get("/{key_id}", response_model=ApiKeyResponse)
def get_api_key(key_id: uuid.UUID, db: Session = Depends(get_db), subject: str = Depends(_get_current_subject)):
    """Get details of a specific API key"""
    user = _get_or_create_user(db, subject)
    key: ApiKey | None = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == user.id)
        .first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        is_active=key.is_active,
        created_at=key.created_at.isoformat(),
        revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
        secret_key_prefix="sk-***"
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(key_id: uuid.UUID, db: Session = Depends(get_db), subject: str = Depends(_get_current_subject)):
    """Delete (deactivate) an API key"""
    # Ensure the key belongs to the current user
    user = _get_or_create_user(db, subject)
    key: ApiKey | None = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == user.id)
        .first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    if not key.is_active:
        return  # already inactive
    key.is_active = False
    db.add(key)
    db.commit()
    return



