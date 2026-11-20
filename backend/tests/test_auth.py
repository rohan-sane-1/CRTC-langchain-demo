import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app import auth
from app.main import app

ORIGIN = {"Origin": "http://localhost:3000"}


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health(client):
    assert (await client.get("/health")).json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/chats", "/auth/me", f"/chats/{uuid.uuid4()}"])
async def test_no_cookie_is_401(client, path):
    assert (await client.get(path)).status_code == 401


async def test_tampered_cookie_is_401(client):
    client.cookies.set(auth.COOKIE_NAME, "garbage")
    assert (await client.get("/chats")).status_code == 401


async def test_post_without_matching_origin_is_403(client):
    assert (await client.post("/chats")).status_code == 403
    r = await client.post("/chats", headers={"Origin": "http://evil.example"})
    assert r.status_code == 403


async def test_post_chats_without_cookie_is_401(client):
    assert (await client.post("/chats", headers=ORIGIN)).status_code == 401


async def test_bad_google_credential_is_401(client):
    r = await client.post("/auth/google", json={"credential": "nope"}, headers=ORIGIN)
    assert r.status_code == 401


async def test_email_not_on_allowlist_is_403(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.verify_google_credential",
        lambda _: {"sub": "123", "email": "stranger@example.com", "name": "X"},
    )
    r = await client.post("/auth/google", json={"credential": "ok"}, headers=ORIGIN)
    assert r.status_code == 403


def test_session_cookie_roundtrip():
    uid = uuid.uuid4()
    token = auth._serializer().dumps(str(uid))
    assert uuid.UUID(auth._serializer().loads(token)) == uid
