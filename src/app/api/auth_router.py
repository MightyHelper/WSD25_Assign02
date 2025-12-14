from fastapi import APIRouter, HTTPException, status
from ..schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from ..security.jwt import create_access_token
from ..db.models import User
from ..security.password import verify_password, hash_password
from app.db.base import get_session
import logging
import uuid

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
            logger.info("Authentication failed for username/email=%s: user not found", req.username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(req.password, user.password_hash):
            logger.info("Authentication failed for username/email=%s: wrong password", req.username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        # issue token with subject set to the user's id (stable, not mutable) and include type
        access_token = create_access_token(subject=user.id, user_type=getattr(user, 'type', None))
        logger.info("Authentication successful for user id=%s username=%s", user.id, user.username)
        return TokenResponse(access_token=access_token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user (no authentication required). Returns an access token."""
    async with get_session() as session:
        from sqlalchemy import select
        # ensure username/email are unique
        stmt = select(User).where((User.username == req.username) | (User.email == req.email))
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            logger.info("Registration attempt with existing username/email=%s/%s", req.username, req.email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already in use")
        user_id = str(uuid.uuid4())
        # enforce that registration creates only regular users (type=0)
        u = User(id=user_id, username=req.username, email=req.email, password_hash=hash_password(req.password), type=0)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        access_token = create_access_token(subject=u.id, user_type=0)
        logger.info("New user registered id=%s username=%s", u.id, u.username)
        return TokenResponse(access_token=access_token)
