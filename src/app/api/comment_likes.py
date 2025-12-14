from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db.models import Comment, CommentLike, User
from app.storage.base import get_session
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class LikeOut(BaseModel):
    message: str

@router.post("/{review_id}/comments/{comment_id}/like", response_model=LikeOut)
async def like_comment(review_id: str, comment_id: str, current_user: User = Depends(get_current_user)):
    """Authenticate and create a like for the comment by the current user."""
    user_id = current_user.id
    async with get_session() as session:
        # ensure comment exists and belongs to the review
        cm = await session.get(Comment, comment_id)
        if not cm or cm.review_id != review_id:
            raise HTTPException(status_code=404, detail="Comment not found")
        existing = await session.get(CommentLike, (comment_id, user_id))
        if existing:
            return LikeOut(message="Already liked")
        new = CommentLike(comment_id=comment_id, user_id=user_id)
        session.add(new)
        await session.commit()
        return LikeOut(message="Comment liked successfully.")

@router.delete("/{review_id}/comments/{comment_id}/like", response_model=LikeOut)
async def unlike_comment(review_id: str, comment_id: str, current_user: User = Depends(get_current_user)):
    """Authenticate and remove the current user's like for the comment."""
    user_id = current_user.id
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
