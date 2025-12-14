# Project (dev)

Development notes

This project contains a FastAPI application plus test-suite. The README below documents how to run the tests, which environment variables matter during development and testing, and a few notes about DB lifecycle and storage.

## Quick start - run the tests

1. Open PowerShell and activate the project's virtualenv (the environment may already be active in some setups).
2. Change to the project directory (if not already there):

   ```powershell
   cd C:\Users\User\Nextcloud\fede\Github\JBNU\WSD\Assignment02\project
   ```

3. Run the full test suite:

   ```powershell
   pytest -q
   ```

## Notes about environment variables used in tests and development

- `PEPPER` (required in production-like flows) — application uses a PEPPER secret when hashing passwords. Tests set a safe default (`tests-pepper`) automatically in `tests/conftest.py` to make the test-suite runnable out of the box, but for any manual runs you may want to set it explicitly (for example when running the app with uvicorn):

  ```powershell
  $env:PEPPER = "your-secret-pepper"
  ```

- `DATABASE_URL` — defaults to an sqlite async URL when not provided. Example (for a local sqlite test DB):

  ```powershell
  $env:DATABASE_URL = "sqlite+aiosqlite:///./test_db.sqlite"
  ```

- `REDIS_URL` — tests set this to empty by default to avoid trying to connect to Redis. If you need Redis for integration runs, set this to your Redis URL.

## Database / test lifecycle behavior (important)

- The test and application startup logic ensures the DB tables exist, but it does *not* drop tables on app startup. This is intentional so tests that create DB fixtures before creating the FastAPI app (a common pattern in these tests) don't lose their data when the app starts.
- If you need a completely clean DB before a test run, remove the `test_db.sqlite` file (or run a dedicated script that drops tables). The test fixtures and `create_tables` helper will create missing tables.

## Running the app locally (dev)

- To run the app interactively (development) with uvicorn:

  ```powershell
  # set PEPPER in your environment first
  $env:PEPPER = "dev-pepper"
  python -m uvicorn app.main:create_app --reload
  ```

- Alternatively you can run the app via docker-compose (the included `docker-compose.yml` starts the app plus MariaDB and Redis). When using docker-compose ensure you provide `PEPPER` in the environment for the container.

## Storage behavior

- Storage kind is configurable via `STORAGE_KIND` (`fs` or `db`). Local dev defaults to `fs`.
- `fs` mode stores cover images on the filesystem under `uploads/` and stores a `book.cover_path` value.
- `db` mode stores raw blobs on the `books.cover` DB column.

## Tests and repository hygiene

- Debug/inspection scripts that were used during development have been cleaned up or converted to placeholders. There remain a set of small helper scripts under `scripts/` used for local inspection; feel free to remove them if you prefer a minimal repository.
- I added auth-focused tests (positive and negative cases) to ensure authentication edge-cases are covered (register/login, token decoding, tampered and expired tokens, wrong scheme, invalid signatures).

## If something fails

- First, ensure the virtualenv is active and dependencies are installed. If pytest is missing, install the project's test requirements.
- Confirm you are running tests from the `project` directory.
- If DB state is causing issues, remove `test_db.sqlite` to force a fresh DB on next test run.

## Contact

- If you want, I can tidy the helper scripts, create a small `Makefile` or `invoke` tasks to simplify running tests and cleaning state, or open a commit/PR with these changes.
