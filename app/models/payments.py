import uuid
from datetime import date
from enum import Enum

from sqlalchemy import Column, String, Float, Boolean, Text, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    PAID = "paid"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class Payment(Base):
    __tablename__ = "payment"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    item_id = Column(Uuid, ForeignKey("item.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(Uuid, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    stripe_session_id = Column(String(255), nullable=False)
    status = Column(String(50), default=OrderStatus.PENDING.value, nullable=False)
    createdAt = Column(Date, default=date.today)

    delivery_id = Column(Uuid, ForeignKey("delivery.id", ondelete="SET NULL"), unique=True, nullable=True)
    delivery = relationship("Delivery", back_populates="payment")

    item = relationship("Item")
    buyer = relationship("User")
    