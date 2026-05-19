import os
from passlib.context import CryptContext
from jose import JWTError, jwt

_pwd_ctx = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)
_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_jwt(payload: dict) -> str:
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        return None
