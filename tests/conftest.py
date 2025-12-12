import os
import pathlib

# ensure a clean sqlite DB for tests
db_path = pathlib.Path("./test_db.sqlite")
if db_path.exists():
    try:
        db_path.unlink()
    except Exception:
        pass

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
# avoid initializing redis during tests unless explicitly provided
os.environ.setdefault("REDIS_URL", "")

from fastapi.testclient import TestClient
import pytest

from app.main import create_app

@pytest.fixture(scope="module")
def test_app() -> TestClient:
    app = create_app()
    with TestClient(app) as client:
        yield client
