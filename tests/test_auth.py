import pytest
import uuid


def test_login_returns_token(test_app):
    # create user first
    user_id = str(uuid.uuid4())
    username = "anyuser"
    password = "anypass"
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": username, "email": f"{user_id}@example.com", "password": password})
    assert r.status_code == 201

    payload = {"username": username, "password": password}
    r = test_app.post("/api/v1/auth/login", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
