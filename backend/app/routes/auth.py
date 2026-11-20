from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    clear_session_cookie,
    current_user,
    set_session_cookie,
    verify_google_credential,
)
from app.config import get_settings
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginBody(BaseModel):
    credential: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str | None


def _user_out(user: User) -> UserOut:
    return UserOut(id=str(user.id), email=user.email, name=user.name)


@router.post("/google", response_model=UserOut)
async def google_login(
    body: GoogleLoginBody, response: Response, session: AsyncSession = Depends(get_session)
) -> UserOut:
    try:
        claims = await run_in_threadpool(verify_google_credential, body.credential)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google credential")

    email = claims["email"].lower()
    allowed = get_settings().allowed_email_set
    if allowed and email not in allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not allowed")

    user = await session.scalar(select(User).where(User.google_sub == claims["sub"]))
    if user is None:
        user = User(google_sub=claims["sub"], email=email, name=claims.get("name"))
        session.add(user)
    else:
        user.email = email
        user.name = claims.get("name")
    await session.commit()

    set_session_cookie(response, user.id)
    return _user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return _user_out(user)
