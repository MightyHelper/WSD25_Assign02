# Project Guidelines (FastAPI + SQLAlchemy, Python 3.13.9)

These are the rules I will follow when creating the new project under `project/`.
They are based on:
- The style and quality of the `demo/` FastAPI project
- The assignment requirements in `instructions.md`
- Modern Python 3.13.9 and SQLAlchemy best practices

## 1. Tech stack & high-level principles

- **Language**: Python `3.13.9` (type-hinted, mypy-friendly, modern features only).
- **Web framework**: FastAPI.
- **ORM**: SQLAlchemy 2.x (declarative, async or sync pattern chosen per design; default to sync + async endpoints via threadpool unless explicitly required otherwise).
- **DB**: MySQL, accessed via SQLAlchemy with Alembic for migrations.
- **Auth**: JWT-based authentication + role-based authorization (at least `ROLE_USER`, `ROLE_ADMIN`).
- **Style baseline**: match the structure, naming, and patterns from `demo/` **unless** in direct conflict with `instructions.md`.

Key principles:
- Clear separation of concerns (API layer, schemas, domain/services, persistence, config).
- Consistent response and error formats across all endpoints.
- Strong typing and validation at the edges (Pydantic in/out models; enums/`Literal` where appropriate).
- Tests and docs treated as first-class citizens.

## 2. Project layout

Under `project/` I will use a structure analogous to `demo/` but extended for DB + auth:

