import uuid


def test_invalid_login(test_app):
    uname = str(uuid.uuid4())
    r = test_app.post("/api/v1/auth/login", json={"username": uname, "password": "x"})
    assert r.status_code == 401


def test_unauthorized_access(test_app):
    # call protected endpoint without token
    book_id = str(uuid.uuid4())
    r = test_app.patch(f"/api/v1/books/{book_id}/like", params={"wishlist": True})
    # should be unauthorized
    assert r.status_code == 401


def test_forbidden_order_access(test_app):
    # create two users and an order for user A and try to modify with user B
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    r = test_app.post("/api/v1/users/", json={"id": user_a, "username": "user_a", "email": f"{user_a}@example.com", "password": "pw"})
    assert r.status_code == 201
    r = test_app.post("/api/v1/users/", json={"id": user_b, "username": "user_b", "email": f"{user_b}@example.com", "password": "pw"})
    assert r.status_code == 201

    # login as user_b
    r = test_app.post("/api/v1/auth/login", json={"username": "user_b", "password": "pw"})
    assert r.status_code == 200
    token_b = r.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # create order for user_a
    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": user_a, "paid": False})
    assert r.status_code == 201

    # attempt to add item as user_b
    book_id = str(uuid.uuid4())
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 1}, headers=headers_b)
    assert r.status_code == 403
