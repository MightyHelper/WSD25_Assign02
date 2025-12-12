from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.db.models import Author
from app.db.base import get_session

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])

class AuthorOut(BaseModel):
    id: str
    name: str

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/", response_model=List[AuthorOut])
async def list_authors(page: int = 1, per_page: int = 20, name: str | None = None):
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(Author)
        if name:
            stmt = stmt.where(Author.name.ilike(f"%{name}%"))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        authors = res.scalars().all()
        return [AuthorOut.model_validate(a) for a in authors
                ]
