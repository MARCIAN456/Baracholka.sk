import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.models.delivery import DeliveryStatus

class DeliveryCreate(BaseModel):
    username: str = Field(..., max_length=100, description="Ім'я отримувача", examples=["Markiian"])
    email: EmailStr = Field(..., description="Email отримувача", examples=["user@example.com"])
    phone: str = Field(..., pattern=r"^\+?[0-9]{9,15}$", description="Номер телефону", examples=["+421912345678"])
    addressId: str = Field(..., max_length=50, description="ID пункту видачі Packeta", examples=["1234"])
    weight: float = Field(..., gt=0, description="Вага в кг", examples=[1.5])
    value: float = Field(..., gt=0, description="Страхова вартість в євро", examples=[420.0])


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
