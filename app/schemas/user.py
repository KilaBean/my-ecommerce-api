# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole
from typing import Optional
from uuid import UUID

# Base Schema
class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: UserRole = UserRole.USER

# Schema for creating a user
class UserCreate(UserBase):
    password: str

# Schema for response (hide password)
class UserResponse(UserBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True

# Schema for Login
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for Token Response
class Token(BaseModel):
    access_token: str
    token_type: str

# Add this new schema for updating user role
class UserUpdateRole(BaseModel):
    role: UserRole

    class Config:
        use_enum_values = True