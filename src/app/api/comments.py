from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel
from ..db.models import Comment, UserBookReview
from app.db.base import get_session
from app.db.models import User
from ..schemas.pagination import PagedResponse
from ..security.dependencies import get_current_user

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
async def create_comment(c: CommentIn, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        # ensure current user is the comment author
        if current_user.type != 1:
            if c.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Forbidden")
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
@router.get("/review/{review_id}/comments", response_model=PagedResponse[CommentOut])
async def list_comments_for_review(
    response: Response,
    review_id: str,
    page: int = 1,
    per_page: int = 20,
    content: str | None = None,
    sort_by: str | None = None,
    sort_dir: str = "asc",
):
    async with get_session() as session:
        # ensure review exists
        r = await session.get(UserBookReview, review_id)
        if not r:
            raise HTTPException(status_code=404, detail="Review not found")
        from sqlalchemy import select, asc, desc, func

        stmt = select(Comment).where(Comment.review_id == review_id)
        if content:
            stmt = stmt.where(Comment.content.ilike(f"%{content}%"))
        # total count
        count_stmt = select(func.count()).select_from(Comment).where(Comment.review_id == review_id)
        if content:
            count_stmt = count_stmt.where(Comment.content.ilike(f"%{content}%"))
        total = int((await session.execute(count_stmt)).scalar_one())
        if sort_by and hasattr(Comment, sort_by):
            col = getattr(Comment, sort_by)
            if sort_dir and sort_dir.lower().startswith("desc"):
                stmt = stmt.order_by(desc(col))
            else:
                stmt = stmt.order_by(asc(col))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        cms = res.scalars().all()
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(per_page)
        return PagedResponse[CommentOut](
            totalElements=total,
            page=page,
            size=per_page,
            content=[CommentOut.model_validate(cm) for cm in cms],
            totalPages=(total + per_page - 1) // per_page if per_page else 0,
        )


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
