# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.models.user import User, UserRole # <--- Import UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from sqlalchemy import select
from datetime import timedelta # <--- Import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == user_in.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # --- START OF CHANGES ---
    # Set expiry based on role
    if user.role == UserRole.ADMIN:
        access_token_expires = timedelta(days=3) # Admins get 3 days
    else:
        access_token_expires = timedelta(days=7) # Users get 7 days

    access_token = create_access_token(
        subject=str(user.id), 
        expires_delta=access_token_expires
    )
    # --- END OF CHANGES ---
    
    return {"access_token": access_token, "token_type": "bearer"}