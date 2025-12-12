from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from app.db.models import Book, UserBookLikes, User
from app.db.base import get_session

router = APIRouter(prefix="/api/v1/books", tags=["books"])

class BookListOut(BaseModel):
    id: str
    title: str
    author_id: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeIn(BaseModel):
    user_id: str
    wishlist: bool | None = False
    favourite: bool | None = False

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeOut(BaseModel):
    book_id: str
    user_id: str
    wishlist: bool
    favourite: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.get("/", response_model=List[BookListOut])
async def list_books(page: int = 1, per_page: int = 20, title: str | None = None, author_id: str | None = None):
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(Book)
        if title:
            # use ilike where supported by dialect; for sqlite this still works
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author_id:
            stmt = stmt.where(Book.author_id == author_id)
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        books = res.scalars().all()
        return [BookListOut.model_validate(b) for b in books]

@router.patch("/{book_id}/like", response_model=LikeOut)
async def like_book(book_id: str, user_id: str, wishlist: bool | None = None, favourite: bool | None = None):
    """Upsert the user's like/wishlist flags for a book.
    Accepts query parameters: user_id (required), wishlist, favourite.
    Returns 201 when created, 200 when updated.
    """
    async with get_session() as session:
        # ensure book exists
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        # ensure user exists
        u = await session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        # check existing like
        existing = await session.get(UserBookLikes, (book_id, user_id))
        if existing:
            if wishlist is not None:
                existing.wishlist = bool(wishlist)
            if favourite is not None:
                existing.favourite = bool(favourite)
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return LikeOut.model_validate(existing)
        # create new
        new = UserBookLikes(book_id=book_id, user_id=user_id, wishlist=bool(wishlist), favourite=bool(favourite))
        session.add(new)
        await session.commit()
        await session.refresh(new)
        # FastAPI will default status code 200; to return 201 we raise a Response with status
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=LikeOut.model_validate(new).model_dump())
