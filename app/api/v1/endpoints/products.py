# app/api/v1/endpoints/products.py
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import List

from app.database import get_db
from app.models.product import Product, Category, ProductVariant
from app.schemas.product import (
    ProductCreate, ProductResponse, 
    CategoryCreate, CategoryResponse,
    ProductVariantBase # We use this base for creating variants
)
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.api.v1.endpoints.websocket import manager

router = APIRouter()

# --- Helper Schema for Stock Update ---
class StockUpdate(BaseModel):
    stock: int = Field(ge=0, description="New inventory count")

# --- Categories ---

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate, 
    db: AsyncSession = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    category = Category(**category_in.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()

# --- Products ---

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate, 
    db: AsyncSession = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    # 1. Verify category exists
    cat_result = await db.execute(select(Category).filter(Category.id == product_in.category_id))
    if not cat_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Category not found")

    # 2. Create Product Object
    product = Product(
        name=product_in.name,
        description=product_in.description,
        category_id=product_in.category_id,
        is_active=product_in.is_active
    )
    
    # 3. Add variants if provided
    for v_data in product_in.variants:
        # We instantiate the variant. SQLAlchemy will link the product_id automatically
        # after we add it to the list and flush/commit.
        # Note: We don't have the product ID yet in Python memory, but the relationship handles it.
        variant = ProductVariant(**v_data.model_dump()) 
        product.variants.append(variant)

    db.add(product)
    await db.commit()
    
    # --- FIX START (MissingGreenlet Error) ---
    # We must re-fetch the product with variants explicitly loaded.
    # If we try to return 'product' directly, Pydantic triggers a lazy load 
    # for variants, which fails in async mode.
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.variants)) 
        .filter(Product.id == product.id)
    )
    product = result.scalar_one()
    # --- FIX END ---

    return product

@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    # Use selectinload to get variants in the same query (prevent N+1 problems)
    result = await db.execute(
        select(Product).options(selectinload(Product.variants)).offset(skip).limit(limit)
    )
    return result.scalars().all()

# --- Inventory Management with Row Locking ---

@router.patch("/variants/{variant_id}/stock")
async def update_stock(
    variant_id: str,
    stock_data: StockUpdate, # Now accepts a JSON body
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # 1. Lock the row. This prevents two admins (or an admin and an order) 
    # from updating stock at the exact same time (Race Condition).
    # Note: We do NOT use 'async with db.begin()' here because get_db already started a transaction.
    
    stmt = select(ProductVariant).filter(ProductVariant.id == variant_id).with_for_update()
    result = await db.execute(stmt)
    variant = result.scalar_one_or_none()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    old_stock = variant.inventory_count
    variant.inventory_count = stock_data.stock
    
    # 2. Commit the changes
    await db.commit()
    
    # 3. Broadcast update via WebSocket
    # We use the product_id because clients usually subscribe to a Product, not a specific Variant ID
    await manager.broadcast(str(variant.product_id), {
        "event": "stock_update",
        "variant_id": str(variant.id),
        "old_stock": old_stock,
        "new_stock": stock_data.stock
    })

    return {"variant_id": str(variant.id), "old_stock": old_stock, "new_stock": stock_data.stock}

# --- WebSocket Endpoint ---
# Usage: ws://localhost:8000/api/v1/products/ws/inventory/{product_id}
@router.websocket("/ws/inventory/{product_id}")
async def websocket_inventory(websocket: WebSocket, product_id: str):
    await manager.connect(websocket, product_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Optional: handle ping/pong logic here
    except WebSocketDisconnect:
        manager.disconnect(websocket, product_id)