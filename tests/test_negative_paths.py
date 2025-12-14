import uuid
from project.tests.conftest import UserWithLogin


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


def test_forbidden_order_access(test_app, normal_user: UserWithLogin, another_normal_user: UserWithLogin):
    # create two users via fixtures and an order for user A and try to modify with user B
    user_a, headers_a = normal_user
    user_b, headers_b = another_normal_user

    # create order for user_a
    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": user_a.id, "paid": False}, headers=headers_a)
    assert r.status_code == 201

    # attempt to add item as user_b
    book_id = str(uuid.uuid4())
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 1}, headers=headers_b)
    assert r.status_code == 403
