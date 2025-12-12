from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.db.models import User
from app.db.base import get_session
from app.security.password import hash_password

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserIn(BaseModel):
    id: str
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserIn):
    async with get_session() as session:
        u = User(id=user_in.id, username=user_in.username, email=user_in.email, password_hash=hash_password(user_in.password))
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return UserOut.model_validate(u)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    async with get_session() as session:
        u = await session.get(User, user_id)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut.model_validate(u)
