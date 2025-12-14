from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import Comment, UserBookReview
from app.db.base import get_session
from app.db.models import User

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])

class CommentIn(BaseModel):
    id: str
    user_id: str
    review_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class CommentOut(BaseModel):
    id: str
    user_id: str
    review_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(c: CommentIn):
    async with get_session() as session:
        cm = Comment(id=c.id, user_id=c.user_id, review_id=c.review_id, content=c.content)
        session.add(cm)
        await session.commit()
        await session.refresh(cm)
        return CommentOut.model_validate(cm)

@router.get("/{comment_id}", response_model=CommentOut)
async def get_comment(comment_id: str):
    async with get_session() as session:
        cm = await session.get(Comment, comment_id)
        if not cm:
            raise HTTPException(status_code=404, detail="Comment not found")
        return CommentOut.model_validate(cm)

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str):
    async with get_session() as session:
        cm = await session.get(Comment, comment_id)
        if not cm:
            raise HTTPException(status_code=404, detail="Comment not found")
        await session.delete(cm)
        await session.commit()
        return {"ok": True}

# ...merged from comments_extra.py - nested review routes...
@router.get("/review/{review_id}/comments", response_model=list[CommentOut])
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

@router.post("/review/{review_id}/comments", response_model=CommentOut, status_code=201)
async def create_comment_under_review(review_id: str, c: CommentIn):
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
