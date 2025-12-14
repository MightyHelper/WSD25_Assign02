from fastapi.testclient import TestClient
from app.main import create_app
import uuid
import sys

app = create_app()
client = TestClient(app)

def run():
    print('RUN_QUICK START', flush=True)
    user_id = str(uuid.uuid4())
    uname = f"u_{user_id[:6]}"
    print('create user', user_id, uname, flush=True)
    r = client.post('/api/v1/users/', json={'id': user_id, 'username': uname, 'email': f'{user_id}@example.com', 'password': 'pw'})
    print('create user status', r.status_code, r.text, flush=True)
    if r.status_code != 201:
        sys.exit(2)

    book_id = str(uuid.uuid4())
    print('create book', book_id, flush=True)
    r = client.post('/api/v1/books/', json={'id': book_id, 'title': 'Rb', 'author_id': None})
    print('create book status', r.status_code, r.text, flush=True)
    if r.status_code != 201:
        sys.exit(3)

    review_id = str(uuid.uuid4())
    payload = {'id': review_id, 'book_id': book_id, 'user_id': user_id, 'title': 'R', 'content': 'c'}
    print('create review payload', payload, flush=True)
    r = client.post('/api/v1/reviews/', json=payload)
    print('create review status', r.status_code, r.text, flush=True)
    if r.status_code != 201:
        print('Response json:', end=' ', flush=True)
        try:
            print(r.json(), flush=True)
        except Exception:
            print(r.text, flush=True)
        sys.exit(4)

    # create comment via DB insert to avoid endpoint differences
    comment_id = str(uuid.uuid4())
    print('inserting comment via DB', comment_id, flush=True)
    from app.db.base import get_session
    from app.db.models import Comment

    async def _insert():
        async with get_session() as session:
            cm = Comment(id=comment_id, user_id=user_id, review_id=review_id, content='hey')
            session.add(cm)
            await session.commit()

    import asyncio
    asyncio.run(_insert())

    r = client.post('/api/v1/auth/login', json={'username': uname, 'password': 'pw'})
    print('login status', r.status_code, r.text, flush=True)
    if r.status_code != 200:
        sys.exit(6)
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    r = client.post(f'/api/v1/reviews/{review_id}/comments/{comment_id}/like', headers=headers)
    print('like status', r.status_code, r.text, flush=True)
    if r.status_code != 200:
        sys.exit(7)

    r = client.delete(f'/api/v1/reviews/{review_id}/comments/{comment_id}/like', headers=headers)
    print('unlike status', r.status_code, r.text, flush=True)
    if r.status_code != 200:
        sys.exit(8)

    r = client.delete(f'/api/v1/reviews/{review_id}/comments/{comment_id}/like', headers=headers)
    print('unlike again status', r.status_code, r.text, flush=True)
    # expecting 404
    if r.status_code != 404:
        sys.exit(9)

    print('All steps completed OK', flush=True)

if __name__ == '__main__':
    run()
