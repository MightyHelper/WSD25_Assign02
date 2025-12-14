from pydantic import BaseModel, Field, EmailStr

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

class RegisterRequest(BaseModel):
    username: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)
