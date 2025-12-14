from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.auth import LoginRequest, TokenResponse, RegisterRequest, RefreshRequest
from ..security.jwt import create_access_token, create_refresh_token_string, REFRESH_TOKEN_EXPIRE_DAYS
from ..db.models import User, RefreshToken
from ..security.password import verify_password, hash_password
from app.db.base import get_session
from app.security.dependencies import get_current_user, get_current_user_optional
import logging
import uuid
import datetime
from datetime import timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
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
        access_token = create_access_token(subject=user.id, user_type=getattr(user, 'type', None))
        # create refresh token
        rtoken = create_refresh_token_string()
        expires = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        rt = RefreshToken(id=str(uuid.uuid4()), user_id=user.id, token=rtoken, expires_at=expires)
        session.add(rt)
        await session.commit()
        logger.info("Authentication successful for user id=%s username=%s", user.id, user.username)
        return TokenResponse(access_token=access_token, refresh_token=rtoken)

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(User).where((User.username == req.username) | (User.email == req.email))
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if existing:
            logger.info("Registration attempt with existing username/email=%s/%s", req.username, req.email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already in use")
        user_id = str(uuid.uuid4())
        u = User(id=user_id, username=req.username, email=req.email, password_hash=hash_password(req.password), type=0)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        access_token = create_access_token(subject=u.id, user_type=0)
        # create refresh token
        rtoken = create_refresh_token_string()
        expires = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        rt = RefreshToken(id=str(uuid.uuid4()), user_id=u.id, token=rtoken, expires_at=expires)
        session.add(rt)
        await session.commit()
        logger.info("New user registered id=%s username=%s", u.id, u.username)
        return TokenResponse(access_token=access_token, refresh_token=rtoken)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    # Validate refresh token exists and not expired, then issue a new access token and rotate refresh token
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(RefreshToken).where(RefreshToken.token == req.refresh_token)
        res = await session.execute(stmt)
        rec = res.scalars().first()
        if not rec:
            logger.info("Invalid refresh token presented")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if rec.expires_at < datetime.datetime.now(timezone.utc):
            logger.info("Expired refresh token for user_id=%s", rec.user_id)
            # remove expired token
            await session.delete(rec)
            await session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        # fetch user
        user = await session.get(User, rec.user_id)
        if not user:
            logger.info("Refresh token user not found user_id=%s", rec.user_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        # rotate token
        new_rtoken = create_refresh_token_string()
        rec.token = new_rtoken
        rec.expires_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        session.add(rec)
        await session.commit()
        access_token = create_access_token(subject=user.id, user_type=getattr(user, 'type', None))
        return TokenResponse(access_token=access_token, refresh_token=new_rtoken)

@router.post("/logout")
async def logout(payload: dict = None, current_user: User | None = Depends(get_current_user_optional)):
    """Logout behavior:
    - If JSON body contains {'refresh_token': '<token>'}, revoke that specific refresh token.
    - Else if Authorization header present and valid, revoke all refresh tokens for that user.
    - Otherwise return 400.
    """
    # payload may be None when no body provided
    rt_value = None
    try:
        if payload and isinstance(payload, dict):
            rt_value = payload.get('refresh_token')
    except Exception:
        rt_value = None

    async with get_session() as session:
        from sqlalchemy import select
        if rt_value:
            stmt = select(RefreshToken).where(RefreshToken.token == rt_value)
            res = await session.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                logger.info("Logout attempted with unknown refresh token")
                # idempotent success
                return {"ok": True}
            await session.delete(rec)
            await session.commit()
            logger.info("Revoked refresh token for user_id=%s", rec.user_id)
            return {"ok": True}

        # no refresh_token provided: revoke for authenticated user
        if current_user:
            stmt = select(RefreshToken).where(RefreshToken.user_id == current_user.id)
            res = await session.execute(stmt)
            tokens = res.scalars().all()
            for t in tokens:
                await session.delete(t)
            await session.commit()
            logger.info("Revoked %d refresh tokens for user id=%s", len(tokens), current_user.id)
            return {"ok": True}

        # nothing provided
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a refresh_token or authenticate to revoke tokens")
