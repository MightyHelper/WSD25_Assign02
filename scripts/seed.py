"""Run as: python scripts/seed.py
Creates basic authors, books and sample users. Uses app config DATABASE_URL.
"""

import csv
import os
import random

import httpx
from sqlalchemy.exc import IntegrityError

from app.db.base import init_db, create_tables, get_session, close_db
from app.db.models import Author, Book, User
from app.security.password import hash_password
from app.config import settings
import asyncio
import uuid

SAMPLE_USERS: list[tuple[str, str, str, int]] = [
    (os.environ["ADMIN_USER"], os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"], 1)
]

covers = os.listdir("scripts/covers")


async def seed_books():
    data = csv.reader(open("scripts/data.csv", encoding="utf-8"))
    next(data)  # skip header
    authors_cache: dict[str, Author] = {}
    http_client = httpx.Client()
    base_url = os.environ["BASE_URL"]
    login = http_client.post(
        f"{base_url}/api/v1/auth/login",
        content=f'{{"username":"{os.environ["ADMIN_USER"]}","password":"{os.environ["ADMIN_PASSWORD"]}"}}',
        headers={"Content-Type": "application/json"},
    ).json()
    token = login["access_token"]
    print("Seeding books...")

    async with get_session() as session:
        for row in data:
            (
                pub_year,
                book_name,
                author_name,
                lang_code,
                author_rating,
                book_avg_rating,
                book_ratings_count,
                genre,
                gross_sales,
                publisher_revenue,
                sale_price,
                sale_rank,
                publisher,
                units_sold,
            ) = row
            if author_name not in authors_cache:
                author = Author(id=str(uuid.uuid4()), name=author_name[:200])
                authors_cache[author_name] = author
            else:
                author = authors_cache[author_name]
            book = Book(
                id=str(uuid.uuid4()),
                title=book_name[:200],
                isbn=str(uuid.uuid4()),  # Random ISBN for seeding
                author_id=author.id,
            )
            session.add(author)
            session.add(book)

        await session.commit()

    data = csv.reader(open("scripts/data.csv", encoding="utf-8"))
    next(data)  # skip header

    for i, row in enumerate(data):
        (
            pub_year,
            book_name,
            author_name,
            lang_code,
            author_rating,
            book_avg_rating,
            book_ratings_count,
            genre,
            gross_sales,
            publisher_revenue,
            sale_price,
            sale_rank,
            publisher,
            units_sold,
        ) = row
        print("Uploading cover for book:", book_name)
        if random.randint(0, 100) > 80:  # ~20% books get covers
            cover_data = open(f"scripts/covers/{covers[hash(book_name) % len(covers)]}", "rb").read()
            print(len(cover_data), "bytes")
            http_client.request(
                "POST",
                f"{base_url}/api/v1/books/{book.id}/cover",
                content=cover_data,
                headers={"Content-Type": "application/octet-stream", "Authorization": f"Bearer {token}"},
            ).json()


async def seed_admin():
    async with get_session() as session:
        # create sample users
        for username, email, pw, typ in SAMPLE_USERS:
            u = User(id=str(uuid.uuid4()), username=username, email=email, password_hash=hash_password(pw), type=typ)
            session.add(u)
        try:
            await session.commit()
        except IntegrityError:
            print(f"Conflicts while seeind, is the db already seeded?")


async def seed() -> None:
    # determine dsn from app settings (fall back to local dev DB)
    dsn = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"
    print("dsn", dsn)
    await init_db(dsn)
    print("Creating tables.")
    await create_tables()
    print("Creating admin.")
    await seed_admin()
    print("Seeding books.")
    await seed_books()
    await close_db()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
