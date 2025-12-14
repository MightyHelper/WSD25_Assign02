from app.db.models import Book
from app.db.base import get_session
from .base import BlobStorage
import logging

logger = logging.getLogger('app.storage.db')

class DBBlobStorage(BlobStorage):
    async def save_blob(self, key: str, data: bytes) -> str:
        # key is book id here; store bytes into book.cover
        async with get_session() as session:
            book = await session.get(Book, key)
            if not book:
                logger.warning("Attempt to save blob for missing book id=%s", key)
                raise ValueError("Book not found")
            book.cover = data
            session.add(book)
            await session.commit()
            logger.info("Saved blob into DB for book id=%s size=%d", key, len(data))
            return key

    async def get_blob(self, key: str) -> bytes | None:
        async with get_session() as session:
            book = await session.get(Book, key)
            if not book:
                logger.debug("Requested blob for missing book id=%s", key)
                return None
            logger.debug("Returning DB blob for book id=%s size=%s", key, len(book.cover) if book.cover else 0)
            return book.cover

    async def delete_blob(self, key: str) -> None:
        async with get_session() as session:
            book = await session.get(Book, key)
            if book:
                book.cover = None
                session.add(book)
                await session.commit()
                logger.info("Removed DB blob for book id=%s", key)
