import uuid


def test_logout_with_refresh_token(test_app):
    username = f"logout_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "email": f"{username}@example.com", "password": "pw"}
    r = test_app.post('/api/v1/auth/register', json=payload)
    assert r.status_code == 201
    data = r.json()
    refresh = data.get('refresh_token')
    assert refresh is not None
    # logout with refresh token
    r2 = test_app.post('/api/v1/auth/logout', json={'refresh_token': refresh})
    assert r2.status_code == 200
    # attempting to refresh should now fail
    r3 = test_app.post('/api/v1/auth/refresh', json={'refresh_token': refresh})
    assert r3.status_code == 401


def test_logout_authenticated_revokes_all(test_app):
    username = f"logout2_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "email": f"{username}@example.com", "password": "pw"}
    r = test_app.post('/api/v1/auth/register', json=payload)
    assert r.status_code == 201
    data = r.json()
    refresh = data.get('refresh_token')
    # login and get access token
    rlogin = test_app.post('/api/v1/auth/login', json={'username': username, 'password': 'pw'})
    assert rlogin.status_code == 200
    access = rlogin.json().get('access_token')
    headers = {'Authorization': f'Bearer {access}'}
    # logout (authenticated) should revoke all tokens
    r2 = test_app.post('/api/v1/auth/logout', headers=headers)
    assert r2.status_code == 200
    # refresh token should be invalid now
    r3 = test_app.post('/api/v1/auth/refresh', json={'refresh_token': refresh})
    assert r3.status_code == 401

