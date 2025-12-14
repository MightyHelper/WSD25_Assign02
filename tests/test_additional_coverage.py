import uuid

import pytest

from app.storage import FSStorage, DBStorage, get_storage
from app.redis_client import get_redis, _NullRedis
from app.db.base import get_session
from project.tests.conftest import UserWithLogin


def test_redis_null_impl_returns_null():
    # ensure no redis url env
    r = get_redis()
    assert isinstance(r, _NullRedis)


@pytest.mark.asyncio
async def test_fsstorage_save_and_get(tmp_path):
    # use a temporary upload directory by monkeypatching UPLOAD_DIR
    from app import storage
    original = storage.UPLOAD_DIR
    storage.UPLOAD_DIR = tmp_path
    try:
        s = FSStorage()
        book_id = str(uuid.uuid4())
        data = b"coverdata"
        path = await s.save_cover(book_id, data)
        assert path is not None
        # create a fake book-like object
        class B:
            cover_path = path
        got = await s.get_cover(B())
        assert got == data
        # missing path returns None
        B2 = type("B2", (), {"cover_path": None})
        assert await s.get_cover(B2()) is None
    finally:
        storage.UPLOAD_DIR = original


@pytest.mark.asyncio
async def test_dbstorage_returns_blob_directly():
    s = DBStorage()
    book_id = str(uuid.uuid4())
    data = b"abc"
    # save_cover returns None indicating DB storage
    res = await s.save_cover(book_id, data)
    assert res is None
    class B:
        cover = data
        cover_path = None
    got = await s.get_cover(B())
    assert got == data


def test_get_storage_respects_setting(monkeypatch):
    from app.config import settings
    from app.config import StorageKind
    monkeypatch.setattr(settings, "STORAGE_KIND", StorageKind.FS)
    s = get_storage()
    assert isinstance(s, FSStorage)
    monkeypatch.setattr(settings, "STORAGE_KIND", StorageKind.DB)
    s2 = get_storage()
    assert isinstance(s2, DBStorage)


def test_cover_upload_and_not_found(test_app, admin_user: UserWithLogin):
    # create user and book
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "CBook", "author_id": None}, headers=admin_user[1])
    assert r.status_code == 201

    # attempt to get non-existing cover
    r = test_app.get(f"/api/v1/books/{book_id}/cover")
    assert r.status_code == 404


def test_order_item_and_pay_flow(test_app, admin_user: UserWithLogin, normal_user: UserWithLogin):
    # create book
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "Order Book", "author_id": None}, headers=admin_user[1])
    assert r.status_code == 201
    # create order
    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": normal_user[0].id}, headers=normal_user[1])
    assert r.status_code == 201

    # add item
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 2}, headers=normal_user[1])
    assert r.status_code == 201
    jr = r.json()
    assert jr["book_id"] == book_id
    assert jr["quantity"] == 2

    # update item (service may return 200 or 201 depending on upsert semantics)
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 1}, headers=normal_user[1])
    assert r.status_code in (200, 201)
    jr = r.json()
    assert jr["quantity"] == 1

    # pay order - should succeed
    r = test_app.post(f"/api/v1/orders/{order_id}/pay", headers=normal_user[1])
    assert r.status_code == 200
    jr = r.json()
    assert jr["paid"] is True

    # paying again should fail
    r = test_app.post(f"/api/v1/orders/{order_id}/pay", headers=normal_user[1])
    assert r.status_code == 400


def test_set_item_bad_authorization(test_app, admin_user: UserWithLogin, normal_user: UserWithLogin, another_normal_user: UserWithLogin):
    # create two users with unique usernames, one creates order the other tries to add
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "Abook", "author_id": None}, headers=admin_user[1])
    assert r.status_code == 201
    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": normal_user[0].id}, headers=normal_user[1])
    assert r.status_code == 201

    # try to add item to user_a's order
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 1}, headers=another_normal_user[1])
    assert r.status_code == 403

