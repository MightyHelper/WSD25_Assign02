import asyncio
import uuid
import os
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine

# Use env DATABASE_URL if available
DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite+aiosqlite:///./dev_seed.db"

from fne.db.models import Base, Author, Book, User, UserBookReview

async def create_tables(engine_url: str):
    engine = create_async_engine(engine_url, future=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

async def seed_sample(engine_url: str):
    engine = create_async_engine(engine_url, future=True, echo=False)
    async with engine.begin() as conn:
        # use connection to insert
        # create authors
        authors = []
        for i in range(1, 51):
            authors.append({"id": str(uuid.uuid4()), "name": f"Author {i}"})
        await conn.execute(Author.__table__.insert(), authors)

        # create books (100)
        books = []
        for i in range(1, 101):
            author = authors[(i - 1) % len(authors)]
            books.append({"id": str(uuid.uuid4()), "title": f"Sample Book {i}", "author_id": author["id"], "isbn": f"ISBN-{i}", "description": f"Description {i}"})
        await conn.execute(Book.__table__.insert(), books)

        # create users (40)
        users = []
        for i in range(1, 41):
            users.append({"id": str(uuid.uuid4()), "username": f"user{i}", "email": f"user{i}@example.com", "password_hash": "seeded"})
        await conn.execute(User.__table__.insert(), users)

        # create reviews (10)
        reviews = []
        for i in range(1, 11):
            book = books[(i - 1) % len(books)]
            user = users[(i - 1) % len(users)]
            reviews.append({"id": str(uuid.uuid4()), "book_id": book["id"], "user_id": user["id"], "title": f"Review {i}", "content": f"Review content {i}"})
        await conn.execute(UserBookReview.__table__.insert(), reviews)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables(DATABASE_URL))
    asyncio.run(seed_sample(DATABASE_URL))
    print("Seeded sample data into", DATABASE_URL)
