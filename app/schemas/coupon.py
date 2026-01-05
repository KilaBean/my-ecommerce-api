# app/schemas/coupon.py
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from app.models.coupon import DiscountType
from datetime import datetime

class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_type: DiscountType
    value: Decimal = Field(gt=0)
    max_uses: int = Field(default=1, gt=0)

class CouponResponse(BaseModel):
    id: UUID
    code: str
    discount_type: DiscountType
    value: Decimal
    is_active: bool
    usage_count: int

    class Config:
        from_attributes = True