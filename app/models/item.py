import uuid
from datetime import date
from enum import Enum
from sqlalchemy import Column, String, Float, Boolean, Text, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class ItemCategory(str, Enum):
    ELECTRONICS = "electronics"
    HOME = "home"
    FASHION = "fashion"
    SPORT = "sport"
    OTHER = "other"

class ItemWeight(str, Enum):
    LIGHT = "under_1kg"
    MEDIUM = "1_to_5kg"
    HEAVY = "5_to_15kg"
    EXTRA_HEAVY = "15_to_30kg"


class Item(Base):
    __tablename__ = "item"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True,)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_sold = Column(Boolean, default=False)
    category = Column(String(50), default=ItemCategory.OTHER.value, nullable=False)
    weight = Column(String(20), server_default="1_to_5kg", nullable=False)
    createdAt = Column(Date, default=date.today)

    images = relationship("ItemImage", cascade="all, delete-orphan")

    user_id = Column(Uuid, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="items")