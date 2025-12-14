import uuid
from conftest import UserWithLogin


def auth_headers(client, username, password):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_and_like_book(test_app, admin_user: UserWithLogin, normal_user: UserWithLogin):
    # use fixture user and create a book
    user, user_headers = normal_user
    user_id = user.id
    username = user.username
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "List Book", "author_id": None}, headers=admin_user[1])
    assert r.status_code == 201

    # list books (public)
    r = test_app.get("/api/v1/books/")
    assert r.status_code == 200
    data = r.json()
    assert any(b["id"] == book_id for b in data['content'])

    headers = user_headers

    # like the book (create)
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"wishlist": True}, headers=headers)
    assert r.status_code in (200, 201)
    jr = r.json()
    assert jr["book_id"] == book_id
    assert jr["user_id"] == user_id
    assert jr["wishlist"] is True

    # update like
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"favourite": True}, headers=headers)
    assert r.status_code == 200
    jr = r.json()
    assert jr["favourite"] is True
