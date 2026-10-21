from fastapi import HTTPException, status
from typing import Generator

import jwt
from fastapi.params import Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:

    exceptional_error = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Cannot verify the token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise exceptional_error

    except jwt.PyJWTError:
        raise exceptional_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise exceptional_error

    return user

