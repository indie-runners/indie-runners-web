import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class CodeExchangeRefused(Exception):
    """Google would not exchange the code: replayed, expired or bogus (W-094)."""


class GoogleAuthService:
    def build_authorize_url(self) -> str:
        params = httpx.QueryParams({
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        })
        return f"{GOOGLE_AUTHORIZE_URL}?{params}"

    async def exchange_code_for_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(GOOGLE_TOKEN_URL, data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_redirect_uri,
            })
            if response.is_error:
                try:
                    error = response.json().get("error", response.status_code)
                except ValueError:
                    error = response.status_code
                # WARNING, not INFO: INFO never reaches Cloud Logging (W-051). Never the code.
                logger.warning(f"Google refused the code exchange: {error}")
                raise CodeExchangeRefused(str(error))
            return response.json()

    async def get_userinfo(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()
        logger.info("Fetched Google userinfo")
        return data
