from typing import TypeVar, Optional
from pydantic import BaseModel

class PagedResponse[T](BaseModel):
    content: list[T]
    """A paginated response model."""
    page: int
    """Current page number."""
    size: int
    """Number of items per page."""
    totalElements: int
    """Total number of elements."""
    totalPages: int
    """Total number of pages."""
    sort: Optional[str] = None
    """Sorting criteria."""

    model_config = {"extra": "ignore"}

