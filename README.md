# Assignment 2 - Project scaffold

This folder contains an async FastAPI project scaffold for Assignment 2.

Quick start (using Docker Compose):

```bash
# copy .env.example → .env and edit values
cp .env.example .env

docker compose up --build
```

The API will be available at http://localhost:8000 and docs at /docs

Notes:
- The scaffold uses async SQLAlchemy (aiomysql) and Redis (redis.asyncio).
- For local development without Docker, configure a local MySQL instance and Redis and set `DATABASE_URL` and `REDIS_URL` in the environment.

