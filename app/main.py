# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import engine, Base, get_db
from app.api.v1.endpoints import auth, users, products, carts, orders, payments, coupons, recommendations

settings = get_settings()

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup Logic
    # Create Database Tables (includes the new 'carts' and 'orders' tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Yield control
    yield
    
    # 3. Shutdown Logic
    pass
# ----------------------------------

# Initialize App
app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["Authentication"])
app.include_router(users.router, prefix=settings.API_V1_STR + "/users", tags=["User Management"])
app.include_router(products.router, prefix=settings.API_V1_STR + "/products", tags=["Product Catalog"])
app.include_router(carts.router, prefix=settings.API_V1_STR + "/cart", tags=["Cart"])
app.include_router(orders.router, prefix=settings.API_V1_STR + "/orders", tags=["Orders"])
app.include_router(payments.router, prefix=settings.API_V1_STR + "/payments", tags=["Payments"])
app.include_router(coupons.router, prefix=settings.API_V1_STR + "/coupons", tags=["Coupons"])
app.include_router(recommendations.router, prefix=settings.API_V1_STR + "/recommendations", tags=["Recommendations"])

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "detail": str(e)}

@app.get("/")
async def root():
    return {"message": "Welcome to the E-Commerce API", "docs": "/docs"}