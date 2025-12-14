import uuid

def test_create_get_author(test_app, admin_headers):
    author_id = str(uuid.uuid4())
    payload = {"id": author_id, "name": "Author Test"}
    r = test_app.post("/api/v1/authors/", json=payload, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["id"] == author_id

    r2 = test_app.get(f"/api/v1/authors/{author_id}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Author Test"
