from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, EmailStr
from app.db.models import User
from app.db.base import get_session
from app.security.password import hash_password
from app.security.dependencies import get_current_user, get_current_user_optional
import logging

logger = logging.getLogger('app.api.users')

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserIn(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str
    type: int | None = None

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    active_order_id: str | None = None
    type: int = 0

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeOut(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool
    favourite: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserIn, current_user: User | None = Depends(get_current_user_optional)):
    """Register or create a new user.
    If 'type' is provided and is not 0, the caller must be an admin (type==1).
    Otherwise, public registration creates normal users with type=0.
    """
    # enforce admin-only creation for admin-type users
    if user_in.type is not None and user_in.type != 0:
        # must be authenticated and admin
        if not current_user or getattr(current_user, 'type', 0) != 1:
            logger.warning("Unauthorized attempt to create user with type=%s by %s", user_in.type, getattr(current_user, 'id', None))
            raise HTTPException(status_code=403, detail="Admin privileges required to create this user type")
        new_type = int(user_in.type)
    else:
        new_type = 0

    async with get_session() as session:
        # ensure username/email unique
        from sqlalchemy import select
        stmt = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            logger.info("Attempt to create user with existing username/email=%s/%s", user_in.username, user_in.email)
            raise HTTPException(status_code=400, detail="Username or email already in use")
        u = User(id=user_in.id, username=user_in.username, email=user_in.email, password_hash=hash_password(user_in.password), type=new_type)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        logger.info("User created id=%s username=%s type=%s created_by=%s", u.id, u.username, u.type, getattr(current_user,'id',None))
        return UserOut.model_validate(u)

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.debug("get_me called for user id=%s", current_user.id)
    return UserOut.model_validate(current_user)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    async with get_session() as session:
        u = await session.get(User, user_id)
        if not u:
            logger.info("User not found: %s", user_id)
            raise HTTPException(status_code=404, detail="User not found")
        logger.debug("get_user returning user id=%s username=%s", u.id, u.username)
        return UserOut.model_validate(u)

@router.get("/me/likes", response_model=list[LikeOut])
async def get_my_likes(current_user: User = Depends(get_current_user), page: int = 1, per_page: int = 20, wishlist: bool | None = None, favourite: bool | None = None, sort_by: str | None = None, sort_dir: str = "asc", response: Response = None):
    async with get_session() as session:
        from sqlalchemy import select, asc, desc, func
        from app.db.models import UserBookLikes
        stmt = select(UserBookLikes).where(UserBookLikes.user_id == current_user.id)
        if wishlist is not None:
            stmt = stmt.where(UserBookLikes.wishlist == bool(wishlist))
        if favourite is not None:
            stmt = stmt.where(UserBookLikes.favourite == bool(favourite))
        # count
        count_stmt = select(func.count()).select_from(UserBookLikes).where(UserBookLikes.user_id == current_user.id)
        if wishlist is not None:
            count_stmt = count_stmt.where(UserBookLikes.wishlist == bool(wishlist))
        if favourite is not None:
            count_stmt = count_stmt.where(UserBookLikes.favourite == bool(favourite))
        total = int((await session.execute(count_stmt)).scalar_one())
        # ordering support
        if sort_by and hasattr(UserBookLikes, sort_by):
            col = getattr(UserBookLikes, sort_by)
            if sort_dir and sort_dir.lower().startswith("desc"):
                stmt = stmt.order_by(desc(col))
            else:
                stmt = stmt.order_by(asc(col))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        items = res.scalars().all()
        if response is not None:
            response.headers["X-Total-Count"] = str(total)
            response.headers["X-Page"] = str(page)
            response.headers["X-Per-Page"] = str(per_page)
        return [LikeOut.model_validate(i) for i in items]
