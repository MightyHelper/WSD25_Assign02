import uuid
import asyncio

from app.db.base import get_session
from app.db.models import User
from app.security.password import hash_password


def create_admin_user_in_db(username: str = 'admin0'):
    async def _create():
        async with get_session() as session:
            uid = str(uuid.uuid4())
            u = User(id=uid, username=username, email=f"{uid}@example.com", password_hash=hash_password('adminpw'), type=1)
            session.add(u)
            await session.commit()
            await session.refresh(u)
            return u
    return asyncio.run(_create())


def test_admin_can_create_author_and_book(test_app):
    # create admin directly in DB and login
    admin = create_admin_user_in_db('testadmin')
    r = test_app.post('/api/v1/auth/login', json={'username': admin.username, 'password': 'adminpw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # create author as admin
    aid = str(uuid.uuid4())
    r = test_app.post('/api/v1/authors/', json={'id': aid, 'name': 'Admin Author'}, headers=headers)
    assert r.status_code == 201

    # create book as admin
    bid = str(uuid.uuid4())
    r = test_app.post('/api/v1/books/', json={'id': bid, 'title': 'Admin Book', 'author_id': aid}, headers=headers)
    assert r.status_code == 201


def test_non_admin_cannot_create_author(test_app):
    # create normal user via API
    uid = str(uuid.uuid4())
    uname = f'u_{uid[:6]}'
    r = test_app.post('/api/v1/users/', json={'id': uid, 'username': uname, 'email': f'{uid}@ex.com', 'password': 'pw'})
    assert r.status_code == 201
    r = test_app.post('/api/v1/auth/login', json={'username': uname, 'password': 'pw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    aid = str(uuid.uuid4())
    r = test_app.post('/api/v1/authors/', json={'id': aid, 'name': 'Should Fail'}, headers=headers)
    assert r.status_code == 403


def test_admin_can_create_admin_user_via_api(test_app):
    # create and login admin
    admin = create_admin_user_in_db('testadmin2')
    r = test_app.post('/api/v1/auth/login', json={'username': admin.username, 'password': 'adminpw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # create new admin via API (type=1)
    uid = str(uuid.uuid4())
    r = test_app.post('/api/v1/users/', json={'id': uid, 'username': f'admin_{uid[:6]}', 'email': f'{uid}@ex.com', 'password': 'pw', 'type': 1}, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data['type'] == 1

    # verify new admin can login and token contains type claim
    r = test_app.post('/api/v1/auth/login', json={'username': data['username'], 'password': 'pw'})
    assert r.status_code == 200
    token = r.json()['access_token']
    # decode token via server endpoint by reading jwt.decode via app.security.jwt
    import app.security.jwt as jwtmod
    payload = jwtmod.decode_token(token)
    assert payload.get('type') == 1

