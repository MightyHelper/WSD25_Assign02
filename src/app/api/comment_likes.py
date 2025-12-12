from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.models import Comment, CommentLike, User
from app.db.base import get_session

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class LikeOut(BaseModel):
    message: str

@router.post("/{review_id}/comments/{comment_id}/like", response_model=LikeOut)
async def like_comment(review_id: str, comment_id: str, user_id: str):
    async with get_session() as session:
        # ensure review exists
        cm = await session.get(Comment, comment_id)
        if not cm or cm.review_id != review_id:
            raise HTTPException(status_code=404, detail="Comment not found")
        # ensure user exists
        u = await session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        existing = await session.get(CommentLike, (comment_id, user_id))
        if existing:
            return LikeOut(message="Already liked")
        new = CommentLike(comment_id=comment_id, user_id=user_id)
        session.add(new)
        await session.commit()
        return LikeOut(message="Comment liked successfully.")

@router.delete("/{review_id}/comments/{comment_id}/like", response_model=LikeOut)
async def unlike_comment(review_id: str, comment_id: str, user_id: str):
    async with get_session() as session:
        cm = await session.get(Comment, comment_id)
        if not cm or cm.review_id != review_id:
            raise HTTPException(status_code=404, detail="Comment not found")
        existing = await session.get(CommentLike, (comment_id, user_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Like not found")
        await session.delete(existing)
        await session.commit()
        return LikeOut(message="Comment like removed successfully.")
