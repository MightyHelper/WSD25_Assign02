from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt

from ..config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    # use timezone-aware UTC datetimes
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    return payload
