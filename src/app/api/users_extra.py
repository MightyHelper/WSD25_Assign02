from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.db.models import User, UserBookLikes
from app.db.base import get_session

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    active_order_id: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeOut(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool
    favourite: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/me", response_model=UserOut)
async def get_me(user_id: str):
    async with get_session() as session:
        u = await session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(u)

@router.get("/me/likes", response_model=List[LikeOut])
async def get_my_likes(user_id: str, page: int = 1, per_page: int = 20, wishlist: bool | None = None, favourite: bool | None = None):
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(UserBookLikes).where(UserBookLikes.user_id == user_id)
        if wishlist is not None:
            stmt = stmt.where(UserBookLikes.wishlist == bool(wishlist))
        if favourite is not None:
            stmt = stmt.where(UserBookLikes.favourite == bool(favourite))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        items = res.scalars().all()
        return [LikeOut.model_validate(i) for i in items]
