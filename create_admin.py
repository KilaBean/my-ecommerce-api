# create_admin.py
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(select(User).filter(User.username == "admin"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Admin user already exists.")
            return

        # Create Admin
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),  # CHANGE THIS AFTER LOGIN
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        await db.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Please log in and change this password immediately.")

if __name__ == "__main__":
    asyncio.run(create_admin())