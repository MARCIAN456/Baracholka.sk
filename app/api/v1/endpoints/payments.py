import uuid
import random
import stripe
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.core.limiter import limiter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.payments import CheckoutSessionResponse
from app.models.user import User
from app.models.item import Item
from app.models.payments import Payment, OrderStatus
from app.models.delivery import Delivery

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

    delivery = db.query(Delivery).filter(Delivery.item_id == item_id, Delivery.email == current_user.email).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please fill in delivery info"
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

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
                    "unit_amount": int(item.price * 100),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "item_id": str(item.id),
            "buyer_id": str(current_user.id),
        },
        success_url="http://localhost:8000/api/v1/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:8000/api/v1/payments/cancel?session_id={CHECKOUT_SESSION_ID}",
    )

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

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    # 1. Читаємо байти запиту
    payload = await request.body()
    # 2. Отримуємо цифровий підпис від Stripe
    sig_header = request.headers.get("stripe-signature")
    # 3. Перевіряємо, чи лист справжній
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Помилка: тіло запиту пошкоджене
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Помилка: цифровий підпис не зійшовся (лист фальшивий)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    # 4. Перевіряємо тип події: чи це успішна оплата
    if event.type == "checkout.session.completed":
        session = event.data.object
        session_id = session.id

        payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()

        if payment:
            payment.status = OrderStatus.PAID.value

            item = db.query(Item).filter(Item.id == payment.item_id).first()
            buyer = db.query(User).filter(User.id == payment.buyer_id).first()

            if item:
                item.is_sold = True

                delivery = db.query(Delivery).filter(Delivery.item_id == payment.item_id, Delivery.email == buyer.email).first()

                if delivery and not delivery.tracking_number:
                    delivery.tracking_number = f"Z{random.randint(100000000, 999999999)}"

                db.query(Delivery).filter(Delivery.item_id == payment.item_id, Delivery.email != buyer.email).delete()
    if event.type == "checkout.session.expired":

        session = event.data.object
        session_id = session.id

        payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()

        if payment:
            payment.status = OrderStatus.CANCELLED.value

            item = db.query(Item).filter(Item.id == payment.item_id).first()

            if item:
                item.is_sold = False


    db.commit()


    # 5. Завжди обов'язково відповідаємо Stripe успіхом 200 OK
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




