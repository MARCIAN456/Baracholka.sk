import uuid
from datetime import date

from sqlalchemy import Column, String, Float, Boolean, Text, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    username = Column(String(30), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String, server_default="USER", nullable=False)
    createdAt = Column(Date, default=date.today)

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")


