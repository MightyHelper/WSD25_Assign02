import os
from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.db.base import init_db, create_tables
from app.db.models import Author, Book
from app.db.base import get_session
from app.security.jwt import create_access_token
from app.security.password import hash_password
from app.security.dependencies import get_current_user
import uuid

# helper used in tests to create DB objects
async def create_initial_data(username: str):
    await init_db(os.environ.get("DATABASE_URL"))
    await create_tables()
    async with get_session() as session:
        a = Author(id=str(uuid.uuid4()), name="Author")
        b = Book(id=str(uuid.uuid4()), title="Book", author_id=a.id)
        session.add(a)
        session.add(b)
        from app.db.models import User
        u = User(id=str(uuid.uuid4()), username=username, email=f"{username}@example.com", password_hash=hash_password("pass"))
        session.add(u)
        await session.commit()
        await session.refresh(b)
        return b, u

def test_storage_fs_upload_and_download():
    os.environ["STORAGE_KIND"] = "fs"
    uname = f"storage_{uuid.uuid4().hex[:8]}"
    book, user = __import__('asyncio').run(create_initial_data(uname))

    # make sure FastAPI app uses the same DATABASE_URL
    from app.config import settings as app_settings
    app_settings.DATABASE_URL = os.environ.get("DATABASE_URL")

    app = create_app()
    # bypass auth for tests by overriding dependency
    app.dependency_overrides[get_current_user] = lambda: user
    data = b"hello-cover-fs"

    with TestClient(app) as client:
        r = client.post(f"/api/v1/books/{book.id}/cover", content=data, headers={"content-type": "application/octet-stream"})
        assert r.status_code == 200
        # verify that book record now points to a file or contains blob
        async def check():
            async with get_session() as session:
                b = await session.get(Book, book.id)
                return b.cover_path, b.cover
        cover_path, cover_blob = __import__('asyncio').run(check())
        if cover_path:
            import pathlib
            assert pathlib.Path(cover_path).exists()
        else:
            assert cover_blob == data

def test_storage_db_upload_and_download():
    os.environ["STORAGE_KIND"] = "db"
    uname2 = f"storage_{uuid.uuid4().hex[:8]}"
    book, user = __import__('asyncio').run(create_initial_data(uname2))

    from app.config import settings as app_settings
    app_settings.DATABASE_URL = os.environ.get("DATABASE_URL")

    app = create_app()
    # bypass auth for tests
    app.dependency_overrides[get_current_user] = lambda: user
    data = b"hello-cover-db"

    with TestClient(app) as client:
        r = client.post(f"/api/v1/books/{book.id}/cover", content=data, headers={"content-type": "application/octet-stream"})
        assert r.status_code == 200
        async def check2():
            async with get_session() as session:
                b = await session.get(Book, book.id)
                return b.cover_path, b.cover
        cover_path, cover_blob = __import__('asyncio').run(check2())
        if cover_path:
            import pathlib
            assert pathlib.Path(cover_path).exists()
        else:
            assert cover_blob == data
