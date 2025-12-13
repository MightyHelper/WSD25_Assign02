import pytest
from app.schemas.auth import RegisterRequest


def test_register_request_validation():
    # Basic Pydantic validation: email must be valid
    with pytest.raises(Exception):
        RegisterRequest(username="u", email="not-an-email", password="p")


def test_register_flow(test_app):
    client = test_app
    # create a user
    payload = {"username": "test_register_user", "email": "test_register@example.com", "password": "strongpass"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data and isinstance(data["access_token"], str)

    # login with the same creds (by username)
    r2 = client.post("/api/v1/auth/login", json={"username": payload["username"], "password": payload["password"]})
    assert r2.status_code == 200
    assert "access_token" in r2.json()

    # login with email (login accepts username or email)
    r3 = client.post("/api/v1/auth/login", json={"username": payload["email"], "password": payload["password"]})
    assert r3.status_code == 200
    assert "access_token" in r3.json()


def test_register_duplicate(test_app):
    client = test_app
    payload = {"username": "dup_user", "email": "dup@example.com", "password": "pw"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    # try again with same username
    r2 = client.post("/api/v1/auth/register", json={"username": payload["username"], "email": "other@example.com", "password": "pw"})
    assert r2.status_code == 400
    # try again with same email
    r3 = client.post("/api/v1/auth/register", json={"username": "othername", "email": payload["email"], "password": "pw"})
    assert r3.status_code == 400


# Edge cases

def test_register_missing_fields_returns_422(test_app):
    client = test_app
    # missing email
    r = client.post("/api/v1/auth/register", json={"username": "noemail", "password": "pw"})
    assert r.status_code == 422
    # missing username
    r2 = client.post("/api/v1/auth/register", json={"email": "a@b.com", "password": "pw"})
    assert r2.status_code == 422
    # missing password
    r3 = client.post("/api/v1/auth/register", json={"username": "nouser", "email": "a@b.com"})
    assert r3.status_code == 422


def test_register_invalid_email_returns_422(test_app):
    client = test_app
    r = client.post("/api/v1/auth/register", json={"username": "bademail", "email": "not-an-email", "password": "pw"})
    assert r.status_code == 422


def test_register_sql_injection_like_input(test_app):
    client = test_app
    payload = {"username": "or 1=1; --", "email": "inject@example.com", "password": "pw"}
    # Should be treated as a normal string and either create a user or raise duplicate/email validation
    r = client.post("/api/v1/auth/register", json=payload)
    # Either created (201) or forbidden/bad request if constraints block it (400/422)
    assert r.status_code in (201, 400, 422)


def test_register_long_username(test_app):
    client = test_app
    long_username = "u" * 300
    r = client.post("/api/v1/auth/register", json={"username": long_username, "email": "long@example.com", "password": "pw"})
    # DB username column is varchar(100); if DB enforces it, expect 400, otherwise creation may succeed.
    assert r.status_code in (201, 400, 422)
