import uuid
import asyncio


def test_authors_pagination_headers(test_app, admin_headers):
    # create several authors
    ids = [str(uuid.uuid4()) for _ in range(3)]
    for i, aid in enumerate(ids):
        r = test_app.post('/api/v1/authors/', json={'id': aid, 'name': f'A{i}'}, headers=admin_headers)
        assert r.status_code == 201
    r = test_app.get('/api/v1/authors/?page=1&per_page=2')
    assert r.status_code == 200
    assert r.headers.get('X-Total-Count') is not None
    assert r.headers.get('X-Page') == '1'
    assert r.headers.get('X-Per-Page') == '2'


def test_books_pagination_headers(test_app, admin_headers):
    # create several books
    ids = [str(uuid.uuid4()) for _ in range(3)]
    for i, bid in enumerate(ids):
        r = test_app.post('/api/v1/books/', json={'id': bid, 'title': f'B{i}', 'author_id': None}, headers=admin_headers)
        assert r.status_code == 201
    r = test_app.get('/api/v1/books/?page=1&per_page=2')
    assert r.status_code == 200
    assert r.headers.get('X-Total-Count') is not None
    assert r.headers.get('X-Page') == '1'
    assert r.headers.get('X-Per-Page') == '2'


def test_reviews_pagination_headers(test_app, admin_headers):
    # create book and some reviews
    book_id = str(uuid.uuid4())
    r = test_app.post('/api/v1/books/', json={'id': book_id, 'title': 'RBook', 'author_id': None}, headers=admin_headers)
    assert r.status_code == 201
    u_id = str(uuid.uuid4())
    r = test_app.post('/api/v1/users/', json={'id': u_id, 'username': f'u_{u_id[:6]}', 'email': f'{u_id}@ex.com', 'password': 'pw'})
    assert r.status_code == 201
    ids = [str(uuid.uuid4()) for _ in range(5)]
    for i, rid in enumerate(ids):
        r = test_app.post('/api/v1/reviews/', json={'id': rid, 'book_id': book_id, 'user_id': u_id, 'title': f'T{i}', 'content': 'c'})
        assert r.status_code == 201
    r = test_app.get(f'/api/v1/reviews/book/{book_id}?page=1&per_page=3')
    assert r.status_code == 200
    assert r.headers.get('X-Total-Count') == '5'
    assert r.headers.get('X-Page') == '1'
    assert r.headers.get('X-Per-Page') == '3'


def test_comments_pagination_headers(test_app, admin_headers):
    # create book, review and comments
    book_id = str(uuid.uuid4())
    r = test_app.post('/api/v1/books/', json={'id': book_id, 'title': 'CBook', 'author_id': None}, headers=admin_headers)
    assert r.status_code == 201
    u_id = str(uuid.uuid4())
    uname = f'u_{u_id[:6]}'
    r = test_app.post('/api/v1/users/', json={'id': u_id, 'username': uname, 'email': f'{u_id}@ex.com', 'password': 'pw'})
    assert r.status_code == 201
    rev_id = str(uuid.uuid4())
    r = test_app.post('/api/v1/reviews/', json={'id': rev_id, 'book_id': book_id, 'user_id': u_id, 'title': 'T', 'content': 'c'})
    assert r.status_code == 201
    ids = [str(uuid.uuid4()) for _ in range(4)]
    for cid in ids:
        r = test_app.post(f'/api/v1/reviews/{rev_id}/comments', json={'id': cid, 'user_id': u_id, 'content': 'hey'})
        assert r.status_code == 201
    r = test_app.get(f'/api/v1/reviews/{rev_id}/comments?page=1&per_page=2')
    assert r.status_code == 200
    assert r.headers.get('X-Total-Count') == '4'
    assert r.headers.get('X-Page') == '1'
    assert r.headers.get('X-Per-Page') == '2'


def test_likes_pagination_headers(test_app, admin_headers):
    # create user, books and likes
    u_id = str(uuid.uuid4())
    uname = f'u_{u_id[:6]}'
    r = test_app.post('/api/v1/users/', json={'id': u_id, 'username': uname, 'email': f'{u_id}@ex.com', 'password': 'pw'})
    assert r.status_code == 201
    bids = [str(uuid.uuid4()) for _ in range(4)]
    for bid in bids:
        r = test_app.post('/api/v1/books/', json={'id': bid, 'title': 'LB', 'author_id': None}, headers=admin_headers)
        assert r.status_code == 201
        r = test_app.post('/api/v1/likes/', json={'book_id': bid, 'user_id': u_id, 'wishlist': True, 'favourite': False})
        assert r.status_code == 201
    # login and get token
    r = test_app.post('/api/v1/auth/login', json={'username': uname, 'password': 'pw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    r = test_app.get('/api/v1/users/me/likes?page=1&per_page=2', headers=headers)
    assert r.status_code == 200
    assert r.headers.get('X-Total-Count') == '4'
    assert r.headers.get('X-Page') == '1'
    assert r.headers.get('X-Per-Page') == '2'
