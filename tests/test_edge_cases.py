import uuid
import os
from app.security.jwt import create_access_token


def auth_headers_for_subject(client, subject, password="pw"):
    token = create_access_token(subject)
    return {"Authorization": f"Bearer {token}"}


def test_like_book_user_not_found(test_app):
    # create a book but use a token whose subject doesn't map to an existing user
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "Edge Book", "author_id": None})
    assert r.status_code == 201
    headers = auth_headers_for_subject(test_app, "ghost_user")
    # should return 401 because user not found
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"wishlist": True}, headers=headers)
    assert r.status_code == 401


def test_upload_cover_empty_body_returns_400(test_app):
    # create user and book
    user_id = str(uuid.uuid4())
    uname = f"u_{user_id[:6]}"
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "EmptyCover", "author_id": None})
    assert r.status_code == 201
    # login
    r = test_app.post("/api/v1/auth/login", json={"username": uname, "password": "pw"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}
    # send empty body
    r = test_app.post(f"/api/v1/books/{book_id}/cover", headers=headers, data=b"")
    assert r.status_code == 400


def test_get_cover_path_missing_returns_404(test_app, tmp_path):
    # create user and book and set cover_path to missing file
    user_id = str(uuid.uuid4())
    uname = f"u_{user_id[:6]}"
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "MissingPath", "author_id": None})
    assert r.status_code == 201
    # set cover_path directly in DB
    from app.db.base import get_session
    async def _set_path():
        async with get_session() as session:
            b = await session.get(__import__("app.db.models", fromlist=["Book"]).Book, book_id)
            b.cover_path = str(tmp_path / "no_file.bin")
            session.add(b)
            await session.commit()
    import asyncio
    asyncio.run(_set_path())
    # now get should return 404
    r = test_app.get(f"/api/v1/books/{book_id}/cover")
    assert r.status_code == 404


def test_comment_like_unlike_flow(test_app):
    # create user
    user_id = str(uuid.uuid4())
    uname = f"u_{user_id[:6]}"
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201

    # create a book and then create review and comment via the new nested endpoint
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "Rb", "author_id": None})
    assert r.status_code == 201
    review_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/reviews/", json={"id": review_id, "book_id": book_id, "user_id": user_id, "title": "R", "content": "c"})
    assert r.status_code == 201
    comment_id = str(uuid.uuid4())
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments", json={"id": comment_id, "user_id": user_id, "content": "hey"})
    assert r.status_code == 201

    # login and like
    r = test_app.post("/api/v1/auth/login", json={"username": uname, "password": "pw"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 200
    jr = r.json()
    assert "liked" in jr["message"].lower()

    # unlike
    r = test_app.delete(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 200
    jr = r.json()
    assert "removed" in jr["message"].lower()

    # unlike again should return 404
    r = test_app.delete(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 404