- `project/`
  - `pyproject.toml` – dependencies, tool config.
  - `Dockerfile` – multi-stage build (builder + runtime) similar to `demo/`.
  - `README.md` – assignment-focused readme (deploy info, how to run, etc.).
  - `.env.example` – environment variable template (no secrets).
  - `requirements-test.txt` – extra test-only dependencies.
  - `scripts/` – DB migration/seed helpers (e.g. `alembic/`, seed scripts).
  - `docs/` – mirrors assignment doc layout (`api-design.md`, `db-schema.*`, `architecture.md`).
  - `postman/` – Postman collection JSON.
  - `src/`
    - `<package_name>/` (e.g. `app/`)
      - `__init__.py`
      - `main.py` – FastAPI app factory and wiring (similar to `demo`'s `create_app`).
      - `config.py` – settings loaded from env (DB URL, JWT secrets, etc.).
      - `constants.py` – API metadata, defaults, limits, and static messages.
      - `errors.py` – custom exceptions + error codes.
      - `state.py` – any in-memory state (for rate limiting, health meta, etc.).
      - `logging_config.py` (optional) – structured logging setup.
      - `db/`
        - `base.py` – SQLAlchemy engine/session setup and declarative base.
        - `models/` – ORM models by domain (`user.py`, `post.py`, etc.).
        - `repositories/` – DB access layer (CRUD, queries, pagination helpers).
      - `security/`
        - `jwt.py` – token generation/verification utilities.
        - `dependencies.py` – `get_current_user`, role checking, etc.
        - `password.py` – password hashing/verification.
      - `middleware/`
        - `__init__.py`
        - `logging_middleware.py` – copy style from `demo`.
        - `rate_limit_middleware.py` – copy/adapt from `demo`.
      - `schemas/` (Pydantic models)
        - `auth.py`, `user.py`, `post.py`, `comment.py`, etc.
        - Separate request/response models where helpful (but keep naming clear).
      - `api/`
        - `routes_*.py` files grouped by resource (or a folder with routers).
      - `response/`
        - `api_response.py` – success envelope (generic `APIResponse[T]`).
        - `json_error.py` – standardized error envelope, similar to `JSONProblem` but aligned with `instructions.md` format.
  - `tests/`
    - `conftest.py` – app/test client fixture, test DB fixture, auth helpers.
    - `test_auth_*.py`, `test_users_*.py`, `test_posts_*.py`, etc.

## 3. FastAPI app style (following `demo`)

- Use an **application factory** in `main.py`:

  ```python
  def create_app(enable_rate_limiting: bool = True) -> FastAPI:
      ...
  ```

- Configure app metadata from `constants.py`:
  - `API_TITLE`, `API_DESCRIPTION`, `API_VERSION`.
  - `docs_url` and `redoc_url` explicitly set.

- Register middleware in the same pattern as `demo`:
  - `LoggingMiddleware` always enabled.
  - `RateLimitMiddleware` toggled by parameter (disabled in tests).

- Register exception handlers at startup for:
  - Custom `APIError` subclasses.
  - `HTTPException`.
  - `RequestValidationError`.
  - Generic `Exception` (fallback).

- Prefer **router modules** (`APIRouter`) mounted under `/api` or similar, but keep the ergonomics and simplicity of `demo` (flat endpoints in `main.py`) if that proves clearer.

## 4. Responses & error handling (aligned with instructions.md)

**Success wrapper**

- Use a generic response envelope similar to `demo`'s `APIResponse[T]`, but we will keep its fields consistent across the project:

  ```python
  class APIResponse[T](BaseModel):
      status: int         # HTTP status code as integer
      data: T
  ```

- All successful endpoints return `APIResponse[...]` models serialized via `.model_dump()`.

**Error response format**

- Follow the assignment's standard error JSON:

  ```json
  {
    "timestamp": "2025-03-05T12:34:56Z",
    "path": "/api/posts/1",
    "status": 400,
    "code": "POST_TITLE_TOO_LONG",
    "message": "...",
    "details": { ... }
  }
  ```

- Implement an error model `JSONError` (or similar) in `response/json_error.py`:
  - `timestamp: datetime`
  - `path: str`
  - `status: int`
  - `code: str`
  - `message: str`
  - `details: dict[str, Any] | None`

- Define at least 10 canonical error codes (from `instructions.md`) in `constants.py` or `errors.py` and map exceptions to them.

- Exception handling rules:
  - All custom exceptions inherit from a base `APIError` that carries `http_status`, `code`, `message`, and optional `details`.
  - Global exception handlers translate `APIError`, `HTTPException`, `RequestValidationError`, and unknown exceptions into `JSONError` responses.
  - Swagger docs include example error responses for relevant status codes.

## 5. ORM, DB, and migrations

- Use **SQLAlchemy 2.x** with the declarative ORM API.
- Use **Alembic** for migrations (via `alembic/` directory and env script wired to SQLAlchemy metadata).
- Use **MySQL** as required, driven by an env-configured DSN (e.g. `MYSQL_DSN` or `DATABASE_URL`).
- Model design:
  - Follow the ERD and `mysql_create.sql` from `HandIn`.
  - Use explicit FKs and indexes where appropriate.
  - Represent relationships (`relationship()`) with lazy/eager loading specified to avoid N+1 issues.
- Seed data:
  - Provide a script or command to insert at least 200 rows across tables.
  - Prefer idempotent or clearly-marked one-shot seeders.

## 6. Authentication & authorization

- Implement JWT-based auth using PyJWT or a modern equivalent.
- Store tokens in headers as `Authorization: Bearer <token>`.
- Implement endpoints at least:
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout` (logical logout; may be token blacklist or rotation).
- User model includes:
  - Unique username or email.
  - Hashed password (using `bcrypt` or Argon2).
  - Role field (`ROLE_USER`, `ROLE_ADMIN`, possibly more) using `Enum`.
- Security dependencies:
  - `get_current_user` dependency extracts and validates JWT.
  - `require_role(role: Role)` or similar to enforce RBAC in routes.
- At least 3 admin-only endpoints (e.g., list users, deactivate users, view statistics).

## 7. API design, pagination, search, sorting

- Implement at least 4 core resources (e.g., `auth`, `users`, `posts`, `comments`, `categories` or similar), each with full CRUD, excluding `auth` which only handles authentication.
- Total endpoint count: **30+** distinct method+path combinations.
- For list endpoints:
  - Support `page`, `size` (with defaults and max values defined in `constants.py`).
  - Support sorting via `sort=field,ASC|DESC` convention.
  - Support at least two filter/search conditions (e.g., `keyword`, `category`, `dateFrom/dateTo`).
- List responses follow:

  ```json
  {
    "content": [ ... ],
    "page": 0,
    "size": 20,
    "totalElements": 153,
    "totalPages": 8,
    "sort": "createdAt,DESC"
  }
  ```

- Pagination and query parsing logic lives in a small helper module (e.g., `utils/pagination.py`) and is reused across handlers.

## 8. Middleware, logging, and rate limiting

- Reuse the **style** of `demo` middleware:
  - `LoggingMiddleware` logs method, path, status code, and latency.
  - `RateLimitMiddleware` maintains per-IP request timestamps and a blacklist in `State`.

- Adapt `RateLimitMiddleware` to the new project:
  - Exclude documentation endpoints and optionally health check from rate limits.
  - Configure all thresholds and durations in `constants.py`.

- Logging:
  - Configure global logging with `logging.basicConfig` in `main.py` (or dedicated config module).
  - Use module-level loggers (`logging.getLogger(__name__)`).

## 9. Testing

- Use `pytest` + `httpx`/`fastapi.testclient` to implement at least **20 automated tests**.
- Organize tests by feature:
  - `test_auth.py`, `test_users.py`, `test_posts.py`, `test_comments.py`, etc.
- Include both success and failure paths:
  - Auth failures (401, 403).
  - Validation errors (400/422).
  - Not found (404).
  - Conflict (409).
- Reuse fixture pattern from `demo/tests/conftest.py`:
  - App/test client fixture (with rate limiting disabled).
  - Auth helper fixtures for user and admin tokens.
  - Test DB session/transaction per test module or function.

## 10. Docker & deployment

- Dockerfile will:
  - Use `python:3.13-slim` as base.
  - Follow a **multi-stage** pattern like `demo` (builder + runtime).
  - Install dependencies from `pyproject.toml`.
  - Run the app with `uvicorn` (module path adjusted to this project).
  - Use a non-root user in runtime.

- Environment variables will be injected at run time (DB URL, JWT secret, etc.), with `.env.example` documenting required keys.

## 11. Documentation & Postman

- Enable FastAPI's automatic OpenAPI/Swagger docs (`/docs`, `/redoc`).
- Add description, tags, and summary strings to endpoints to produce meaningful docs.
- Provide example requests/responses (especially error cases) via Pydantic examples or docstrings.
- Provide a Postman collection in `postman/` with:
  - Environment variables for base URL and tokens.
  - At least 5 pre-request or test scripts (e.g., storing/using JWTs, asserting status codes).

## 12. Python 3.13.9 specifics

- Prefer **modern typing features**:
  - `list[int]`, `dict[str, Any]` instead of `List`, `Dict`.
  - `Self` from `typing` for fluent APIs.
  - `Final`, `Literal`, and `Enum` for constrained domains.
- Use pattern matching only where it clearly improves readability.
- Avoid deprecated APIs; follow current FastAPI and SQLAlchemy recommendations for Python 3.11+ (fully compatible with 3.13.9).

---

These guidelines are the contract for the new project under `project/`. When in doubt, I will:
1. Prefer the **style and structure** of `demo`.
2. Ensure I am **not** violating explicit requirements from `instructions.md`.
3. Keep the code type-safe, well-tested, and easy to understand.
