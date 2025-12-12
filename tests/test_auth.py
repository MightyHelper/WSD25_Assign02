import pytest
import uuid

def test_login_returns_token(test_app):
    payload = {"username": "anyuser", "password": "anypass"}
    r = test_app.post("/api/v1/auth/login", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
