import uuid

import app.security.jwt as jwtmod


def test_admin_can_create_author_and_book(test_app, admin_user):
    # use admin fixture which already creates an admin and returns auth headers
    headers = admin_user[1]

    # create author as admin
    aid = str(uuid.uuid4())
    r = test_app.post('/api/v1/authors/', json={'id': aid, 'name': 'Admin Author'}, headers=headers)
    assert r.status_code == 201

    # create book as admin
    bid = str(uuid.uuid4())
    r = test_app.post('/api/v1/books/', json={'id': bid, 'title': 'Admin Book', 'author_id': aid}, headers=headers)
    assert r.status_code == 201


def test_non_admin_cannot_create_author(test_app, normal_user):
    aid = str(uuid.uuid4())
    r = test_app.post('/api/v1/authors/', json={'id': aid, 'name': 'Should Fail'}, headers=normal_user[1])
    assert r.status_code == 403


def test_admin_can_create_admin_user_via_api(test_app, admin_user):
    # create new admin via API (type=1)
    uid = str(uuid.uuid4())
    r = test_app.post('/api/v1/users/', json={'id': uid, 'username': f'admin_{uid[:6]}', 'email': f'{uid}@ex.com', 'password': 'pw', 'type': 1}, headers=admin_user[1])
    assert r.status_code == 201
    data = r.json()
    assert data['type'] == 1

    # verify new admin can login and token contains type claim
    r = test_app.post('/api/v1/auth/login', json={'username': data['username'], 'password': 'pw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    # decode token via server endpoint by reading jwt.decode via app.security.jwt
    payload = jwtmod.decode_token(token)
    assert payload.get('type') == 1
