import uuid

from project.tests.conftest import UserWithLogin



def test_authors_reviews_comments_likes_orders_more(test_app, admin_user: UserWithLogin, normal_user: UserWithLogin):
    # setup user, author, book
    author_id = str(uuid.uuid4())
    book_id = str(uuid.uuid4())
    review_id = str(uuid.uuid4())
    comment_id = str(uuid.uuid4())
    order_id = str(uuid.uuid4())

    r = test_app.post("/api/v1/authors/", json={"id": author_id, "name": "Auth"}, headers=admin_user[1])
    assert r.status_code == 201

    r = test_app.post("/api/v1/books/", json={"id": book_id, "title": "BookMore", "author_id": author_id}, headers=admin_user[1])
    assert r.status_code == 201

    # create review and comment
    r = test_app.post("/api/v1/reviews/", json={"id": review_id, "book_id": book_id, "user_id": normal_user[0].id, "title": "R", "content": "C"}, headers=normal_user[1])
    assert r.status_code == 201

    r = test_app.post("/api/v1/comments/", json={"id": comment_id, "user_id": normal_user[0].id, "review_id": review_id, "content": "Nice"}, headers=normal_user[1])
    assert r.status_code == 201

    # list authors
    r = test_app.get("/api/v1/authors/")
    assert r.status_code == 200
    assert any(a["id"] == author_id for a in r.json()['content'])

    # list reviews for book
    r = test_app.get(f"/api/v1/reviews/book/{book_id}")
    assert r.status_code == 200
    assert any(rv["id"] == review_id for rv in r.json()['content'])

    # list comments for review
    r = test_app.get(f"/api/v1/reviews/{review_id}/comments")
    assert r.status_code == 200
    assert any(c["id"] == comment_id for c in r.json()['content'])

    # like comment
    r = test_app.post(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=normal_user[1])
    assert r.status_code == 200

    # unlike comment
    r = test_app.delete(f"/api/v1/reviews/{review_id}/comments/{comment_id}/like", headers=normal_user[1])
    assert r.status_code == 200

    # create order
    r = test_app.post("/api/v1/orders/", json={"id": order_id, "user_id": normal_user[0].id, "paid": False}, headers=normal_user[1])
    assert r.status_code == 201

    # add item
    r = test_app.post(f"/api/v1/orders/{order_id}/items", json={"book_id": book_id, "quantity": 2}, headers=normal_user[1])
    assert r.status_code == 201

    # pay order
    r = test_app.post(f"/api/v1/orders/{order_id}/pay", headers=normal_user[1])
    assert r.status_code == 200
    assert r.json()["paid"] is True
