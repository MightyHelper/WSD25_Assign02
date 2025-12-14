import os
import pathlib
import pytest
from fastapi.testclient import TestClient

# ensure test environment variables are set before importing the application
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
# avoid initializing redis during tests unless explicitly provided
os.environ.setdefault("REDIS_URL", "")
# provide PEPPER used by security settings during tests
os.environ.setdefault("PEPPER", "tests-pepper")
# mark environment as test so runtime code can reset DB between tests when needed
os.environ.setdefault("APP_ENV", "test")

from app.main import create_app


@pytest.fixture(scope="function")
def test_app() -> TestClient:
    # ensure a clean sqlite DB for this test
    db_path = pathlib.Path("./test_db.sqlite")
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    app = create_app()
    with TestClient(app) as client:
        yield client
