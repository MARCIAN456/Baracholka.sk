import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(pwd_bytes, salt)

    return hashed.decode("utf-8")

def verify_password(hash_password: str, password: str) -> bool:
    hash_bytes = hash_password.encode("utf-8")
    password_bytes = password.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hash_bytes)

def create_access_token(user_id: str, user_role: str, expires_delta: timedelta | None = None):
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    payload = {"sub": str(user_id), "role": user_role, "exp": expire}

    return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)

