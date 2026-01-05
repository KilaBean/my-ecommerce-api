# app/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
import stripe
import os
import uuid

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User # Import User to fetch email
from app.schemas.order import OrderResponse # Import for email payload
from app.api.deps import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from decimal import Decimal

# IMPORT EMAIL FUNCTION
from app.core.email import send_order_confirmation_email

router = APIRouter()

# Initialize Stripe with key from config
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- Schemas ---
class CreatePaymentIntent(BaseModel):
    order_id: uuid.UUID

# --- Endpoints ---

@router.post("/create-intent")
async def create_payment_intent(
    data: CreatePaymentIntent,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a Stripe Payment Intent for a specific Order.
    Frontend uses 'client_secret' from response to confirm payment.
    """
    # 1. Find Order
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == data.order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # 2. Security Check: Ensure user owns this order
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this order")

    # 3. Create Intent
    # Stripe requires amount in cents (e.g., $10.00 = 1000)
    amount_in_cents = int(order.total_amount * 100)
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd", # Change if needed
            metadata={
                "order_id": str(order.id) # Link this payment to our Order ID
            }
        )
        
        # 4. Save Payment Intent ID to Order
        order.stripe_payment_intent_id = intent.id
        await db.commit()
        
        # Extract public key from secret key for frontend usage
        secret_key = os.getenv("STRIPE_API_KEY")
        public_key = secret_key.replace("sk_test_", "pk_test_")
        
        return {
            "client_secret": intent.client_secret,
            "public_key": public_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint Stripe calls when payment succeeds.
    It verifies the signature to ensure it's actually Stripe calling us.
    """
    payload = await request.body()
    sig_header = stripe_signature
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # 1. Verify Event
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    # 2. Handle the Event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id_str = payment_intent['metadata'].get('order_id')
        
        if order_id_str:
            # 3. Update Order Status to PAID
            order_id = uuid.UUID(order_id_str)
            
            result = await db.execute(
                select(Order)
                .options(selectinload(Order.items)) 
                .filter(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if order:
                order.status = OrderStatus.PAID
                await db.commit()
                
                # --- EMAIL LOGIC START ---
                # Fetch User to get email address
                user_res = await db.execute(select(User).filter(User.id == order.user_id))
                user = user_res.scalar_one_or_none()
                
                if user:
                    # Convert ORM Order to Pydantic Schema for the email template
                    order_dto = OrderResponse.from_orm(order)
                    await send_order_confirmation_email(order=order_dto, user=user)
                # --- EMAIL LOGIC END ---
                
    return {"status": "success"}

# --- Helper Endpoint for Testing (Optional) ---
@router.post("/webhook/test-trigger/{order_id}")
async def test_payment_success(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    MANUAL TRIGGER: Simulates a Stripe Webhook success.
    This is useful if you can't set up Stripe CLI locally yet.
    """
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if order:
        order.status = OrderStatus.PAID
        await db.commit()
        
        # Trigger Test Email
        user_res = await db.execute(select(User).filter(User.id == order.user_id))
        user = user_res.scalar_one_or_none()
        
        if user:
            order_dto = OrderResponse.from_orm(order)
            await send_order_confirmation_email(order=order_dto, user=user)
            
        return {"message": f"Order {order_id} marked as PAID"}
    
    raise HTTPException(status_code=404, detail="Order not found")