import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.models.delivery import DeliveryStatus

class DeliveryCreate(BaseModel):
    username: str = Field(..., max_length=100, description="Recipient name", examples=["Markiian"])
    phone: str = Field(..., pattern=r"^\+?[0-9]{9,15}$", description="Phone number", examples=["+421912345678"])
    addressId: str = Field(..., max_length=50, description="Packeta pickup point ID", examples=["1234"])


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    phone: str
    addressId: str
    weight: float
    value: float
    tracking_number: str | None = None
    status: DeliveryStatus
    item_id: uuid.UUID
    createdAt: date
    model_config = ConfigDict(from_attributes=True)

class DeliveryPaginatedResponse(BaseModel):
    delivery: list[DeliveryResponse]
    total: int
    page: int
    size: int
    pages: int

class PacketaWebhookPayload(BaseModel):
    packetId: str
    barcode: str
    statusCode: int
    statusText: str | None = None
