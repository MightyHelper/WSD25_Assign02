import uuid


def test_list_and_like_book(test_app):
    # create user and book
    user_id = str(uuid.uuid4())
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/users/", json={"id": user_id, "username": "u_list", "email": f"{user_id}@example.com", "password": "pw"})
    assert r.status_code == 201
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "List Book", "author_id": None})
    assert r.status_code == 201

    # list books
    r = test_app.get("/api/v1/books/")
    assert r.status_code == 200
    data = r.json()
    assert any(b["id"] == book_id for b in data)

    # like the book (create)
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"user_id": user_id, "wishlist": True})
    assert r.status_code in (200, 201)
    jr = r.json()
    assert jr["book_id"] == book_id
    assert jr["user_id"] == user_id
    assert jr["wishlist"] is True

    # update like
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"user_id": user_id, "favourite": True})
    assert r.status_code == 200
    jr = r.json()
    assert jr["favourite"] is True

