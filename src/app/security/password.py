from passlib.context import CryptContext

# Use pbkdf2_sha256 which is pure-python and avoids native bcrypt issues in some envs
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    # ensure str and not bytes
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
