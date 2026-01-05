# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRole
from app.api.deps import get_current_admin

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # Only Admins can list users
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str, # UUID as string
    role_update: UserUpdateRole,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # Only Admins
):
    # Find the user to update
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role
    user.role = role_update.role
    await db.commit()
    await db.refresh(user)
    
    return user