import os
from typing import Dict, Any
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv


class GoogleOAuth2Client:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self) -> None:
        # Load env from .env if present (aligns with taxsage_backend pattern)
        load_dotenv()
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    async def get_access_token(self, code: str, redirect_uri: str) -> str:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.TOKEN_URL, data=data)
        if resp.status_code != 200:
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            raise HTTPException(status_code=400, detail=f"Failed to get access token from Google: {payload}")
        return resp.json().get("access_token")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.USER_INFO_URL, headers=headers)
        if resp.status_code != 200:
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            raise HTTPException(status_code=400, detail=f"Failed to get user info from Google: {payload}")
        info = resp.json()
        return {
            "email": info.get("email"),
            "first_name": info.get("given_name", ""),
            "last_name": info.get("family_name", ""),
            "sso_id": info.get("id"),
            "sso_provider": "google",
        }


google_oauth2_client = GoogleOAuth2Client()


