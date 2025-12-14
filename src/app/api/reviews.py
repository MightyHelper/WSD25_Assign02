from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import UserBookReview
from app.storage.base import get_session
from app.security.dependencies import get_current_user
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
async def create_review(r: ReviewIn, current_user: User = Depends(get_current_user)):
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
