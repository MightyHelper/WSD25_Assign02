from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.db.models import User
from app.db.base import get_session
from app.security.password import hash_password
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserIn(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    active_order_id: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeOut(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool
    favourite: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserIn):
    """Register a new user (no authentication required)."""
    async with get_session() as session:
        # ensure username/email unique
        from sqlalchemy import select
        stmt = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Username or email already in use")
        u = User(id=user_in.id, username=user_in.username, email=user_in.email, password_hash=hash_password(user_in.password))
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return UserOut.model_validate(u)

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    async with get_session() as session:
        u = await session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(u)

@router.get("/me/likes", response_model=list[LikeOut])
async def get_my_likes(current_user: User = Depends(get_current_user), page: int = 1, per_page: int = 20, wishlist: bool | None = None, favourite: bool | None = None):
    async with get_session() as session:
        from sqlalchemy import select
        from app.db.models import UserBookLikes
        stmt = select(UserBookLikes).where(UserBookLikes.user_id == current_user.id)
        if wishlist is not None:
            stmt = stmt.where(UserBookLikes.wishlist == bool(wishlist))
        if favourite is not None:
            stmt = stmt.where(UserBookLikes.favourite == bool(favourite))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        items = res.scalars().all()
        return [LikeOut.model_validate(i) for i in items]
