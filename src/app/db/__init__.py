from ..config import settings, FileStorageOption, StorageKind
from app.storage.db_storage import DBBlobStorage
from app.storage.fs_storage import FileSystemStorage
from app.storage.base import BlobStorage

_storage_instance: BlobStorage | None = None

def _create_storage() -> BlobStorage:
    if settings.STORAGE_KIND == StorageKind.DB:
        return DBBlobStorage()
    if settings.STORAGE_KIND == StorageKind.FS:
        return FileSystemStorage()
    return DBBlobStorage()

def get_storage_instance() -> BlobStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = _create_storage()
    return _storage_instance

# FastAPI dependency
def get_storage_dep() -> BlobStorage:
    return get_storage_instance()
