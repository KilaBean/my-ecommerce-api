# app/schemas/product.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: UUID

    class Config:
        from_attributes = True

class VariantAttribute(BaseModel):
    # Dynamic attributes like color, size, etc.
    pass 

class ProductVariantBase(BaseModel):
    sku: str
    price: Decimal = Field(gt=0)
    inventory_count: int = Field(ge=0)
    attributes: Dict[str, str] = {} # e.g. {"color": "Red"}

class ProductVariantCreate(ProductVariantBase):
    product_id: UUID

class ProductVariantResponse(ProductVariantBase):
    id: UUID
    product_id: UUID

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID
    is_active: bool = True

class ProductCreate(ProductBase):
    variants: List[ProductVariantBase] = [] # Allow creating variants with product

class ProductResponse(ProductBase):
    id: UUID
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True