from typing import Protocol, Optional
from uuid import uuid4
from pathlib import Path
from app.config import settings, StorageKind
from app.db.models import Book
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class Storage(Protocol):
    async def save_cover(self, book_id: str, data: bytes) -> Optional[str]:
        """Save the cover data. Returns a path or None if stored in DB."""

    async def get_cover(self, book: Book) -> Optional[bytes]:
        """Return raw bytes for cover or None."""

class FSStorage:
    async def save_cover(self, book_id: str, data: bytes) -> Optional[str]:
        # create filename
        filename = f"{book_id}-{uuid4().hex}.bin"
        dest = UPLOAD_DIR / filename
        # write using thread to avoid blocking event loop
        await asyncio.to_thread(dest.write_bytes, data)
        # return absolute resolved path to avoid cwd-related issues
        return str(dest.resolve())

    async def get_cover(self, book: Book) -> Optional[bytes]:
        path = book.cover_path
        logger.info("FSStorage.get_cover called for book=%s cover_path=%s", getattr(book, 'id', None), path)
        if not path:
            logger.info("no cover_path set")
            return None
        p = Path(path)
        exists = await asyncio.to_thread(p.exists)
        logger.info("Path exists: %s (%s)", exists, p)
        if not exists:
            return None
        data = await asyncio.to_thread(p.read_bytes)
        logger.info("Read %d bytes", len(data))
        return data

class DBStorage:
    async def save_cover(self, book_id: str, data: bytes) -> Optional[str]:
        # DB storage writes to the Book.cover column; higher-level code will handle DB write
        return None

    async def get_cover(self, book: Book) -> Optional[bytes]:
        return book.cover


def get_storage() -> Storage:
    # compare against the enum StorageKind
    if settings.STORAGE_KIND == StorageKind.FS:
        return FSStorage()
    return DBStorage()
