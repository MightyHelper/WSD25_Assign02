from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from app.db.models import Comment, UserBookReview
from app.db.base import get_session
from app.db.models import User

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class CommentOut(BaseModel):
    id: str
    user_id: str
    review_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/{review_id}/comments", response_model=list[CommentOut])
async def list_comments_for_review(response: Response, review_id: str, page: int = 1, per_page: int = 20):
    async with get_session() as session:
        # ensure review exists
        r = await session.get(UserBookReview, review_id)
        if not r:
            raise HTTPException(status_code=404, detail="Review not found")
        from sqlalchemy import select, func
        stmt = select(Comment).where(Comment.review_id == review_id).offset((page - 1) * per_page).limit(per_page)
        # total count
        count_stmt = select(func.count()).select_from(Comment).where(Comment.review_id == review_id)
        total = int((await session.execute(count_stmt)).scalar_one())
        res = await session.execute(stmt)
        cms = res.scalars().all()
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(per_page)
        return [CommentOut.model_validate(c) for c in cms]

# Adapter: Allow creating comments under a review path (nested style)
class CommentIn(BaseModel):
    id: str
    user_id: str
    content: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/{review_id}/comments", response_model=CommentOut, status_code=201)
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
