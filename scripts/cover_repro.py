import os
from fastapi.testclient import TestClient
from app.main import create_app
import uuid

app = create_app()
with TestClient(app) as client:
    user_id = str(uuid.uuid4())
    uname = 'dbg_' + user_id[:6]
    print('creating user', uname)
    r = client.post('/api/v1/users/', json={'id': user_id, 'username': uname, 'email': f'{user_id}@example.com', 'password': 'pw'})
    print('create user', r.status_code, r.text)
    book_id = str(uuid.uuid4())
    print('creating book', book_id)
    r = client.post('/api/v1/books/', json={'id': book_id, 'title': 'testbook', 'author_id': None})
    print('create book', r.status_code, r.text)
    r = client.post('/api/v1/auth/login', json={'username': uname, 'password': 'pw'})
    print('login', r.status_code, r.text)
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/octet-stream'}
    print('posting cover with headers', headers)
    r = client.post(f'/api/v1/books/{book_id}/cover', data=b'abc', headers=headers)
    print('post cover', r.status_code)
    try:
        print('json', r.json())
    except Exception:
        print('text', r.text)
    print('done')

