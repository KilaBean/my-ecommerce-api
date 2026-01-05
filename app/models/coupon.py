# app/models/coupon.py
import uuid
import enum
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"

class Coupon(Base):
    __tablename__ = "coupons"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType), default=DiscountType.PERCENTAGE)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2)) # e.g. 10.00% or $20.00
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    max_uses: Mapped[int] = mapped_column(nullable=True) # Max times it can be used
    usage_count: Mapped[int] = mapped_column(default=0)