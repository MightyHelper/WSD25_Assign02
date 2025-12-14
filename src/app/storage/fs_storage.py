import os
from pathlib import Path
from typing import Optional
from .base import BlobStorage
import logging

logger = logging.getLogger('app.storage.fs')

# default to a project-local uploads dir which is easier to inspect during tests
default_dir = Path("./uploads")
if os.environ.get('UPLOAD_DIR'):
    STORAGE_DIR = Path(os.environ.get('UPLOAD_DIR'))
else:
    STORAGE_DIR = default_dir
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class FileSystemStorage(BlobStorage):
    async def save_blob(self, key: str, data: bytes) -> str:
        path = STORAGE_DIR / key
        try:
            path.write_bytes(data)
            logger.info("Saved blob to filesystem key=%s path=%s size=%d", key, str(path), len(data))
            return str(path)
        except Exception as exc:
            logger.exception("Failed to save blob key=%s: %s", key, exc)
            raise

    async def get_blob(self, key: str) -> Optional[bytes]:
        path = STORAGE_DIR / key
        if not path.exists():
            logger.debug("Blob not found on filesystem key=%s", key)
            return None
        try:
            data = path.read_bytes()
            logger.debug("Read blob from filesystem key=%s size=%d", key, len(data))
            return data
        except Exception as exc:
            logger.exception("Failed to read blob key=%s: %s", key, exc)
            return None

    async def delete_blob(self, key: str) -> None:
        path = STORAGE_DIR / key
        if path.exists():
            try:
                path.unlink()
                logger.info("Deleted blob key=%s path=%s", key, str(path))
            except Exception:
                logger.exception("Failed to delete blob key=%s", key)
