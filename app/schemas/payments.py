
import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict,  Field
from app.models.payments import OrderStatus

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
