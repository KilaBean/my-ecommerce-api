# app/api/v1/endpoints/coupons.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponResponse
from app.api.deps import get_current_admin
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    coupon_in: CouponCreate, 
    db: AsyncSession = Depends(get_db), 
    current_admin: User = Depends(get_current_admin)
):
    # Check if code exists
    result = await db.execute(select(Coupon).filter(Coupon.code == coupon_in.code.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Coupon code already exists")
        
    coupon = Coupon(
        code=coupon_in.code.upper(),
        discount_type=coupon_in.discount_type,
        value=coupon_in.value,
        max_uses=coupon_in.max_uses
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon

@router.get("/", response_model=list[CouponResponse])
async def list_coupons(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Coupon))
    return result.scalars().all()