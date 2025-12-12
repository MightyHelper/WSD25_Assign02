from ..config import settings, FileStorageOption
from .db_storage import DBBlobStorage
from .fs_storage import FileSystemStorage
from .base import BlobStorage

_storage_instance: BlobStorage | None = None

def _create_storage() -> BlobStorage:
    if settings.FILE_STORAGE == FileStorageOption.db:
        return DBBlobStorage()
    if settings.FILE_STORAGE == FileStorageOption.filesystem:
        return FileSystemStorage()
    # s3 not implemented yet -> fallback to DB storage
    return DBBlobStorage()

def get_storage_instance() -> BlobStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = _create_storage()
    return _storage_instance

# FastAPI dependency
def get_storage_dep() -> BlobStorage:
    return get_storage_instance()
