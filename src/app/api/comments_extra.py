from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.db.models import Comment, UserBookReview
from app.storage.base import get_session
from app.security.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class CommentOut(BaseModel):
    id: str
    user_id: str
    review_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/{review_id}/comments", response_model=List[CommentOut])
async def list_comments_for_review(review_id: str, page: int = 1, per_page: int = 20):
    async with get_session() as session:
        # ensure review exists
        r = await session.get(UserBookReview, review_id)
        if not r:
            raise HTTPException(status_code=404, detail="Review not found")
        from sqlalchemy import select
        stmt = select(Comment).where(Comment.review_id == review_id).offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        cms = res.scalars().all()
        return [CommentOut.model_validate(c) for c in cms]

# Adapter: Allow creating comments under a review path (nested style)
class CommentIn(BaseModel):
    id: str
    user_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/{review_id}/comments", response_model=CommentOut, status_code=201)
async def create_comment_under_review(review_id: str, c: CommentIn, current_user: User = Depends(get_current_user)):
    """Adapter route: create a comment for a given review id.
    This mirrors the top-level `POST /api/v1/comments/` behavior but keeps a nicer nested URL.
    """
    async with get_session() as session:
        # ensure review exists
        r = await session.get(UserBookReview, review_id)
        if not r:
            raise HTTPException(status_code=404, detail="Review not found")
        cm = Comment(id=c.id, user_id=c.user_id, review_id=review_id, content=c.content)
        session.add(cm)
        await session.commit()
        await session.refresh(cm)
        return CommentOut.model_validate(cm)
