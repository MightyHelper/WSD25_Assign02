import logging

from fastapi import APIRouter, HTTPException, status, Response, Depends
from pydantic import BaseModel

from app.db.base import get_session
from app.db.models import Author, User
from app.schemas.pagination import PagedResponse
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])
logger = logging.getLogger('app.api.authors')

class AuthorIn(BaseModel):
    id: str
    name: str

    model_config = {"extra": "ignore", "from_attributes": True}

class AuthorOut(BaseModel):
    id: str
    name: str

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=AuthorOut, status_code=status.HTTP_201_CREATED)
async def create_author(author_in: AuthorIn, current_user: User = Depends(get_current_user)):
    # only admins can create authors
    if getattr(current_user, 'type', 0) != 1:
        logger.warning("Unauthorized author create attempt by user id=%s", getattr(current_user, 'id', None))
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        a = Author(id=author_in.id, name=author_in.name)
        session.add(a)
        await session.commit()
        await session.refresh(a)
        logger.info("Author created id=%s name=%s by user id=%s", a.id, a.name, getattr(current_user, 'id', None))
        return AuthorOut.model_validate(a)

@router.get("/{author_id}", response_model=AuthorOut)
async def get_author(author_id: str):
    async with get_session() as session:
        a = await session.get(Author, author_id)
        if not a:
            logger.info("Author not found: %s", author_id)
            raise HTTPException(status_code=404, detail="Author not found")
        logger.debug("Returning author id=%s name=%s", a.id, a.name)
        return AuthorOut.model_validate(a)

@router.get("/", response_model=PagedResponse[AuthorOut])
async def list_authors(response: Response, page: int = 1, per_page: int = 20, name: str | None = None, sort_by: str | None = None, sort_dir: str = "asc"):
    async with get_session() as session:
        from sqlalchemy import select, asc, desc, func
        stmt = select(Author)
        if name:
            stmt = stmt.where(Author.name.ilike(f"%{name}%"))
        # total count
        count_stmt = select(func.count()).select_from(Author)
        if name:
            count_stmt = count_stmt.where(Author.name.ilike(f"%{name}%"))
        res = await session.execute(count_stmt)
        total = int(res.scalar_one())
        # ordering
        sort_clause = None
        if sort_by and hasattr(Author, sort_by):
            col = getattr(Author, sort_by)
            sort_clause = f"{sort_by},{sort_dir}"
            if sort_dir and sort_dir.lower().startswith("desc"):
                stmt = stmt.order_by(desc(col))
            else:
                stmt = stmt.order_by(asc(col))
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        res = await session.execute(stmt)
        authors = res.scalars().all()
        # set headers for backward compatibility
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(per_page)
        # envelope
        import math
        total_pages = math.ceil(total / per_page) if per_page else 0
        return PagedResponse[AuthorOut](
            content=[AuthorOut.model_validate(a) for a in authors],
            page=page,
            size=per_page,
            totalElements=total,
            totalPages=total_pages,
            sort=sort_clause,
        )

@router.put("/{author_id}", response_model=AuthorOut)
async def update_author(author_id: str, author_in: AuthorIn, current_user: User = Depends(get_current_user)):
    if getattr(current_user, 'type', 0) != 1:
        logger.warning("Unauthorized author update attempt by user id=%s", getattr(current_user, 'id', None))
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        a = await session.get(Author, author_id)
        if not a:
            logger.info("Author not found for update: %s", author_id)
            raise HTTPException(status_code=404, detail="Author not found")
        a.name = author_in.name
        session.add(a)
        await session.commit()
        await session.refresh(a)
        logger.info("Author updated id=%s name=%s by user id=%s", a.id, a.name, getattr(current_user, 'id', None))
        return AuthorOut.model_validate(a)

@router.patch("/{author_id}", response_model=AuthorOut)
async def patch_author(author_id: str, author_in: AuthorIn, current_user: User = Depends(get_current_user)):
    # same admin check
    if getattr(current_user, 'type', 0) != 1:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    async with get_session() as session:
        a = await session.get(Author, author_id)
        if not a:
            raise HTTPException(status_code=404, detail="Author not found")
        if author_in.name:
            a.name = author_in.name
        session.add(a)
        await session.commit()
        await session.refresh(a)
        return AuthorOut.model_validate(a)
