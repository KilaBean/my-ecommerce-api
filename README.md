# 🛍️ E-Commerce REST API

A robust, production-ready backend API for an E-commerce platform built with **FastAPI**. The system serves as a modular monolith handling users, inventory, orders, and payments.

## ✨ Features

- **🔐 Authentication:** User & Admin roles, JWT Tokens, Secure Password Hashing.
- **🛒️ Product Catalog:** Categories, Products, and SKUs (Variants) management.
- **📦 Inventory System:** Row-level locking to prevent overselling + Real-time updates via WebSockets.
- **🛒️ Shopping Cart:** Session-based carts stored in PostgreSQL (JSONB).
- **💰 Order Processing:** Complete state machine (Created -> Paid -> Shipped).
- **💳 Payments:** Stripe Integration (Payment Intents & Webhooks).
- **🎫 Coupons:** Percentage and Fixed discount codes with usage tracking.
- **📧 Recommendations:** Content-based recommendation engine.
- **📧 Notifications:** Automated Order Confirmation emails (Gmail SMTP).
- **🔒 CORS:** Secure Cross-Origin Resource Sharing configuration.
- **📖 API Versioning:** Structured v1 endpoints.

## 🛠️ Tech Stack

- **Backend:** FastAPI (Async)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 (Async)
- **Cache:** Not used (Cart is DB-backed)
- **Payments:** Stripe
- **Email:** Gmail (SMTP)
- **Real-time:** WebSockets (Inventory updates)

## 📦 Project Structure

```text
my_ecommerce_api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── carts.py
│   │   │   │   ├── coupons.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── payments.py
│   │   │   │   ├── products.py
│   │   │   │   ├── recommendations.py
│   │   │   │   ├── users.py
│   │   │   │   └── websocket.py
│   │   │   └── deps.py
│   │   └── deps.py
│   ├── core/
│   │   ├── email.py
│   │   └── security.py
│   ├── database.py
│   ├── main.py
│   ├── models/
│   │   ├── cart.py
│   │   ├── coupon.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── coupon.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   ├── config.py
│   └── redis_client.py (legacy, not currently used)
├── templates/
│   └── email/
│       └── order_confirmation.html
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- PostgreSQL Server (Local or Cloud)
- Stripe Account (For payment testing)

### 2. Installation

1. **Clone the repository**
```bash
git clone https://github.com/KilaBean/my-ecommerce-api.git
cd my-ecommerce-api
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory and add your configuration variables:

```ini
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=ecommerce_db

# Security
SECRET_KEY=your_super_secret_key_here

# Stripe (Test Keys for development)
STRIPE_API_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_test_your_key_here

# Email (Gmail App Password)
EMAIL_USER=yourname@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_FROM=yourname@gmail.com
```

### 4. Run the Application

Start the Uvicorn server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 5. API Documentation

Once the server is running, access the interactive Swagger UI:
```text
http://127.0.0.1:8000/docs
```
Or ReDoc:
```text
http://127.0.0.1:8000/redoc
```

## 📌 Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user | No |
| `POST` | `/api/v1/auth/login` | Login to get JWT | No |
| `GET` | `/api/v1/products/` | List all products | No |
| `POST` | `/api/v1/products/` | Create product | Admin |
| `GET` | `/api/v1/cart/` | Get cart items | No |
| `POST` | `/api/v1/cart/add` | Add item to cart | No |
| `POST` | `/api/v1/orders/checkout` | Create order & lock stock | User |
| `POST` | `/api/v1/payments/create-intent` | Initiate Stripe payment | User |
| `POST` | `/api/v1/recommendations/{id}` | Get related products | No |


**📝 Note:** This project uses a modular monolith architecture. It is scalable, maintainable, and ready for high-traffic environments.
```

---

### 2. Create `requirements.txt`
Create a file named `requirements.txt` in your project folder and paste this:

```text
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
passlib[bcrypt]
python-jose[cryptography]
python-multipart
pydantic-settings
pydantic[email]
email-validator
stripe
python-docx
aiosmtplib
jinja2
```

---

### 3. Create `.gitignore`
Create a file named `.gitignore` in your project folder and paste this:

```text
# Python
venv/
__pycache__/
*.pyc
*.pyo

# Environment Variables (Secrets)
.env

# Database
*.db
*.sqlite3

# OS Specific
.DS_Store
Thumbs.db