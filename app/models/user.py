import uuid
from datetime import date

from sqlalchemy import Column, String, Uuid, Date
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    username = Column(String(30), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String, server_default="USER", nullable=False)
    city = Column(String(50), server_default="Košice", nullable=False)
    country = Column(String(50), server_default="Slovakia", nullable=False)
    createdAt = Column(Date, default=date.today)
    iban = Column(String(50), nullable=True)
    stripe_account_id = Column(String(255), nullable=True)

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    deliveries= relationship("Delivery", back_populates="buyer")


