from pydantic import BaseModel
from typing import Optional


class SSOLogin(BaseModel):
    code: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class LogoutResponse(BaseModel):
    detail: str = "Logged out"


