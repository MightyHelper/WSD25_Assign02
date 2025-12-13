"""Run as: python scripts/seed.py
Creates basic authors, books and sample users. Uses app config DATABASE_URL.
"""
from sqlalchemy.exc import IntegrityError

from app.db.base import init_db, create_tables, get_session
from app.db.models import Author, Book, User
from app.security.password import hash_password
from app.config import settings
import asyncio
import uuid

SAMPLE_AUTHORS: list[str] = ["Jane Austen", "Mark Twain", "George Orwell"]
SAMPLE_BOOKS: list[tuple[str, str]] = [
    ("Pride and Prejudice", "A classic novel."),
    ("Adventures of Huckleberry Finn", "A novel about a boy on a raft."),
    ("1984", "Dystopian classic."),
]

SAMPLE_USERS: list[tuple[str, str, str]] = [
    ("seeduser", "seed@example.com", "password"),
    ("alice", "alice@example.com", "alicepw"),
    ("bob", "bob@example.com", "bobpw"),
]


async def seed() -> None:
    # determine dsn from app settings (fall back to local dev DB)
    dsn = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"
    print("dsn", dsn)
    await init_db(dsn)
    await create_tables()
    async with get_session() as session:
        # create authors
        authors: list[Author] = []
        for name in SAMPLE_AUTHORS:
            a = Author(id=str(uuid.uuid4()), name=name)
            session.add(a)
            authors.append(a)
        await session.commit()

        # create books
        # refresh first author to ensure FK available
        if authors:
            await session.refresh(authors[0])
        for i, (title, desc) in enumerate(SAMPLE_BOOKS):
            a = authors[min(i, len(authors) - 1)] if authors else None
            b = Book(id=str(uuid.uuid4()), title=title, description=desc, author_id=(a.id if a else None))
            session.add(b)

        # create sample users
        for username, email, pw in SAMPLE_USERS:
            u = User(id=str(uuid.uuid4()), username=username, email=email, password_hash=hash_password(pw))
            session.add(u)
        try:
            await session.commit()
        except IntegrityError:
            print(f"Conflicts while seeind, is the db already seeded?")

if __name__ == "__main__":
    asyncio.run(seed())
    print("Seeding complete.")
