import pytest
import asyncio
from httpx import AsyncClient
from app.main import create_app

@pytest.fixture(scope="module")
async def test_app():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

