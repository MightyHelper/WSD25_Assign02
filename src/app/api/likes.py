from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import UserBookLikes
from app.storage.base import get_session
from app.security.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/api/v1/likes", tags=["likes"])

class LikeIn(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool = False
    favourite: bool = False

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeOut(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool
    favourite: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=LikeOut, status_code=status.HTTP_201_CREATED)
async def upsert_like(l: LikeIn, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        existing = await session.get(UserBookLikes, (l.book_id, l.user_id))
        if existing:
            existing.wishlist = l.wishlist
            existing.favourite = l.favourite
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return LikeOut.model_validate(existing)
        new = UserBookLikes(book_id=l.book_id, user_id=l.user_id, wishlist=l.wishlist, favourite=l.favourite)
        session.add(new)
        await session.commit()
        await session.refresh(new)
        return LikeOut.model_validate(new)

@router.delete("/")
async def delete_like(book_id: str, user_id: str):
    async with get_session() as session:
        existing = await session.get(UserBookLikes, (book_id, user_id))
        if not existing:
            raise HTTPException(status_code=404, detail="Like not found")
        await session.delete(existing)
        await session.commit()
        return {"ok": True}
