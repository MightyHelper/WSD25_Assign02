from fastapi import APIRouter, HTTPException, status, Response, Depends
from pydantic import BaseModel

from app.db.base import get_session
from ..db.models import UserBookReview, Book, User, Comment, CommentLike
from ..security.dependencies import get_current_user

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
async def list_reviews_for_book(response: Response, book_id: str, page: int = 1, per_page: int = 20, title: str | None = None, content: str | None = None, sort_by: str | None = None, sort_dir: str = "asc"):
    async with get_session() as session:
        # ensure book exists
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        from sqlalchemy import select, asc, desc, func
        stmt = select(UserBookReview).where(UserBookReview.book_id == book_id)
        if title:
            stmt = stmt.where(UserBookReview.title.ilike(f"%{title}%"))
        if content:
            stmt = stmt.where(UserBookReview.content.ilike(f"%{content}%"))
        # total count
        count_stmt = select(func.count()).select_from(UserBookReview).where(UserBookReview.book_id == book_id)
        if title:
            count_stmt = count_stmt.where(UserBookReview.title.ilike(f"%{title}%"))
        if content:
            count_stmt = count_stmt.where(UserBookReview.content.ilike(f"%{content}%"))
        total = int((await session.execute(count_stmt)).scalar_one())
        if sort_by and hasattr(UserBookReview, sort_by):
            col = getattr(UserBookReview, sort_by)
            if sort_dir and sort_dir.lower().startswith("desc"):
                stmt = stmt.order_by(desc(col))
            else:
                stmt = stmt.order_by(asc(col))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        revs = res.scalars().all()
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(per_page)
        return [ReviewOut.model_validate(r) for r in revs]


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
