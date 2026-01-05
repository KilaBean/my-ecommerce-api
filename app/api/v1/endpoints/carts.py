# app/api/v1/endpoints/carts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified  # CRITICAL: To save JSONB changes
from app.database import get_db
from app.models.cart import Cart 
from app.models.product import ProductVariant
from app.schemas.order import CartItem, CartResponse
from app.models.user import User
from app.api.deps import get_current_user
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=CartResponse)
async def get_cart(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve cart items for a given session_id.
    """
    result = await db.execute(select(Cart).filter(Cart.session_id == session_id))
    cart = result.scalar_one_or_none()
    
    if not cart:
        return CartResponse(session_id=session_id, items=[])
    
    return CartResponse(session_id=cart.session_id, items=cart.items)

@router.post("/add")
async def add_to_cart(item: CartItem, session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Add or update an item in cart.
    """
    # 1. Get Cart
    result = await db.execute(select(Cart).filter(Cart.session_id == session_id))
    cart = result.scalar_one_or_none()
    
    # 2. If cart doesn't exist, create it
    if not cart:
        cart = Cart(session_id=session_id, items=[])
        db.add(cart)
        await db.flush() # Flush to assign an ID before we work on the object
    
    # 3. Validate Variant exists (Optional, but good for error handling)
    v_result = await db.execute(select(ProductVariant).filter(ProductVariant.id == item.variant_id))
    if not v_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Variant not found")
        
    # 4. Logic: Update quantity if item exists, else append new item
    # 'items' is a Python list of dicts
    current_items = cart.items
    
    # Safety check if items is None (unlikely but possible)
    if current_items is None:
        current_items = []
        
    found = False
    for i in current_items:
        # Ensure we compare UUIDs correctly (convert JSON string back to UUID for comparison)
        if UUID(i["variant_id"]) == item.variant_id:
            i["quantity"] += item.quantity
            found = True
            break
            
    if not found:
        current_items.append({
            "variant_id": str(item.variant_id),
            "quantity": item.quantity
        })
    
    # 5. Save Changes
    # First, re-assign list to model
    cart.items = current_items
    
    # Second, TELL SQLAlchemy to update this specific column (Fixes "Empty Cart" issue)
    flag_modified(cart, "items")
    
    await db.commit()
    return {"message": "Item added", "items": cart.items}

@router.delete("/")
async def clear_cart(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Clear all items in cart.
    """
    result = await db.execute(select(Cart).filter(Cart.session_id == session_id))
    cart = result.scalar_one_or_none()
    
    if cart:
        cart.items = []
        flag_modified(cart, "items") # Ensure this triggers update
        await db.commit()
        
    return {"message": "Cart cleared"}