# app/api/v1/endpoints/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
import uuid

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import ProductVariant
from app.models.cart import Cart
from app.models.coupon import Coupon, DiscountType # <--- NEW IMPORT
from app.schemas.order import CheckoutRequest, OrderResponse, OrderItemResponse
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()

@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    1. Get Cart
    2. Validate Coupon (If provided)
    3. Validate Inventory (Lock Rows)
    4. Calculate Total
    5. Apply Discount
    6. Create Order
    7. Deduct Inventory & Update Coupon Usage
    8. Clear Cart
    """
    
    # 1. Retrieve Cart
    cart_result = await db.execute(select(Cart).filter(Cart.session_id == request.session_id))
    cart = cart_result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart is empty or not found")
        
    items_data = cart.items # List of dicts
    
    if not items_data:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # --- NEW: DISCOUNT LOGIC START ---
    coupon = None
    discount_amount = Decimal("0.00")
    
    if request.coupon_code:
        coupon_code = request.coupon_code.upper()
        c_result = await db.execute(select(Coupon).filter(Coupon.code == coupon_code))
        coupon = c_result.scalar_one_or_none()
        
        if not coupon:
            raise HTTPException(status_code=404, detail="Invalid coupon code")
            
        if not coupon.is_active:
            raise HTTPException(status_code=400, detail="Coupon is inactive")
            
        if coupon.max_uses and coupon.usage_count >= coupon.max_uses:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")
            
    # We will calculate the specific amount after we get the raw total
    # --- DISCOUNT LOGIC PREP END ---
        
    # 2. Start Transaction & Lock Inventory
    variant_ids = [uuid.UUID(item["variant_id"]) for item in items_data]
    
    # Query variants WITH lock
    stmt = select(ProductVariant).filter(
        ProductVariant.id.in_(variant_ids)
    ).with_for_update()
    
    result = await db.execute(stmt)
    variants = result.scalars().all()
    
    # Map to dict
    variant_map = {v.id: v for v in variants}
    
    order_items_to_create = []
    total_amount = Decimal("0.00")
    
    # 3. Validate and Calculate Raw Total
    for item in items_data:
        v_id = uuid.UUID(item["variant_id"])
        qty = item["quantity"]
        
        if v_id not in variant_map:
            raise HTTPException(status_code=400, detail=f"Variant {v_id} not found")
            
        variant = variant_map[v_id]
        
        if variant.inventory_count < qty:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for SKU {variant.sku}. Available: {variant.inventory_count}, Requested: {qty}"
            )
            
        line_total = variant.price * qty
        total_amount += line_total
        
        order_items_to_create.append(OrderItem(
            variant_id=v_id,
            quantity=qty,
            unit_price=variant.price
        ))
    
    # --- NEW: APPLY DISCOUNT START ---
    if coupon:
        if coupon.discount_type == DiscountType.PERCENTAGE:
            # Calculate percentage
            discount_amount = total_amount * (coupon.value / Decimal("100"))
        else:
            # Fixed amount
            discount_amount = coupon.value
        
        total_amount -= discount_amount
        
        # Ensure total doesn't go negative (unless we want free items, which is fine)
        if total_amount < 0:
            total_amount = Decimal("0.00")
            
        # Increment usage count immediately
        coupon.usage_count += 1
    # --- APPLY DISCOUNT END ---
    
    # 4. Create Order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount, # Final discounted amount
        status=OrderStatus.CREATED,
        shipping_address=request.shipping_address,
        items=order_items_to_create
    )
    
    db.add(order)
    
    # 5. Update Inventory (Commit happens here)
    for item in items_data:
        v_id = uuid.UUID(item["variant_id"])
        variant_map[v_id].inventory_count -= item["quantity"]
        
        # Optional: Broadcast real-time update
        try:
            from app.api.v1.endpoints.websocket import manager
            await manager.broadcast(str(variant_map[v_id].product_id), {
                "event": "stock_update",
                "variant_id": str(v_id),
                "new_stock": variant_map[v_id].inventory_count
            })
        except ImportError:
            pass

    await db.commit()
    
    # 6. REFRESH FIX (MissingGreenlet Error)
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items)) 
        .filter(Order.id == order.id)
    )
    order = result.scalar_one()
    
    # 7. Clear Cart
    cart.items = []
    flag_modified(cart, "items") 
    await db.commit()
    
    return order

@router.get("/", response_model=list[OrderResponse])
async def list_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()

# Simple Admin view for all orders
@router.get("/admin/all", response_model=list[OrderResponse])
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()