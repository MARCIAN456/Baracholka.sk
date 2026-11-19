import uuid
import random
import math
import stripe
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.core.limiter import limiter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.payments import CheckoutSessionResponse, PayoutPaginatedResponse
from app.models.user import User
from app.models.item import Item
from app.models.payments import Payment, OrderStatus, Payout
from app.models.delivery import Delivery, DeliveryStatus

router = APIRouter()


@router.post("/create-checkout-session/{item_id}", response_model=CheckoutSessionResponse)
@limiter.limit("10/minute")
def create_checkout_session(request: Request, item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if item.is_sold == True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is sold"
        )

    if current_user.id == item.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cant buy your own item"
        )

    delivery = db.query(Delivery).filter(
        Delivery.item_id == item_id,
        Delivery.buyer_id == current_user.id,
        Delivery.status != DeliveryStatus.RETURNED.value
    ).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please fill in delivery info"
        )

    if delivery.payment and delivery.payment.status in (OrderStatus.PAID.value, OrderStatus.COMPLETED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cant pay for product more than one time"
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if delivery.payment and delivery.payment.status == OrderStatus.PENDING.value:
        try:
            old_session = stripe.checkout.Session.retrieve(delivery.payment.stripe_session_id)
            if old_session.status == "complete":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment for this item is already being processed"
                )
            if old_session.status == "open":
                stripe.checkout.Session.expire(old_session.id)
        except stripe.error.StripeError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment provider error, please try again"
            )

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": item.title,
                        "description": item.description,
                    },
                    "unit_amount": int(round(item.price * 100)),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "item_id": str(item.id),
            "buyer_id": str(current_user.id),
        },
        success_url=f"{settings.PUBLIC_API_URL}/api/v1/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.PUBLIC_API_URL}/api/v1/payments/cancel?session_id={{CHECKOUT_SESSION_ID}}",
    )
    if delivery.payment and delivery.payment.status in (OrderStatus.PENDING.value, OrderStatus.CANCELLED.value):
        delivery.payment.stripe_session_id = session.id
        delivery.payment.amount = item.price
        delivery.payment.status = OrderStatus.PENDING.value
        db.commit()
    else:
        new_payment = Payment(
            item_id = item_id,
            buyer_id = current_user.id,
            amount = item.price,
            stripe_session_id = session.id,
            status = OrderStatus.PENDING.value,
            delivery_id = delivery.id
        )

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

    return CheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id
    )

async def get_raw_body(request: Request) -> bytes:
    return await request.body()


@router.post("/webhook")
def stripe_webhook(request: Request, payload: bytes = Depends(get_raw_body), db: Session = Depends(get_db)):
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        session_id = session.id

        payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()

        if payment:
            if payment.status in (OrderStatus.PAID.value, OrderStatus.COMPLETED.value, OrderStatus.REFUNDED.value):
                return {"status": "already_processed"}
            if payment.item and payment.item.is_sold:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                if session.payment_intent:
                    try:
                        stripe.Refund.create(
                            payment_intent=session.payment_intent,
                            idempotency_key=f"refund-{session.id}",
                        )
                    except stripe.error.StripeError as e:
                        if getattr(e, "code", None) != "charge_already_refunded":
                            raise HTTPException(
                                status_code=status.HTTP_502_BAD_GATEWAY,
                                detail="Refund failed"
                            )

                payment.status = OrderStatus.REFUNDED.value
                db.commit()
                return {"status": "item_already_sold_refunded"}

            payment.status = OrderStatus.PAID.value
            if payment.item:
                payment.item.is_sold = True
            if payment.delivery:
                payment.delivery.status = DeliveryStatus.PENDING.value

                if not payment.delivery.tracking_number:
                    payment.delivery.tracking_number = f"Z{random.randint(100000000, 999999999)}"

                db.query(Delivery).filter(
                    Delivery.item_id == payment.item_id,
                    Delivery.id != payment.delivery_id,
                    Delivery.status == DeliveryStatus.DRAFT.value
                ).delete()
    if event.type == "checkout.session.expired":

        session = event.data.object
        session_id = session.id

        payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()

        if payment and payment.status == OrderStatus.PENDING.value:
            payment.status = OrderStatus.CANCELLED.value


    db.commit()


    return {"status": "success"}


@router.get("/success")
def payment_success(session_id: str = None):
    return {
        "status": "success",
        "message": "Оплата успішна! Кошти заморожено на платформі. Очікуйте відправку через Packeta.",
        "session_id": session_id
    }


@router.get("/cancel")
def payment_cancel(session_id: str = None):
    return {
        "status": "cancelled",
        "message": "Оплату скасовано.",
        "session_id": session_id
    }

@router.get("/payouts/my", response_model=PayoutPaginatedResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def get_my_payouts(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        page: int = Query(1, ge=1, description="Number of page(starts with 1)"),
        size: int = Query(10, ge=1, le=20, description="Amount of items on page (max 20)"),
):
    payout_query = db.query(Payout).filter(Payout.seller_id == current_user.id)

    payout_query = payout_query.order_by(Payout.createdAt.desc())


    total = payout_query.count()

    offset = (page - 1) * size

    items = payout_query.offset(offset).limit(size).all()

    total_pages = math.ceil(total/size) if total > 0 else 1

    return PayoutPaginatedResponse(
        payouts = items,
        total = total,
        page=page,
        size=size,
        pages=total_pages
    )





