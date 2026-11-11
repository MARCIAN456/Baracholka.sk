from sqlalchemy.orm import Session
from fastapi import APIRouter, status, Depends
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.payments import Payout, PayoutStatus
from app.schemas.user import UserPrivateResponse, UserUpdateIBAN

router = APIRouter()

@router.get("/me", response_model=UserPrivateResponse, status_code=status.HTTP_200_OK)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/iban", response_model=UserPrivateResponse, status_code=status.HTTP_200_OK)
def update_my_iban(
        body: UserUpdateIBAN,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    clean_iban = body.iban.replace(" ", "").upper()
    current_user.iban = clean_iban

    db.query(Payout).filter(
        Payout.seller_id == current_user.id,
        Payout.status == PayoutStatus.PENDING.value
    ).update({"iban": clean_iban})

    db.commit()
    db.refresh(current_user)

    return current_user

