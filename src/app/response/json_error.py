from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

class JSONError(BaseModel):
    timestamp: datetime
    path: str
    status: int
    code: str
    message: str
    details: Optional[Any] = None

    @classmethod
    def from_exception(cls, path: str, status: int, code: str, message: str, details: Any = None) -> "JSONError":
        return cls(timestamp=datetime.utcnow(), path=path, status=status, code=code, message=message, details=details)

