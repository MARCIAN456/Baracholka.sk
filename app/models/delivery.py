import uuid
from datetime import date
from sqlalchemy import Column, String, Float, Uuid, Date
from sqlalchemy.orm import relationship

from app.models.base import Base
from enum import Enum

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    READY_FOR_PICKUP = "ready_for_pickup"
    DELIVERED = "delivered"
    RETURNED = "returned"

class Delivery(Base):
    __tablename__ = "delivery"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), server_default="+421900000000", nullable=False)
    addressId = Column(String(50), nullable=False)
    weight = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    item_id = Column(Uuid, nullable=False)

    payment = relationship("Payment", back_populates="delivery", uselist=False)

    tracking_number = Column(String(100), nullable=True)
    status = Column(String(50), default=DeliveryStatus.PENDING.value, nullable=False)
    createdAt = Column(Date, default=date.today)