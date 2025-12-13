import uuid
import asyncio
import os
from app.config import settings, StorageKind


def unique_uname():
    return f"u_{uuid.uuid4().hex[:8]}"


def auth_headers(client, username, password="pw"):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_order_item_delete_and_pay_empty(test_app):
    user_id = str(uuid.uuid4())
    uname = unique_uname()
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "OrderDelBook", "author_id": None})
    assert r.status_code == 201

    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": user_id})
    assert r.status_code == 201

    headers = auth_headers(test_app, uname)
    # add item
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 1}, headers=headers)
    assert r.status_code == 201
    # delete by setting quantity 0
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 0}, headers=headers)
    assert r.status_code in (200, 201)
    jr = r.json()
    assert jr["quantity"] == 0
    # now pay should fail because empty
    r = test_app.post(f"/api/v1/orders/{order_id}/pay", headers=headers)
    assert r.status_code == 400


def test_comment_like_already_liked(test_app):
    user_id = str(uuid.uuid4())
    uname = unique_uname()
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "CLB", "author_id": None})
    assert r.status_code == 201
    review_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/reviews/", json={"id": review_id, "book_id": book_id, "user_id": user_id, "title": "R", "content": "c"})
    assert r.status_code == 201
    comment_id = str(uuid.uuid4())
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments", json={"id": comment_id, "user_id": user_id, "content": "hey"})
    assert r.status_code == 201

    headers = auth_headers(test_app, uname)
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 200
    jr = r.json()
    assert "liked" in jr["message"].lower()
    # like again should return Already liked
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 200
    jr = r.json()
    assert "already" in jr["message"].lower()
    # cleanup unlike
    r = test_app.delete(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=headers)
    assert r.status_code == 200


def test_books_extra_cover_db_storage(monkeypatch, test_app):
    # force DB storage
    monkeypatch.setattr(settings, "STORAGE_KIND", StorageKind.DB)
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "DBCover", "author_id": None})
    assert r.status_code == 201
    data = b"myblob"
    # write blob directly into DB (control path) and verify GET works
    from app.db.base import get_session
    from app.db.models import Book
    import asyncio

    async def _write_blob():
        async with get_session() as session:
            b = await session.get(Book, book_id)
            b.cover = data
            session.add(b)
            await session.commit()

    asyncio.run(_write_blob())
    r2 = test_app.get(f"/api/v1/books/{book_id}/cover")
    assert r2.status_code == 200
    assert r2.content == data


def test_security_invalid_scheme(test_app):
    # create user and book
    user_id = str(uuid.uuid4())
    uname = unique_uname()
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": uname, "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "SecBook", "author_id": None})
    assert r.status_code == 201
    # call protected endpoint with wrong scheme
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"wishlist": True}, headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
