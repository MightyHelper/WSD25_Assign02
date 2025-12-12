import uuid

from app.db.models import User
from app.db.base import get_session
from app.security.password import hash_password, verify_password


def test_hash_and_verify():
    pw = "mysecret"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("wrong", h) is False


def test_user_model_roundtrip():
    user_id = str(uuid.uuid4())
    async def _create_get():
        async with get_session() as session:
            u = User(id=user_id, username="u2", email="u2@example.com", password_hash=hash_password("pw"))
            session.add(u)
            await session.commit()
            await session.refresh(u)
            return u
    import asyncio
    u = asyncio.run(_create_get())
    assert u.email == "u2@example.com"

