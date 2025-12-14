import os
from pathlib import Path
from typing import Optional
from .base import BlobStorage

STORAGE_DIR = Path("/tmp/fne_blobs")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class FileSystemStorage(BlobStorage):
    async def save_blob(self, key: str, data: bytes) -> str:
        path = STORAGE_DIR / key
        path.write_bytes(data)
        return str(path)

    async def get_blob(self, key: str) -> Optional[bytes]:
        path = STORAGE_DIR / key
        if not path.exists():
            return None
        return path.read_bytes()

    async def delete_blob(self, key: str) -> None:
        path = STORAGE_DIR / key
        if path.exists():
            path.unlink()

