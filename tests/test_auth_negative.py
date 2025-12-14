import uuid
from datetime import timedelta

from app.security.jwt import create_access_token
from project.tests.conftest import UserWithLogin


def test_missing_auth_returns_401(test_app):
    r = test_app.get("/api/v1/users/me")
    assert r.status_code == 401


def test_wrong_scheme_returns_401(test_app, normal_user: UserWithLogin):
    # provide Basic instead of Bearer
    headers = {"Authorization": "Basic abcdef"}
    r = test_app.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401


def test_tampered_token_returns_401(test_app, normal_user: UserWithLogin):
    # create valid token then tamper
    token = create_access_token(subject=normal_user[0].id, user_type=1)
    tampered = token + "tamper"
    headers = {"Authorization": f"Bearer {tampered}"}
    r = test_app.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401


def test_expired_token_returns_401(test_app, normal_user: UserWithLogin):
    # use fixture user and create token with negative expiry
    uid = normal_user[0].id
    token = create_access_token(subject=uid, expires_delta=timedelta(seconds=-10))
    headers = {"Authorization": f"Bearer {token}"}
    r = test_app.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401


def test_invalid_signature_token_returns_401(test_app, monkeypatch, normal_user: UserWithLogin):
    # monkeypatch jose.jwt.decode to raise an error simulating signature failure
    import jose
    def fake_jose_decode(tok, *args, **kwargs):
        raise Exception("Signature verification failed")
    monkeypatch.setattr(jose.jwt, "decode", fake_jose_decode)
    # Also patch the decode_token symbol used directly by the dependency module
    import importlib
    deps_mod = importlib.import_module('app.security.dependencies')
    def fake_decode_token(tok):
        raise Exception("Signature verification failed")
    monkeypatch.setattr(deps_mod, 'decode_token', fake_decode_token)
    headers = {"Authorization": f"Bearer {normal_user[1]['Authorization'].split(' ')[1]}"}
    r = test_app.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401
