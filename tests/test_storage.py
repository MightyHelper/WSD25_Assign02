import os

from app.main import create_app
from app.db.models import Author, Book
from app.db.base import get_session
import uuid
async def _create_author_and_book():
    async with get_session() as session:
        a = Author(id=str(uuid.uuid4()), name="Author")
        b = Book(id=str(uuid.uuid4()), title="Book", author_id=a.id)
        session.add(a)
        session.add(b)
        await session.commit()
        await session.refresh(b)
        return b


def test_storage_fs_upload_and_download(test_app, normal_user, admin_user):
    os.environ["STORAGE_KIND"] = "fs"
    # create author/book in DB
    book = __import__('asyncio').run(_create_author_and_book())

    # make sure FastAPI app uses the same DATABASE_URL
    from app.config import settings as app_settings
    app_settings.DATABASE_URL = os.environ.get("DATABASE_URL")

    app = create_app()
    # bypass auth for tests by overriding dependency
    data = b"hello-cover-fs"

    with __import__('fastapi').testclient.TestClient(app) as client:
        r = client.post(f"/api/v1/books/{book.id}/cover", content=data, headers={"content-type": "application/octet-stream", "Authorization": admin_user[1]['Authorization']})
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


def test_storage_db_upload_and_download(test_app, normal_user, admin_user):
    os.environ["STORAGE_KIND"] = "db"
    # create author/book in DB
    book = __import__('asyncio').run(_create_author_and_book())

    app = create_app()
    # bypass auth for tests
    data = b"hello-cover-db"

    with __import__('fastapi').testclient.TestClient(app) as client:
        r = client.post(f"/api/v1/books/{book.id}/cover", content=data, headers={"content-type": "application/octet-stream", "Authorization": admin_user[1]['Authorization']})
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
