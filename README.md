# Project

A production-minded FastAPI + SQLAlchemy project scaffold implementing the Assignment 2 requirements (DB-backed REST API, JWT auth, RBAC, pagination/search/sort, OpenAPI docs, migrations & seeds, logging, rate limiting, and tests).

This repository contains a complete server prototype and developer tooling aimed at delivering a deployable service for the assignment.
Status
- Purpose: Teaching / assignment scaffold and reference implementation.
- Stage: Established prototype with application structure, standards, and tooling in place (migrations, tests, docs). You may need to adapt a few environment-specific values before running.

Key features
- FastAPI-based HTTP API with automatic OpenAPI/Swagger documentation.
- SQLAlchemy ORM with Alembic migrations (MySQL target by default).
- JWT authentication with role-based access control (ROLE_USER=0, ROLE_ADMIN=1).
- Pagination, sorting and search utilities for list endpoints.
- Docker-friendly (multi-stage Dockerfile) and test suite (pytest).
- Metrics using Prometheus!
- Redis caching support!

## Playground

See http://113.198.66.75:18083/docs for a live demo of the API.

- Health: http://113.198.66.75:18083/health
- MysqlDB at: http://113.198.66.75:10083/
- See metrics at: http://113.198.66.75:18083/metrics
- Grafana: http://localhost:3000/goto/bf730c2c875kwd?orgId=1

Credentials provided upon reasonable request to federicowilliamson@hotmail.co.uk.


## Quickstart (local development)

1) Prerequisites
- Python, tested with 3.13.9
- Recommended: create an isolated virtual environment.

2) Create & activate a venv
```sh
uv sync
```

3) Environment configuration
- Configure settings from app.config.Settings
- You may use a `.env` file
- Env vars take precedence over `.env` values

4) Running the app with Docker (quick)
- The repository contains a multi-stage `Dockerfile` and `docker-compose.yml` in the `project/` folder. Build and run with:
```
docker-compose up --build
```
This will start the application and the database (if `docker-compose.yml` wires one up).

5) Seed the DB

Run `python scripts/seed_db.py`. It expects the DB creds/url from the env vars or `.env` file.

Seeding will also require the ADMIN_USER, ADMIN_PASSWORD and ADMIN_EMAIL via en to create as this depends on each environment.

## API documentation & Postman
- OpenAPI/Swagger UI: `/docs` or `/redoc` (configured in the app factory). Example:
  - http://localhost:8080/docs
- Postman collection: check the `postman/` directory for `<project>.postman_collection.json` and an environment file.
  - The collection includes pre-request scripts to store tokens and a few tests; configure the base URL in the environment.

## Authentication
- Auth endpoints:
  - `POST /auth/login` – produce access token (JWT)
  - `POST /auth/refresh` – refresh token
  - `POST /auth/logout` – invalidate token / logical logout

Testing
- Run the test suite with pytest (or use tox if configured):
```
pytest -q
```
- Tests cover authentication flows, authorization checks (401/403), validation errors (400/422), CRUD endpoints, and some integration paths.

Health checks & monitoring
- Health endpoint (no auth): `GET /health` → returns 200 and app metadata (version, build time).
- Logging: request and response summary logs include method, path, status, and latency.

