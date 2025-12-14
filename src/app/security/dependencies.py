from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
import logging

from ..security.jwt import decode_token
from app.db.base import get_session
from ..db.models import User

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not creds:
        logger.debug("No credentials provided to get_current_user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    scheme = creds.scheme.lower()
    if scheme != "bearer":
        logger.warning("Invalid auth scheme provided: %s", creds.scheme)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    token = creds.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        logger.debug("Token decoded payload: keys=%s sub=%s", list(payload.keys()), sub)
        if not sub:
            logger.warning("Token decoded but missing subject")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception as exc:
        logger.exception("Failed to decode token during get_current_user: %s", exc)
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
            logger.warning("Token subject %s did not match any user", sub)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        logger.debug("Authenticated user id=%s username=%s type=%s", u.id, getattr(u, 'username', None), getattr(u, 'type', None))
        return u

async def get_current_user_optional(creds: HTTPAuthorizationCredentials = Depends(security)) -> User | None:
    # Similar to get_current_user but returns None instead of raising when creds missing or invalid
    if not creds:
        return None
    scheme = creds.scheme.lower()
    if scheme != "bearer":
        return None
    token = creds.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            return None
    except Exception as exc:
        logger.exception("Optional decode failed: %s", exc)
        return None
    async with get_session() as session:
        try:
            u = await session.get(User, sub)
        except Exception:
            u = None
        if not u:
            stmt = select(User).where((User.username == sub) | (User.email == sub))
            res = await session.execute(stmt)
            u = res.scalars().first()
        return u
