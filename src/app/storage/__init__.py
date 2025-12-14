from typing import Protocol, Optional
from uuid import uuid4
from pathlib import Path
from app.config import settings, StorageKind
from app.db.models import Book
import os
import asyncio
import logging

from .db_storage import DBBlobStorage

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
        if not path:
            return None
        p = Path(path)
        exists = await asyncio.to_thread(p.exists)
        if not exists:
            return None
        data = await asyncio.to_thread(p.read_bytes)
        return data

    # provide blob-style methods used in tests
    async def save_blob(self, key: str, data: bytes) -> str:
        return await self.save_cover(key, data)

    async def get_blob(self, key: str) -> Optional[bytes]:
        # key is filename (book id in tests) - attempt to find a file starting with key
        for p in UPLOAD_DIR.iterdir():
            if p.name.startswith(key):
                return await asyncio.to_thread(p.read_bytes)
        return None

    async def delete_blob(self, key: str) -> None:
        for p in UPLOAD_DIR.iterdir():
            if p.name.startswith(key):
                await asyncio.to_thread(p.unlink)

class DBStorage:
    async def save_cover(self, book_id: str, data: bytes) -> Optional[str]:
        # DB storage writes to the Book.cover column; higher-level code will handle DB write
        return None

    async def get_cover(self, book: Book) -> Optional[bytes]:
        return book.cover

    # Provide blob aliases using the DBBlobStorage implementation
    def _db_blob_impl(self) -> DBBlobStorage:
        return DBBlobStorage()

    async def save_blob(self, key: str, data: bytes) -> str:
        return await self._db_blob_impl().save_blob(key, data)

    async def get_blob(self, key: str) -> Optional[bytes]:
        return await self._db_blob_impl().get_blob(key)

    async def delete_blob(self, key: str) -> None:
        await self._db_blob_impl().delete_blob(key)


def get_storage() -> Storage:
    # compare against the enum StorageKind
    if settings.STORAGE_KIND == StorageKind.FS:
        return FSStorage()
    # return DB-backed storage that supports both cover and blob operations
    return DBStorage()

# expose names expected by tests
__all__ = ["get_storage", "FSStorage", "DBStorage", "DBBlobStorage"]
