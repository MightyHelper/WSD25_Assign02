from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import Comment
from app.storage.base import get_session
from app.security.dependencies import get_current_user
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
async def create_comment(c: CommentIn, current_user: User = Depends(get_current_user)):
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
