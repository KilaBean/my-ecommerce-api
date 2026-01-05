# app/models/cart.py
import uuid
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Cart(Base):
    __tablename__ = "carts"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True) # Unique cart ID
    items: Mapped[dict] = mapped_column(JSON, default=[]) # Stores the list: [{"variant_id": "...", "quantity": 1}]