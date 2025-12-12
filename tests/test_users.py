import pytest
import uuid

def test_create_get_user(test_app):
    user_id = str(uuid.uuid4())
    payload = {"id": user_id, "username": "testuser", "email": "test@example.com", "password": "pass"}
    r = test_app.post("/api/v1/users/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "testuser"

    r2 = test_app.get(f"/api/v1/users/{user_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == user_id
