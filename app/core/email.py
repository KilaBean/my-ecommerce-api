# app/core/email.py
import aiosmtplib
from email.message import EmailMessage
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
from typing import List
from app.config import get_settings
from app.schemas.order import OrderResponse
from app.models.user import User

settings = get_settings()

# Setup Jinja2 to find templates
# We load templates from the 'templates' folder in project root
loader = FileSystemLoader(searchpath="templates")
env = Environment(loader=loader)

async def send_order_confirmation_email(order: OrderResponse, user: User):
    """
    Sends a nice HTML email to user confirming their order.
    """
    try:
        # 1. Render HTML Template
        template = env.get_template("email/order_confirmation.html")
        html_content = template.render(
            user_name=user.username,
            order=order
        )
        
        # 2. Create Message
        message = EmailMessage()
        message["Subject"] = f"Order Confirmation - {order.id}"
        message["From"] = settings.EMAIL_FROM
        message["To"] = user.email
        
        message.set_content(html_content, subtype="html")
        
        # 3. Send Async
        await aiosmtplib.send(
            message,
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_USER,
            password=settings.EMAIL_PASSWORD,
            start_tls=True # Secure connection
        )
        
        print(f"✅ Email sent to {user.email}")
        
    except Exception as e:
        # Log error but don't crash the API (Order is already saved)
        print(f"❌ Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Order saved, but email failed.")