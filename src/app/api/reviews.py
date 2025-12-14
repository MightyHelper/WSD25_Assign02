from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import UserBookReview, Book
from app.db.base import get_session
from app.db.models import User

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class ReviewIn(BaseModel):
    id: str
    book_id: str
    user_id: str
    title: str | None = None
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class ReviewOut(BaseModel):
    id: str
    book_id: str
    user_id: str
    title: str | None = None
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(r: ReviewIn):
    async with get_session() as session:
        rev = UserBookReview(id=r.id, book_id=r.book_id, user_id=r.user_id, title=r.title, content=r.content)
        session.add(rev)
        await session.commit()
        await session.refresh(rev)
        return ReviewOut.model_validate(rev)

@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(review_id: str):
    async with get_session() as session:
        rev = await session.get(UserBookReview, review_id)
        if not rev:
            raise HTTPException(status_code=404, detail="Review not found")
        return ReviewOut.model_validate(rev)

@router.delete("/{review_id}")
async def delete_review(review_id: str):
    async with get_session() as session:
        rev = await session.get(UserBookReview, review_id)
        if not rev:
            raise HTTPException(status_code=404, detail="Review not found")
        await session.delete(rev)
        await session.commit()
        return {"ok": True}

@router.get("/book/{book_id}", response_model=list[ReviewOut])
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
