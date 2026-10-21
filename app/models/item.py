import uuid
from datetime import date

from sqlalchemy import Column, String, Float, Boolean, Text, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Item(Base):
    __tablename__ = "item"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True,)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_sold = Column(Boolean, default=False)
    createdAt = Column(Date, default=date.today)

    user_id = Column(Uuid, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="items")