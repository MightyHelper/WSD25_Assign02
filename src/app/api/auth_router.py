from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.auth import LoginRequest, TokenResponse
from ..security.jwt import create_access_token
from ..db.models import User
from ..security.password import verify_password
from ..db.base import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # Lookup user by username or email
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(User).where((User.username == req.username) | (User.email == req.username))
        res = await session.execute(stmt)
        user = res.scalars().first()
        logger.debug("login attempt for %s, user_found=%s", req.username, bool(user))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        # issue token with subject set to the user's id (stable, not mutable)
        access_token = create_access_token(subject=user.id)
        return TokenResponse(access_token=access_token)
