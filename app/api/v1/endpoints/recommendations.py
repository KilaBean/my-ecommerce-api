# app/api/v1/endpoints/recommendations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductResponse
from typing import List

router = APIRouter()

@router.get("/{product_id}", response_model=List[ProductResponse])
async def get_recommendations(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns 4 other products in the same category as the provided product_id.
    """
    # 1. Find the current product to get its category
    product_result = await db.execute(select(Product).filter(Product.id == product_id))
    current_product = product_result.scalar_one_or_none()
    
    if not current_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 2. Find related products (Same category, NOT the current product)
    # Limit to 4 recommendations
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.variants)) # We need variants for price/images
        .filter(Product.category_id == current_product.category_id)
        .filter(Product.id != current_product.id)
        .limit(4)
    )
    
    recommendations = result.scalars().all()
    return recommendations