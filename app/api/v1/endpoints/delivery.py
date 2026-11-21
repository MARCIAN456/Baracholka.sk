import hmac
import uuid
import math

import stripe

from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from enum import Enum

from app.api.deps import get_current_user, get_db
from app.models.item import Item
from app.schemas.delivery import DeliveryResponse, DeliveryCreate, DeliveryStatus, DeliveryPaginatedResponse, \
    PacketaWebhookPayload
from app.models.delivery import Delivery
from app.models.payments import OrderStatus, Payout, PayoutStatus
from app.models.user import User
from app.core.limiter import limiter

router = APIRouter()

ITEM_WEIGHT_KG = {
    "under_1kg": 1.0,
    "1_to_5kg": 5.0,
    "5_to_15kg": 15.0,
    "15_to_30kg": 30.0,
}

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
    existing_delivery = db.query(Delivery).filter(
        Delivery.item_id == item_id,
        Delivery.buyer_id == current_user.id,
        Delivery.status != DeliveryStatus.RETURNED.value
    ).first()
    weight = ITEM_WEIGHT_KG.get(item.weight, 5.0)

    if existing_delivery:
        if existing_delivery.payment and existing_delivery.payment.status in (OrderStatus.PAID.value, OrderStatus.COMPLETED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery is already paid"
            )

        existing_delivery.username = body.username
        existing_delivery.email = current_user.email
        existing_delivery.phone = body.phone
        existing_delivery.addressId = body.addressId
        existing_delivery.weight = weight
        existing_delivery.value = item.price

        db.commit()
        db.refresh(existing_delivery)

        return existing_delivery


    new_delivery = Delivery(
        username = body.username,
        email = current_user.email,
        phone=body.phone,
        addressId=body.addressId,
        weight=weight,
        value=item.price,
        status=DeliveryStatus.DRAFT.value,
        item_id=item_id,
        buyer_id=current_user.id
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
        query_delivery = db.query(Delivery).filter(Delivery.buyer_id == current_user.id)
    else:
        query_delivery = db.query(Delivery).join(Delivery.item).filter(Item.user_id == current_user.id, Delivery.status != DeliveryStatus.DRAFT.value)

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

@router.get("/{delivery_id}", response_model=DeliveryResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def get_delivery(request: Request, delivery_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    is_buyer = (current_user.id == delivery.buyer_id)
    is_seller = (delivery.item and current_user.id == delivery.item.user_id)

    if not(is_buyer or is_seller):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have no access"
        )
    return delivery

@router.post("/packeta_webhook", status_code=status.HTTP_200_OK)
def packeta_webhook(
        payload: PacketaWebhookPayload,
        request: Request,
        db: Session = Depends(get_db)
):
    token = request.headers.get("X-Packeta-Token")
    if not hmac.compare_digest(token or "", settings.PACKETA_WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN
        )
    clean_barcode = payload.barcode.replace(" ", "")
    delivery = db.query(Delivery).filter(Delivery.tracking_number == clean_barcode).first()

    if not delivery:
        return {"status": "ignored", "reason": "Delivery not found"}

    if payload.statusCode == 7:
        delivery.status = DeliveryStatus.DELIVERED.value
        if delivery.payment:
            delivery.payment.status = OrderStatus.COMPLETED.value
            if not delivery.payment.payout and delivery.item:
                seller = delivery.item.owner
                if seller:
                    seller_iban = seller.iban

                    new_payout = Payout(
                        payment_id=delivery.payment.id,
                        seller_id=delivery.item.user_id,
                        amount=delivery.payment.amount,
                        iban=seller_iban,
                        status=PayoutStatus.PENDING.value,
                    )
                    db.add(new_payout)

        db.commit()
        return {"status": "delivered"}

    if payload.statusCode == 10:
        if delivery.payment and delivery.payment.status == OrderStatus.REFUNDED.value:
            return {"status": "already_refunded"}

        if delivery.payment:
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                session = stripe.checkout.Session.retrieve(delivery.payment.stripe_session_id)
                if session.payment_intent:
                    stripe.Refund.create(payment_intent=session.payment_intent)

                delivery.payment.status = OrderStatus.REFUNDED.value
            except stripe.error.StripeError as e:
                db.rollback()

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Stripe refund error: {str(e)}"
                )


        delivery.status = DeliveryStatus.RETURNED.value
        if delivery.item:
            delivery.item.is_sold = False
        db.commit()
        return {"status": "returned_and_refunded"}





















