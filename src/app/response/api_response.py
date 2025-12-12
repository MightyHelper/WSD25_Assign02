from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status: int
    data: T

    @classmethod
    def success(cls, data: T, status: int = 200) -> "APIResponse[T]":
        return cls(status=status, data=data)

