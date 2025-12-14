from app.db.models import Book
from app.storage.base import get_session
from .base import BlobStorage

class DBBlobStorage(BlobStorage):
    async def save_blob(self, key: str, data: bytes) -> str:
        # key is book id here; store bytes into book.cover
        async with get_session() as session:
            book = await session.get(Book, key)
            if not book:
                raise ValueError("Book not found")
            book.cover = data
            session.add(book)
            await session.commit()
            return key

    async def get_blob(self, key: str) -> bytes | None:
        async with get_session() as session:
            book = await session.get(Book, key)
            if not book:
                return None
            return book.cover

    async def delete_blob(self, key: str) -> None:
        async with get_session() as session:
            book = await session.get(Book, key)
            if book:
                book.cover = None
                session.add(book)
                await session.commit()
