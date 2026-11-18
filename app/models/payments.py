import uuid
from datetime import date
from enum import Enum

from sqlalchemy import Column, String, Float, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class OrderStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    PAID = "paid"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"

class PayoutStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REJECTED = "rejected"
    FAILED = "failed"

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
    payout = relationship("Payout", back_populates="payment", uselist=False)

    item = relationship("Item")
    buyer = relationship("User")

class Payout(Base):
    __tablename__ = "payout"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_id = Column(Uuid, ForeignKey("payment.id", ondelete="CASCADE"), unique=True, nullable=False)
    seller_id = Column(Uuid, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    iban = Column(String(50), nullable=True)
    status = Column(String(50), default=PayoutStatus.PENDING.value, nullable=False)
    paidAt = Column(Date, nullable=True)
    stripe_transfer_id = Column(String(255), nullable=True)
    createdAt = Column(Date, default=date.today)
    payment = relationship("Payment", back_populates="payout")
    seller = relationship("User")
