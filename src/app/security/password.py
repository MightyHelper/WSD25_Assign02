from passlib.context import CryptContext
from app.config import settings

# Use pbkdf2_sha256 which is pure-python and avoids native bcrypt issues in some envs
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    # ensure str and not bytes
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")
    # apply pepper (global secret) before hashing
    if settings.PEPPER:
        password = password + settings.PEPPER
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(plain_password, bytes):
        plain_password = plain_password.decode("utf-8", errors="ignore")
    if settings.PEPPER:
        plain_password = plain_password + settings.PEPPER
    return pwd_context.verify(plain_password, hashed_password)
