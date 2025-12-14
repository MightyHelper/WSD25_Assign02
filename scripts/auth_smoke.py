from app.main import create_app
from fastapi.testclient import TestClient
import uuid

app = create_app()
with TestClient(app) as client:
    user_id = str(uuid.uuid4())
    username = f"smoke_{user_id[:8]}"
    payload = {"username": username, "email": f"{username}@example.com", "password": "pw"}
    r = client.post("/api/v1/auth/register", json=payload)
    print('register', r.status_code, r.json())
    data = r.json()
    token = data.get('access_token')
    refresh = data.get('refresh_token')
    # use refresh
    r2 = client.post('/api/v1/auth/refresh', json={'refresh_token': refresh})
    print('refresh', r2.status_code, r2.json())

