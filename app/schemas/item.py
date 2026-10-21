import uuid
from datetime import date


from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse



class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=30)
    description: str | None = Field(..., min_length=30, max_length=2000)
    price: float = Field(..., gt=0)


class ItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    price: float
    is_sold: bool
    createdAt: date
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ItemDetailedResponse(ItemResponse):
    owner: UserResponse

class ItemPaginatedResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    size: int
    pages: int

class ItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=30)
    description: str | None = Field(None, min_length=30, max_length=2000)
    price: float = Field(None, gt=0)


