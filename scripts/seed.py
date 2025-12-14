"""Run as: python scripts/seed.py
Creates basic authors, books and sample users. Uses app config DATABASE_URL.
"""
import csv
import os

from sqlalchemy.exc import IntegrityError

from app.db.base import init_db, create_tables, get_session
from app.db.models import Author, Book, User
from app.security.password import hash_password
from app.config import settings
import asyncio
import uuid

from app.storage import get_storage

SAMPLE_USERS: list[tuple[str, str, str, int]] = [
    (os.environ["ADMIN_USER"], os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"], 1)
]

# Read data.csv with format:
# Publishing_Year,Book_Name,Author,Language_Code,Author_Rating,Book_Average_Rating,Book_Ratings_Count,Genre,Gross_Sales,Publisher_Revenue,Sale_Price,Sale_Rank,Publisher,Units_Sold

covers = os.listdir("scripts/covers")


async def seed_books():
    data = csv.reader(open("scripts/data.csv"))
    next(data)  # skip header
    authors_cache: dict[str, Author] = {}
    storage = get_storage()
    async with get_session() as session:
        for row in data:
            pub_year, book_name, author_name, lang_code, author_rating, book_avg_rating, book_ratings_count, genre, gross_sales, publisher_revenue, sale_price, sale_rank, publisher, units_sold = row
            if author_name not in authors_cache:
                author = Author(id=str(uuid.uuid4()), name=author_name)
                authors_cache[author_name] = author
            else:
                author = authors_cache[author_name]
            book = Book(
                id=str(uuid.uuid4()),
                title=book_name,
                isbn=str(uuid.uuid4()), # Random ISBN for seeding
                author_id=author.id,
            )
            session.add(author)
            session.add(book)
            if hash(book_name) % 100 > 80:  # ~20% books get covers
                await storage.save_cover(
                    book.id,
                    open(f"scripts/covers/{covers[hash(book_name) % len(covers)]}", "rb").read(),
                )
        session.commit()


async def seed() -> None:
    # determine dsn from app settings (fall back to local dev DB)
    dsn = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"
    print("dsn", dsn)
    await init_db(dsn)
    await create_tables()
    await seed_books()
    async with get_session() as session:
        # create sample users
        for username, email, pw, typ in SAMPLE_USERS:
            u = User(id=str(uuid.uuid4()), username=username, email=email, password_hash=hash_password(pw), type=typ)
            session.add(u)
        try:
            await session.commit()
        except IntegrityError:
            print(f"Conflicts while seeind, is the db already seeded?")


if __name__ == "__main__":
    asyncio.run(seed())
    print("Seeding complete.")
