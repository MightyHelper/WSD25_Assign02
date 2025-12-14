import logging

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from pydantic import BaseModel

from app.db import get_storage_dep, BlobStorage
from app.db.base import get_session
from app.db.models import Book, UserBookLikes, User
from app.redis_client import get_redis_dep
from app.storage import get_storage
from ..security.dependencies import get_current_user
from app.schemas.pagination import PagedResponse

router = APIRouter(prefix="/api/v1/books", tags=["books"])
logger = logging.getLogger('app.api.books')

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
async def create_book(book_in: BookIn, current_user: User = Depends(get_current_user)):
    # only admins can create books
    if getattr(current_user, 'type', 0) != 1:
        logger.warning("Unauthorized book create attempt by user id=%s", getattr(current_user, 'id', None))
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        b = Book(id=book_in.id, title=book_in.title, author_id=book_in.author_id, isbn=book_in.isbn, description=book_in.description)
        session.add(b)
        await session.commit()
        await session.refresh(b)
        logger.info("Book created id=%s title=%s author_id=%s by user id=%s", b.id, b.title, b.author_id, getattr(current_user,'id',None))
        return BookOut.model_validate(b)

@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: str, redis=Depends(get_redis_dep)):
    cache_key = f"book:{book_id}"
    cached = await redis.get(cache_key)
    if cached:
        logger.debug("Cache hit for %s", cache_key)
        # cached is JSON string; return it directly
        from json import loads
        return BookOut.model_validate(loads(cached))
    logger.debug("Cache miss for %s", cache_key)

    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            logger.info("Book not found: %s", book_id)
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
            logger.info("Book not found for delete: %s", book_id)
            raise HTTPException(status_code=404, detail="Book not found")
        # If there's a cover path, try to remove file
        if getattr(b, 'cover_path', None):
            try:
                from pathlib import Path
                await __import__('asyncio').get_event_loop().run_in_executor(None, Path(b.cover_path).unlink)
            except Exception as exc:
                logger.exception("Failed to remove cover file %s: %s", getattr(b, 'cover_path', None), exc)
        await session.delete(b)
        await session.commit()
        logger.info("Book deleted id=%s", book_id)
        return {"ok": True}

@router.get("/", response_model=PagedResponse[BookListOut])
async def list_books(response: Response, page: int = 1, per_page: int = 20, title: str | None = None, author_id: str | None = None, sort_by: str | None = None, sort_dir: str = "asc"):
    async with get_session() as session:
        from sqlalchemy import select, asc, desc, func
        stmt = select(Book)
        if title:
            # use ilike where supported by dialect; for sqlite this still works
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author_id:
            stmt = stmt.where(Book.author_id == author_id)
        # total
        count_stmt = select(func.count()).select_from(Book)
        if title:
            count_stmt = count_stmt.where(Book.title.ilike(f"%{title}%"))
        if author_id:
            count_stmt = count_stmt.where(Book.author_id == author_id)
        total = int((await session.execute(count_stmt)).scalar_one())
        # Apply ordering if requested and valid
        sort_clause = None
        if sort_by:
            # allow only attributes that exist on Book to avoid SQL injection
            if hasattr(Book, sort_by):
                col = getattr(Book, sort_by)
                sort_clause = f"{sort_by},{sort_dir}"
                if sort_dir and sort_dir.lower().startswith("desc"):
                    stmt = stmt.order_by(desc(col))
                else:
                    stmt = stmt.order_by(asc(col))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        books = res.scalars().all()
        # set headers for backward compatibility
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(per_page)
        # build envelope
        import math
        total_pages = math.ceil(total / per_page) if per_page else 0
        return PagedResponse[BookListOut](
            content=[BookListOut.model_validate(b) for b in books],
            page=page,
            size=per_page,
            totalElements=total,
            totalPages=total_pages,
            sort=sort_clause,
        )

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

@router.get("/{book_id}/cover")
async def get_cover(book_id: str, storage: BlobStorage = Depends(get_storage_dep)):
    # Prefer storage abstraction first
    try:
        blob = await storage.get_blob(book_id)
        if blob:
            logger.debug("Blob storage returned data for book_id=%s", book_id)
            return Response(content=blob, media_type="application/octet-stream")
    except Exception:
        logger.exception("Error fetching blob from storage for book_id=%s", book_id)
        pass
    # fallback to DB-stored blob or filesystem path
    async with get_session() as session:
        book = await session.get(Book, book_id)
        if not book:
            logger.info("Book not found for cover fetch: %s", book_id)
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

@router.put("/{book_id}", response_model=BookOut)
async def update_book(book_id: str, book_in: BookIn, current_user: User = Depends(get_current_user)):
    if getattr(current_user, 'type', 0) != 1:
        logger.warning("Unauthorized book update attempt by user id=%s", getattr(current_user, 'id', None))
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            logger.info("Book not found for update: %s", book_id)
            raise HTTPException(status_code=404, detail="Book not found")
        b.title = book_in.title
        b.author_id = book_in.author_id
        b.isbn = book_in.isbn
        b.description = book_in.description
        session.add(b)
        await session.commit()
        await session.refresh(b)
        logger.info("Book updated id=%s title=%s by user id=%s", b.id, b.title, getattr(current_user, 'id', None))
        return BookOut.model_validate(b)

@router.patch("/{book_id}", response_model=BookOut)
async def patch_book(book_id: str, book_in: BookIn, current_user: User = Depends(get_current_user)):
    if getattr(current_user, 'type', 0) != 1:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        if book_in.title:
            b.title = book_in.title
        if book_in.author_id is not None:
            b.author_id = book_in.author_id
        if book_in.isbn is not None:
            b.isbn = book_in.isbn
        if book_in.description is not None:
            b.description = book_in.description
        session.add(b)
        await session.commit()
        await session.refresh(b)
        return BookOut.model_validate(b)

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
            book.cover_path = None
        else:
            book.cover_path = result
            book.cover = None
        session.add(book)
        await session.commit()
        await session.refresh(book)
        logging.getLogger(__name__).info("After upload - book.cover_path=%s, book.cover is %s", getattr(book, 'cover_path', None), 'set' if getattr(book,'cover',None) else 'none')
        return {"ok": True, "book_id": book_id}
