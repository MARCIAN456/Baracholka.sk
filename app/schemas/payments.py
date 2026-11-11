
import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict,  Field
from app.models.payments import OrderStatus, PayoutStatus


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class PaymentResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    buyer_id: uuid.UUID
    amount: float = Field(..., gt=0, le=100_000)
    status: OrderStatus = Field(...)
    createdAt: date

    model_config = ConfigDict(from_attributes=True)

class PayoutResponse(BaseModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    seller_id: uuid.UUID
    amount: float
    iban: str | None = None
    status: PayoutStatus
    paidAt: date | None = None
    stripe_transfer_id: str | None = None
    createdAt: date

    model_config = ConfigDict(from_attributes=True)

class PayoutPaginatedResponse(BaseModel):
    payouts: list[PayoutResponse]
    total: int
    page: int
    size: int
    pages: int
