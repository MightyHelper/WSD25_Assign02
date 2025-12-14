from abc import ABC, abstractmethod
from typing import Optional

class BlobStorage(ABC):
    @abstractmethod
    async def save_blob(self, key: str, data: bytes) -> str:
        """Save a blob and return an identifier/url."""
        raise NotImplementedError()

    @abstractmethod
    async def get_blob(self, key: str) -> Optional[bytes]:
        raise NotImplementedError()

    @abstractmethod
    async def delete_blob(self, key: str) -> None:
        raise NotImplementedError()

