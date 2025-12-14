import os
import pathlib
import pytest
from fastapi.testclient import TestClient
from app.security.jwt import create_access_token
from app.security.password import hash_password

# ensure test environment variables are set before importing the application
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
# avoid initializing redis during tests unless explicitly provided
os.environ.setdefault("REDIS_URL", "")
# provide PEPPER used by security settings during tests
os.environ.setdefault("PEPPER", "tests-pepper")
# mark environment as test so runtime code can reset DB between tests when needed
os.environ.setdefault("APP_ENV", "test")

from app.main import create_app
from app.db.base import get_session
from app.db.models import User

import asyncio


def _create_admin_in_db(username: str = "__test_admin"):
    async def _create():
        async with get_session() as session:
            # remove any existing admin with this username
            from sqlalchemy import select
            stmt = select(User).where(User.username == username)
            res = await session.execute(stmt)
            existing = res.scalars().first()
            if existing:
                return existing
            uid = str(__import__('uuid').uuid4())
            u = User(id=uid, username=username, email=f"{uid}@example.com", password_hash=hash_password('adm1npw'), type=1)
            session.add(u)
            await session.commit()
            await session.refresh(u)
            return u
    return asyncio.run(_create())


@pytest.fixture(scope="function")
def test_app() -> TestClient:
    # ensure a clean sqlite DB for this test
    db_path = pathlib.Path("./test_db.sqlite")
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def admin_headers():
    # create admin in DB and return Authorization header
    admin = _create_admin_in_db()
    token = create_access_token(subject=admin.id, user_type=1)
    return {"Authorization": f"Bearer {token}"}
