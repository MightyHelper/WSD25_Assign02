from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db.models import UserBookReview, Book
from app.storage.base import get_session

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class ReviewOut(BaseModel):
    id: str
    book_id: str
    user_id: str
    title: str | None = None
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/book/{book_id}", response_model=List[ReviewOut])
async def list_reviews_for_book(book_id: str, page: int = 1, per_page: int = 20):
    async with get_session() as session:
        # ensure book exists
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        from sqlalchemy import select
        stmt = select(UserBookReview).where(UserBookReview.book_id == book_id).offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        revs = res.scalars().all()
        return [ReviewOut.model_validate(r) for r in revs]

