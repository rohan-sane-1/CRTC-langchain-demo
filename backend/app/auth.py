import uuid

from fastapi import Depends, HTTPException, Request, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import User

COOKIE_NAME = "crtc_session"
SESSION_MAX_AGE = 7 * 24 * 3600  # 7 days

_google_request = google_requests.Request()


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="crtc-session")


def verify_google_credential(credential: str) -> dict:
    """Verify a Google ID token (signature, expiry, audience, issuer). Blocking: call in a thread.

    verify_oauth2_token checks `aud` against our client ID and `iss` against Google's issuers.
    """
    claims = google_id_token.verify_oauth2_token(
        credential, _google_request, get_settings().google_client_id
    )
    if not claims.get("email_verified"):
        raise ValueError("Email not verified")
    return claims


def set_session_cookie(response: Response, user_id: uuid.UUID) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _serializer().dumps(str(user_id)),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=get_settings().cookie_secure,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def read_session_user_id(request: Request) -> uuid.UUID | None:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        return uuid.UUID(_serializer().loads(raw, max_age=SESSION_MAX_AGE))
    except (BadSignature, ValueError):
        return None


async def current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    user_id = read_session_user_id(request)
    user = await session.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def check_origin(request: Request) -> None:
    """CSRF defence for mutating routes (on top of SameSite=Lax): Origin must be our frontend."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if request.headers.get("origin") != get_settings().frontend_origin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bad origin")
