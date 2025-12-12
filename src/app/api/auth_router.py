from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.auth import LoginRequest, TokenResponse
from ..security.jwt import create_access_token
from ..db.models import User
from ..security.password import verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # In a complete implementation we'd query the DB for the user and verify password.
    # For now, implement a stub that accepts any username/password and returns a token.
    # TODO: replace with DB lookup
    access_token = create_access_token(subject=req.username)
    return TokenResponse(access_token=access_token)

