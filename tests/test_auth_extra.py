import uuid
import asyncio

from app.security.jwt import decode_token
from app.db.base import get_session
from app.db.models import User
from project.tests.conftest import UserWithLogin


def test_register_and_decode_token(test_app):
    r = test_app.post("/api/v1/auth/register", json={"username": "treg", "email": "treg@example.com", "password": "s3cr3t"})
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data and isinstance(data["access_token"], str)
    payload = decode_token(data["access_token"])
    sub = payload.get("sub")
    assert sub is not None

    async def _check():
        async with get_session() as session:
            u = await session.get(User, sub)
            assert u is not None
    asyncio.run(_check())


def test_login_with_username_and_email(test_app, normal_user: UserWithLogin):
    r1 = test_app.post("/api/v1/auth/login", json={"username": normal_user[0].username, "password": "userpw"})
    assert r1.status_code == 200
    r2 = test_app.post("/api/v1/auth/login", json={"username": normal_user[0].email, "password": "userpw"})
    assert r2.status_code == 200

    payload = decode_token(r1.json()["access_token"])
    assert payload.get("sub") == normal_user[0].id


def test_password_pepper_effect(monkeypatch):
    import app.security.password as pwmod
    # hash with current pepper
    hashed = pwmod.hash_password("pw")
    # change pepper to a different value and ensure verification fails
    monkeypatch.setattr(pwmod.settings, "PEPPER", "some-other-pepper")
    assert not pwmod.verify_password("pw", hashed)

