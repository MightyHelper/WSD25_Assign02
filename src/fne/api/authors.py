from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel
from app.db.models import Author
from app.db.base import get_session

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])

class AuthorIn(BaseModel):
    id: str
    name: str

    model_config = {"extra": "ignore", "from_attributes": True}

class AuthorOut(BaseModel):
    id: str
    name: str

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=AuthorOut, status_code=status.HTTP_201_CREATED)
async def create_author(author_in: AuthorIn):
    async with get_session() as session:
        a = Author(id=author_in.id, name=author_in.name)
        session.add(a)
        await session.commit()
        await session.refresh(a)
        return AuthorOut.model_validate(a)

@router.get("/{author_id}", response_model=AuthorOut)
async def get_author(author_id: str):
    async with get_session() as session:
        a = await session.get(Author, author_id)
        if not a:
            raise HTTPException(status_code=404, detail="Author not found")
        return AuthorOut.model_validate(a)
