from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
import logging
import secrets

from ..config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None, user_type: Optional[int] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    # use timezone-aware UTC datetimes
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    if user_type is not None:
        to_encode["type"] = int(user_type)
    if extra_claims:
        to_encode.update(extra_claims)
    logger.debug("Creating access token for sub=%s type=%s exp=%s", subject, to_encode.get("type"), expire)
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        logger.debug("Decoded token payload keys=%s", list(payload.keys()))
        return payload
    except Exception as exc:
        logger.exception("Failed to decode token: %s", exc)
        raise

def create_refresh_token_string() -> str:
    # use a URL-safe random token
    return secrets.token_urlsafe(48)
