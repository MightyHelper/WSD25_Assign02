from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
import logging

from ..security.jwt import decode_token
from app.db.base import get_session
from ..db.models import User

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

async def _extract_sub_from_token(token: str, raise_on_error: bool) -> str | None:
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        logger.debug("Token decoded payload: keys=%s sub=%s", list(payload.keys()), sub)
        if not sub:
            if raise_on_error:
                logger.warning("Token decoded but missing subject")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            return None
        return sub
    except Exception as exc:
        if raise_on_error:
            logger.exception("Failed to decode token during get_current_user: %s", exc)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
        logger.exception("Optional decode failed: %s", exc)
        return None

async def _get_user_by_sub(sub: str) -> User | None:
    async with get_session() as session:
        try:
            u = await session.get(User, sub)
        except Exception:
            u = None
        return u

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not creds:
        logger.debug("No credentials provided to get_current_user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization")
    scheme = creds.scheme.lower()
    if scheme != "bearer":
        logger.warning("Invalid auth scheme provided: %s", creds.scheme)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    token = creds.credentials
    sub = await _extract_sub_from_token(token, raise_on_error=True)
    u = await _get_user_by_sub(sub)
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
    sub = await _extract_sub_from_token(token, raise_on_error=False)
    if not sub:
        return None
    u = await _get_user_by_sub(sub)
    return u

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if getattr(current_user, 'type', 0) != 1:
        logger.warning("Non-admin user id=%s attempted to access admin-only resource", getattr(current_user, 'id', None))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    logger.debug("Admin user id=%s access granted", getattr(current_user, 'id', None))
    return current_user