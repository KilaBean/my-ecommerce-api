# app/schemas/order.py
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.models.order import OrderStatus

class CartItemBase(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)

class CartItem(CartItemBase):
    pass

class CartResponse(BaseModel):
    session_id: str
    items: List[CartItem] = []

class OrderItemResponse(BaseModel):
    id: UUID
    variant_id: UUID
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: Decimal
    status: OrderStatus
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# --- UPDATED CHECKOUT REQUEST ---
class CheckoutRequest(BaseModel):
    session_id: str
    shipping_address: str
    coupon_code: Optional[str] = None # <--- NEW FIELD