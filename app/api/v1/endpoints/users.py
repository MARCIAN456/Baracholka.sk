
from fastapi import APIRouter, status, Depends
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

