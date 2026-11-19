import uuid
from datetime import date
from app.models.item import ItemCategory, ItemWeight

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserPublicResponse



class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=30)
    description: str | None = Field(..., min_length=30, max_length=2000)
    price: float = Field(..., gt=0, le=100_000)
    category: ItemCategory = ItemCategory.OTHER
    weight: ItemWeight = Field(..., description="Вагова категорія товару (обов'язково)")

class ItemImageResponse(BaseModel):
    id: uuid.UUID
    image_url: str

    model_config = ConfigDict(from_attributes=True)

class ItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    price: float
    is_sold: bool
    category: ItemCategory
    weight: ItemWeight
    createdAt: date
    user_id: uuid.UUID
    images: list[ItemImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ItemDetailedResponse(ItemResponse):
    owner: UserPublicResponse

class ItemPaginatedResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    size: int
    pages: int

class ItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=30)
    description: str | None = Field(None, min_length=30, max_length=2000)
    price: float | None = Field(None, gt=0, le=100_000)
    category: ItemCategory | None = None
    weight: ItemWeight | None = None




