from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel
from app.db.models import Book, User, UserBookLikes
from app.db.base import get_session
from app.db import get_storage_dep, BlobStorage
from app.redis_client import get_redis_dep
from app.security.dependencies import get_current_user
from app.storage import get_storage
import logging

router = APIRouter(prefix="/api/v1/books", tags=["books"])

CACHE_TTL = 60  # seconds

class BookIn(BaseModel):
    id: str
    title: str
    author_id: str | None = None
    isbn: str | None = None
    description: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

class BookOut(BaseModel):
    id: str
    title: str
    author_id: str | None = None
    isbn: str | None = None
    description: str | None = None

    model_config = {"extra": "ignore", "from_attributes": True}

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

@router.post("/", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(book_in: BookIn):
    async with get_session() as session:
        b = Book(id=book_in.id, title=book_in.title, author_id=book_in.author_id, isbn=book_in.isbn, description=book_in.description)
        session.add(b)
        await session.commit()
        await session.refresh(b)
        return BookOut.model_validate(b)

@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: str, redis=Depends(get_redis_dep)):
    cache_key = f"book:{book_id}"
    cached = await redis.get(cache_key)
    if cached:
        # cached is JSON string; return it directly
        from json import loads
        return BookOut.model_validate(loads(cached))

    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        book_out = BookOut.model_validate(b)
        # cache
        from json import dumps
        await redis.set(cache_key, dumps(book_out.model_dump()), ex=CACHE_TTL)
        return book_out

@router.delete("/{book_id}")
async def delete_book(book_id: str):
    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        # If there's a cover path, try to remove file
        if getattr(b, 'cover_path', None):
            try:
                from pathlib import Path
                await __import__('asyncio').get_event_loop().run_in_executor(None, Path(b.cover_path).unlink)
            except Exception:
                pass
        await session.delete(b)
        await session.commit()
        return {"ok": True}

@router.get("/", response_model=list[BookListOut])
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

# Blob endpoints
@router.put("/{book_id}/cover", status_code=status.HTTP_200_OK)
async def upload_cover(book_id: str, request: Request, storage: BlobStorage = Depends(get_storage_dep)):
    data = await request.body()
    try:
        await storage.save_blob(book_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"ok": True}

@router.post("/{book_id}/cover")
async def upload_cover_alt(book_id: str, request: Request):
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
            book.cover_path = None
        else:
            book.cover_path = result
            book.cover = None
        session.add(book)
        await session.commit()
        await session.refresh(book)
        logging.getLogger(__name__).info("After upload - book.cover_path=%s, book.cover is %s", getattr(book, 'cover_path', None), 'set' if getattr(book,'cover',None) else 'none')
        return {"ok": True, "book_id": book_id}

@router.get("/{book_id}/cover")
async def get_cover(book_id: str, storage: BlobStorage = Depends(get_storage_dep)):
    # Prefer storage abstraction first
    try:
        blob = await storage.get_blob(book_id)
        if blob:
            return Response(content=blob, media_type="application/octet-stream")
    except Exception:
        pass
    # fallback to DB-stored blob or filesystem path
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
