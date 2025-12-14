from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from pydantic import BaseModel
from typing import List
from ..security.dependencies import get_current_user
from app.db.models import Book, UserBookLikes, User
from app.storage.base import get_session
from app.storage import get_storage
import logging

router = APIRouter(prefix="/api/v1/books", tags=["books"])

class BookListOut(BaseModel):
    id: str
    title: str
    author_id: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class LikeIn(BaseModel):
    user_id: str | None = None
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
async def like_book(book_id: str, wishlist: bool | None = None, favourite: bool | None = None, current_user: User = Depends(get_current_user)):
    """Upsert the user's like/wishlist flags for a book.
    Accepts query parameters: wishlist, favourite.
    Returns 201 when created, 200 when updated.
    """
    # use authenticated user
    user_id = current_user.id

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

# New endpoints for cover upload/download
@router.post("/{book_id}/cover")
async def upload_cover(book_id: str, request: Request, current_user: User = Depends(get_current_user)):
    """Upload a cover image for a book. Uses configured storage (fs or db). Accepts raw bytes in the request body."""
    storage = get_storage()
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Empty body")
    async with get_session() as session:
        book = await session.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        # if storage.save_cover returns a path, store cover_path; if None, store blob
        result = await storage.save_cover(book_id, data)
        if result is None:
            # DB storage: write to blob column
            book.cover = data
        else:
            book.cover_path = result
        session.add(book)
        await session.commit()
        await session.refresh(book)
        logging.getLogger(__name__).info("After upload - book.cover_path=%s, book.cover is %s", getattr(book, 'cover_path', None), 'set' if getattr(book,'cover',None) else 'none')
        return {"ok": True, "book_id": book_id}

@router.get("/{book_id}/cover")
async def get_cover(book_id: str):
    """Return cover image bytes for a book if present."""
    async with get_session() as session:
        book = await session.get(Book, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        # Prefer filesystem path if present
        if getattr(book, "cover_path", None):
            from pathlib import Path
            p = Path(book.cover_path)
            import asyncio
            try:
                data = await asyncio.to_thread(p.read_bytes)
                return Response(content=data, media_type="application/octet-stream")
            except Exception as exc:
                logging.getLogger(__name__).exception("Failed to read cover file %s: %s", p, exc)
                raise HTTPException(status_code=404, detail="Cover not found")
        # fallback to blob stored in DB
        if getattr(book, "cover", None):
            return Response(content=book.cover, media_type="application/octet-stream")
        raise HTTPException(status_code=404, detail="Cover not found")
