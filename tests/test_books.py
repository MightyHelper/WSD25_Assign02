import uuid
from conftest import UserWithLogin


def test_create_get_delete_book(test_app, admin_user: UserWithLogin):
    book_id = str(uuid.uuid4())
    payload = {"id": book_id, "title": "Integration Test Book", "author_id": None}
    r = test_app.post("/api/v1/books/", json=payload, headers=admin_user[1])
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == book_id

    r2 = test_app.get(f"/api/v1/books/{book_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == book_id

    r3 = test_app.delete(f"/api/v1/books/{book_id}")
    assert r3.status_code == 200

    r4 = test_app.get(f"/api/v1/books/{book_id}")
    assert r4.status_code == 404


def test_cover_upload_and_get(test_app, admin_user: UserWithLogin):
    book_id = str(uuid.uuid4())
    payload = {"id": book_id, "title": "Cover Test Book", "author_id": None}
    r = test_app.post("/api/v1/books/", json=payload, headers=admin_user[1])
    assert r.status_code == 201

    # upload cover
    cover_bytes = b"hello cover"
    r2 = test_app.post(f"/api/v1/books/{book_id}/cover", content=cover_bytes, headers=admin_user[1])
    assert r2.status_code == 200

    r3 = test_app.get(f"/api/v1/books/{book_id}/cover")
    assert r3.status_code == 200
    assert r3.content == cover_bytes
