# Project (dev)

Development notes

- To run tests locally: python -m pytest
- To run the app locally (dev):
  - Ensure a `.env` exists with PEPPER set (for example: `PEPPER=dev-pepper`)
  - Start with: python -m uvicorn app.main:app --reload

Docker

- The included `docker-compose.yml` will start the app, MariaDB and Redis.
- You must provide an environment variable `PEPPER` when running docker-compose. Example:

  PEPPER=my-secret-pepper docker compose up --build

Seeding

- A simple seeding script is provided at `scripts/seed.py`. Run it after the app DB is up to create sample authors/books and a user:

  python scripts/seed.py

Notes

- Storage kind is configurable via `STORAGE_KIND` config (fs or db). Local dev defaults to `fs` (filesystem).
- Cover images are stored either as blobs in DB or as files in `uploads/` and referenced by `book.cover_path`.

