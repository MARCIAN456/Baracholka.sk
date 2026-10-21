from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import hash_password, create_access_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_db

from app.models.user import User
from app.schemas.token import Token

from app.schemas.user import UserCreate, UserResponse, UserLogin

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == body.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email exists"
        )

    hashed_password = hash_password(body.password)

    new_user = User(
        username=body.name,
        password=hashed_password,
        email=body.email,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == body.username).first()

    if not existing_user :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You need register first"
        )
    verified_password = verify_password(existing_user.password, body.password)

    if not verified_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(
        user_id=str(existing_user.id),
        user_role=existing_user.role
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )

