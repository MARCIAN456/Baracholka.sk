import uuid
from app.models.base import Base
from sqlalchemy import Column, String, Uuid, Date, ForeignKey
from sqlalchemy.orm import relationship

class ItemImage(Base):
    __tablename__ = "item_image"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    item_id = Column(Uuid, ForeignKey("item.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    public_id = Column(String(250), nullable=False)
