import uuid

from app.db.models import Book
from app.db.base import init_db, create_tables, get_session
from fne.storage import get_storage_instance


def test_blob_save_and_get():
    # use sqlite test DB from conftest which is created on startup
    book_id = str(uuid.uuid4())
    # create a book record
    async def _create_book():
        async with get_session() as session:
            b = Book(id=book_id, title="B1")
            session.add(b)
            await session.commit()
    import asyncio
    asyncio.run(_create_book())

    storage = get_storage_instance()
    data = b"hello"
    import asyncio
    asyncio.run(storage.save_blob(book_id, data))
    got = asyncio.run(storage.get_blob(book_id))
    assert got == data


