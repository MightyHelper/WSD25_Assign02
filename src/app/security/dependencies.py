from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from ..security.jwt import decode_token
from ..db.base import get_session
from ..db.models import User

security = HTTPBearer(auto_error=False)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    scheme = creds.scheme.lower()
    if scheme != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    token = creds.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    # fetch user: prefer ID (stable) then fall back to username/email
    async with get_session() as session:
        # try by primary key id first
        try:
            u = await session.get(User, sub)
        except Exception:
            u = None
        if not u:
            stmt = select(User).where((User.username == sub) | (User.email == sub))
            res = await session.execute(stmt)
            u = res.scalars().first()
        if not u:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return u
