import uuid
import math

from app.api.v1.endpoints.payments import payment_success
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from enum import Enum

from app.api.deps import get_current_user, get_db
from app.models.item import Item
from app.schemas.delivery import DeliveryResponse, DeliveryCreate, DeliveryStatus, DeliveryPaginatedResponse
from app.models.delivery import Delivery
from app.models.payments import Payment
from app.models.user import User
from app.core.limiter import limiter

router = APIRouter()

@router.post("/create-delivery/{item_id}", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_delivery(request: Request, body: DeliveryCreate, item_id: uuid.UUID,  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    if item.is_sold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is sold"
        )
    if current_user.id == item.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cant buy your own item"
        )
    existing_delivery = db.query(Delivery).filter(Delivery.item_id == item_id, Delivery.email == current_user.email).first()
    if existing_delivery:
        db.delete(existing_delivery)


    new_delivery = Delivery(
        username = body.username,
        email = current_user.email,
        phone=body.phone,
        addressId=body.addressId,
        weight=body.weight,
        value=item.price,
        status=DeliveryStatus.PENDING.value,
        item_id=item_id,
    )

    db.add(new_delivery)
    db.commit()
    db.refresh(new_delivery)

    return new_delivery

class UserDeliveryRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"

@router.get("/my", response_model=DeliveryPaginatedResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def get_my_deliveries(
        request: Request,
        role: UserDeliveryRole = Query(UserDeliveryRole.BUYER, description="buyer = my purchases, seller = my sales"),
        page: int = Query(1, ge=1, description="Number of page(starts with 1)"),
        size: int = Query(10, ge=1, le = 20, description="Amount of items in page(max 20)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if role == UserDeliveryRole.BUYER:
        query_delivery = db.query(Delivery).filter(Delivery.email == current_user.email)
    else:
        query_delivery = db.query(Delivery).join(Item, Delivery.item_id == Item.id).filter(Item.user_id == current_user.id)

    total = query_delivery.count()

    offset = (page - 1) * size

    items = query_delivery.offset(offset).limit(size).all()

    total_pages = math.ceil(total/size) if total > 0 else 1

    return DeliveryPaginatedResponse(
        delivery = items,
        total = total,
        page=page,
        size=size,
        pages=total_pages
    )

@router.get("/{delivery_id}", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def get_delivery(request: Request, delivery_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    item = db.query(Item).filter(Item.id == delivery.item_id).first()
    seller_id = item.user_id

    is_buyer = (current_user.email == delivery.email)
    is_seller = (current_user.id == seller_id)

    if not(is_buyer or is_seller):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no access"
        )
    return delivery

@router.patch("/{delivery_id}/status", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
def update_delivery_status(delivery_id: uuid.UUID, new_status: DeliveryStatus, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    delivery.status = new_status.value
    if new_status == DeliveryStatus.DELIVERED:
        payment = db.query(Payment).filter(Payment.item_id == delivery.item_id).first()
        if payment:
            payment.status = "completed"

    db.commit()
    db.refresh(delivery)

    return delivery










