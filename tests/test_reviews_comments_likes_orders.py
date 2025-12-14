import uuid
from project.tests.conftest import UserWithLogin


def test_review_comment_like_order_flow(test_app, admin_user: UserWithLogin, normal_user: UserWithLogin):
    # create user via fixture
    user, _ = normal_user
    user_id = user.id
    # create author
    author_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/authors/", json={"id": author_id, "name": "A"}, headers=admin_user[1])
    assert r.status_code == 201
    # create book
    book_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "B", "author_id": author_id}, headers=admin_user[1])
    assert r.status_code == 201
    # create review
    review_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/reviews/", json={"id": review_id, "book_id": book_id, "user_id": user_id, "title": "R", "content": "C"}, headers=normal_user[1])
    assert r.status_code == 201
    # comment
    comment_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/comments/", json={"id": comment_id, "user_id": user_id, "review_id": review_id, "content": "Nice"}, headers=normal_user[1])
    assert r.status_code == 201
    # like
    r = test_app.post("/api/v1/likes/", json={"book_id": book_id, "user_id": user_id, "wishlist": True, "favourite": False}, headers=normal_user[1])
    assert r.status_code == 201
    # order
    order_id = str(uuid.uuid4())
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": user_id, "paid": False}, headers=normal_user[1])
    assert r.status_code == 201
    # cleanup: delete review
    r = test_app.delete(f"/api/v1/reviews/{review_id}", headers=normal_user[1])
    assert r.status_code in (200, 204)
