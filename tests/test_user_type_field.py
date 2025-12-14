import uuid

def test_user_type_default_and_response(test_app):
    uid = str(uuid.uuid4())
    uname = f'user_{uid[:6]}'
    r = test_app.post('/api/v1/users/', json={'id': uid, 'username': uname, 'email': f'{uid}@ex.com', 'password': 'pw'})
    assert r.status_code == 201
    data = r.json()
    assert 'type' in data
    assert isinstance(data['type'], int)
    assert data['type'] == 0

    # get user by id and ensure type present
    r2 = test_app.get(f'/api/v1/users/{uid}')
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2['type'] == 0

