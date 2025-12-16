from pydantic import BaseModel
from typing import Optional
from pydantic import EmailStr


class SSOLogin(BaseModel):
    code: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class LogoutResponse(BaseModel):
    detail: str = "Logged out"


class SignupRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: Optional[str]


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "If an account exists with this email, a password reset link has been sent."


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str = "Password has been reset successfully"


