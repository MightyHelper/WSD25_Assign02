from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel
from app.db.models import Book
from app.db.base import get_session
from ..storage import get_storage_dep, BlobStorage
from app.redis_client import get_redis_dep

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

@router.put("/{book_id}", response_model=BookOut)
async def update_book(book_id: str, book_in: BookIn, redis=Depends(get_redis_dep)):
    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        b.title = book_in.title
        b.author_id = book_in.author_id
        b.isbn = book_in.isbn
        b.description = book_in.description
        session.add(b)
        await session.commit()
        await session.refresh(b)
        # invalidate cache
        await redis.delete(f"book:{book_id}")
        return BookOut.model_validate(b)

@router.delete("/{book_id}")
async def delete_book(book_id: str, redis=Depends(get_redis_dep)):
    async with get_session() as session:
        b = await session.get(Book, book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        await session.delete(b)
        await session.commit()
        await redis.delete(f"book:{book_id}")
        return Response(status_code=status.HTTP_200_OK)

# Blob endpoints
@router.put("/{book_id}/cover", status_code=status.HTTP_200_OK)
async def upload_cover(book_id: str, request: Request, storage: BlobStorage = Depends(get_storage_dep)):
    data = await request.body()
    try:
        await storage.save_blob(book_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"ok": True}

@router.get("/{book_id}/cover")
async def get_cover(book_id: str, storage: BlobStorage = Depends(get_storage_dep)):
    blob = await storage.get_blob(book_id)
    if not blob:
        raise HTTPException(status_code=404, detail="Cover not found")
    return Response(content=blob, media_type="application/octet-stream")
