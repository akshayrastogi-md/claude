# 🚀 D2C Analytics & Forecasting Platform - Complete Documentation

**Version:** 1.0.0
**Framework:** FastAPI (Python 3.9+)
**License:** MIT

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Installation & Setup](#installation--setup)
5. [Database Models](#database-models)
6. [API Endpoints](#api-endpoints)
7. [Integration Modules](#integration-modules)
8. [ML/AI Forecasting](#mlai-forecasting)
9. [Authentication](#authentication)
10. [Webhooks](#webhooks)
11. [Environment Configuration](#environment-configuration)
12. [Deployment](#deployment)

---

## 🎯 Overview

### What is This Platform?

A **comprehensive SaaS platform** for Direct-to-Consumer (D2C) brands that provides:

- **AI-Powered Demand Forecasting** - Predict future demand using 4 ML models (Prophet, ARIMA, LSTM, XGBoost)
- **Multi-Channel Analytics** - Unified analytics from Shopify, WooCommerce, Facebook Ads, Google Ads
- **Shipping Intelligence** - RTO tracking, delivery performance, courier comparison via Shiprocket
- **Marketing Attribution** - Track which channels actually drive sales
- **Customer Lifetime Value** - Predictive LTV and cohort analysis
- **Inventory Optimization** - Reorder points, safety stock calculations

### Problem Solved

D2C founders struggle with:
- Fragmented data across platforms
- Poor inventory planning (stockouts vs overstocking)
- Unclear marketing ROI
- High RTO rates
- Unknown customer LTV

This platform **unifies everything** into one analytics engine with AI-powered insights.

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL PLATFORMS                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌────────┐│
│  │ Shopify  │  │WooCommer.│  │Facebook│  │ Google │  │Shiprock││
│  │          │  │          │  │  Ads   │  │  Ads   │  │        ││
│  └────┬─────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └───┬────┘│
└───────┼─────────────┼────────────┼───────────┼───────────┼─────┘
        │             │            │           │           │
        └─────────────┴────────────┴───────────┴───────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │      FastAPI Application (Port 8000)      │
        │  ┌─────────────────────────────────────┐  │
        │  │         API Layer (REST)            │  │
        │  │  - Integrations  - Forecasting      │  │
        │  │  - Analytics     - Webhooks         │  │
        │  └─────────────────────────────────────┘  │
        │  ┌─────────────────────────────────────┐  │
        │  │        Business Services            │  │
        │  │  - D2C Analytics - Forecast Service │  │
        │  └─────────────────────────────────────┘  │
        │  ┌─────────────────────────────────────┐  │
        │  │       ML/AI Engine                  │  │
        │  │  - Prophet  - ARIMA                 │  │
        │  │  - LSTM     - XGBoost               │  │
        │  └─────────────────────────────────────┘  │
        └───────────────────┬───────────────────────┘
                            │
        ┌───────────────────▼───────────────────────┐
        │         Data Storage Layer                │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐│
        │  │PostgreSQL│  │ MongoDB  │  │  Redis   ││
        │  │(Primary) │  │(Analytics)│  │ (Cache)  ││
        │  └──────────┘  └──────────┘  └──────────┘│
        └───────────────────────────────────────────┘
```

### Module Structure

```
claude/
├── app/
│   ├── api/                    # API Endpoints
│   │   ├── integrations.py    # Platform connections
│   │   ├── webhooks.py         # Real-time event handlers
│   │   ├── d2c_analytics.py    # D2C dashboard & metrics
│   │   ├── forecast.py         # AI forecasting
│   │   ├── products.py         # Product CRUD
│   │   ├── sales.py            # Sales records
│   │   ├── analytics.py        # General analytics
│   │   └── inventory.py        # Inventory management
│   │
│   ├── integrations/          # Platform Integrations
│   │   ├── shopify.py         # Shopify OAuth & API
│   │   ├── woocommerce.py     # WooCommerce REST API
│   │   ├── facebook_ads.py    # Facebook Marketing API
│   │   ├── google_ads.py      # Google Ads API
│   │   └── shiprocket.py      # Shiprocket Logistics
│   │
│   ├── services/              # Business Logic
│   │   ├── d2c_analytics.py   # D2C analytics engine
│   │   ├── forecast_service.py # Forecasting service
│   │   └── analytics_service.py # General analytics
│   │
│   ├── ml/                    # Machine Learning
│   │   ├── forecasting_engine.py # Model orchestrator
│   │   ├── models.py          # ML model implementations
│   │   └── base_model.py      # Base model interface
│   │
│   ├── models/                # Database Models (SQLAlchemy)
│   │   ├── store.py           # Multi-tenant stores
│   │   ├── order.py           # Orders
│   │   ├── customer.py        # Customers
│   │   ├── product.py         # Products
│   │   ├── marketing.py       # Marketing campaigns
│   │   ├── shipment.py        # Shipments
│   │   └── forecast.py        # Forecast results
│   │
│   ├── core/                  # Core Infrastructure
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # PostgreSQL connection
│   │   ├── mongodb.py         # MongoDB connection
│   │   ├── security.py        # JWT authentication
│   │   └── logging.py         # Logging setup
│   │
│   └── main.py                # Application entry point
│
├── docs/
│   ├── README.md              # Main documentation
│   ├── API_GUIDE.md           # API reference
│   ├── INTEGRATIONS_GUIDE.md  # Platform setup guides
│   ├── INTEGRATION_API_GUIDE.md # Integration API docs
│   ├── AUTH_ARCHITECTURE.md   # Auth design docs
│   ├── DEPLOYMENT.md          # Deployment guides
│   └── PRODUCTION_SETUP.md    # Production setup
│
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Local development
├── docker-compose.prod.yml    # Production deployment
└── .env.example               # Environment template
```

---

## 💻 Technology Stack

### Backend Framework
- **FastAPI** 0.109.0 - High-performance async Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Databases
- **PostgreSQL** - Primary relational database (orders, customers, stores)
- **MongoDB** - Analytics data, logs, time-series
- **Redis** - Caching, session management

### AI/ML Libraries
- **Prophet** 1.1.5 - Facebook's time series forecasting
- **Statsmodels** 0.14.1 - ARIMA models
- **TensorFlow** 2.15.0 - LSTM neural networks
- **XGBoost** 2.0.3 - Gradient boosting
- **Scikit-learn** 1.4.0 - ML utilities

### Data Processing
- **Pandas** 2.2.0 - Data manipulation
- **NumPy** 1.26.3 - Numerical computing

### Authentication & Security
- **python-jose** - JWT tokens
- **passlib** - Password hashing (bcrypt)
- **cryptography** - Encryption

### Platform APIs
- **google-ads** 23.1.0 - Google Ads integration
- **facebook-business** 19.0.0 - Facebook Marketing API
- **requests** 2.31.0 - HTTP client

### DevOps & Monitoring
- **Sentry** - Error tracking
- **Prometheus** - Metrics
- **Docker** - Containerization

---

## 🚀 Installation & Setup

### Prerequisites

```bash
# Required
Python 3.9+
PostgreSQL 14+
MongoDB 6+
Redis 7+

# Optional (for production)
Docker & Docker Compose
Nginx (reverse proxy)
```

### Quick Start (Development)

```bash
# 1. Clone repository
git clone <your-repo>
cd claude

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Initialize databases
# PostgreSQL
createdb d2c_analytics

# Run migrations (if using Alembic)
alembic upgrade head

# 6. Start the server
python app/main.py

# Or with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup (Recommended)

```bash
# Start all services (PostgreSQL, MongoDB, Redis, FastAPI)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Points

- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📊 Database Models

### Store (Multi-Tenant)

```python
class Store:
    id: int
    name: str                    # Store name
    domain: str                  # Store domain
    email: str                   # Contact email (unique)
    plan: str                    # free, starter, pro, enterprise
    is_active: bool             # Active status
    currency: str               # USD, INR, etc.
    timezone: str               # UTC, Asia/Kolkata, etc.
    created_at: datetime
    updated_at: datetime
```

### Integration

```python
class Integration:
    id: int
    store_id: int               # FK to Store
    platform: str               # shopify, woocommerce, facebook, google, shiprocket
    status: str                 # active, inactive, error
    access_token: str           # OAuth token (encrypted)
    refresh_token: str          # Refresh token
    shop_url: str               # Platform-specific URL
    platform_data: JSON         # Platform-specific config
    last_sync_at: datetime      # Last successful sync
    sync_status: str            # pending, syncing, completed, error
    created_at: datetime
    updated_at: datetime
```

### Order

```python
class Order:
    id: int
    store_id: int               # FK to Store
    customer_id: int            # FK to Customer
    platform: str               # shopify, woocommerce
    platform_order_id: str      # External order ID
    order_number: str           # Human-readable order #
    subtotal: float
    tax: float
    shipping_cost: float
    discount: float
    total: float
    currency: str
    line_items: JSON            # Product details
    item_count: int
    financial_status: str       # paid, pending, refunded
    fulfillment_status: str     # fulfilled, unfulfilled, partial

    # Attribution
    utm_source: str             # facebook, google, email
    utm_medium: str             # cpc, organic, email
    utm_campaign: str           # Campaign name
    referrer: str               # Referring URL
    landing_page: str           # First page visited
    attributed_channel: str     # Normalized channel name

    order_date: datetime
```

### Customer

```python
class Customer:
    id: int
    store_id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    city: str
    state: str
    country: str
    postal_code: str
    total_orders: int           # Lifetime orders
    total_spent: float          # Lifetime value
    first_order_date: datetime
    last_order_date: datetime
    shopify_customer_id: str
    woocommerce_customer_id: str
    created_at: datetime
```

### MarketingCampaign

```python
class MarketingCampaign:
    id: int
    store_id: int
    name: str                   # Campaign name
    channel: str                # facebook, google
    campaign_type: str          # conversion, awareness, shopping
    platform_campaign_id: str   # External ID
    budget: float
    spent: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    ctr: float                  # Click-through rate
    cpc: float                  # Cost per click
    cpa: float                  # Cost per acquisition
    roas: float                 # Return on ad spend
    status: str                 # active, paused, ended
    start_date: datetime
    end_date: datetime
    last_synced_at: datetime
```

### Shipment

```python
class Shipment:
    id: int
    store_id: int
    order_id: int
    shiprocket_order_id: str
    shiprocket_shipment_id: str
    awb_code: str               # Tracking number
    courier_name: str           # Delhivery, Blue Dart, etc.
    courier_id: str
    weight: float
    dimensions: str
    shipping_charges: float
    cod_charges: float
    total_cost: float
    pickup_date: datetime
    delivered_date: datetime
    delivery_days: int
    status: str                 # pickup, in_transit, delivered, rto
    current_status: str         # Detailed status
    is_delivered: bool
    is_rto: bool                # Return to origin
    destination_city: str
    destination_state: str
    destination_pincode: str
    created_at: datetime
```

### ForecastResult

```python
class ForecastResult:
    id: int
    product_id: int
    model_type: str             # prophet, arima, lstm, xgboost
    forecast_horizon_days: int
    predictions: JSON           # [{date, predicted_demand, lower_bound, upper_bound}]
    confidence_interval: float
    accuracy_metrics: JSON      # {mae, rmse, mape}
    recommendations: JSON       # {reorder_point, safety_stock, order_quantity}
    created_at: datetime
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All endpoints (except webhooks and health) require JWT token:

```bash
Authorization: Bearer <YOUR_JWT_TOKEN>
```

---

## 1️⃣ Platform Integrations API

### List All Integrations

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "platform": "shopify",
      "status": "active",
      "last_sync_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Connect Shopify (Direct)

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/shopify/connect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_url": "mystore.myshopify.com",
    "access_token": "shpat_xxxxxxxxxxxx"
  }'
```

### Initiate Shopify OAuth

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/shopify/oauth/initiate?shop=mystore.myshopify.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "oauth_url": "https://mystore.myshopify.com/admin/oauth/authorize?client_id=...",
  "message": "Redirect user to this URL to authorize Shopify access"
}
```

### Connect WooCommerce

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/woocommerce/connect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "store_url": "https://mystore.com",
    "consumer_key": "ck_xxxxxxxxxxxxx",
    "consumer_secret": "cs_xxxxxxxxxxxxx"
  }'
```

### Connect Facebook Ads

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/facebook/connect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "EAAxxxxxxxxxxxx",
    "ad_account_id": "act_123456789"
  }'
```

### Connect Google Ads

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/google-ads/connect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "developer_token": "your_dev_token",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "refresh_token": "your_refresh_token",
    "customer_id": "1234567890"
  }'
```

### Connect Shiprocket

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/shiprocket/connect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'
```

### Trigger Manual Sync

```bash
curl -X POST "http://localhost:8000/api/v1/integrations/1/sync" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Integration Status

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "platform": "shopify",
    "status": "active",
    "last_sync_at": "2024-01-15T10:30:00Z",
    "sync_healthy": true,
    "hours_since_sync": 2.5
  }
}
```

### Disconnect Integration

```bash
curl -X DELETE "http://localhost:8000/api/v1/integrations/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 2️⃣ D2C Analytics API

### Get Comprehensive Dashboard

```bash
curl -X GET "http://localhost:8000/api/v1/d2c/dashboard?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "revenue_metrics": {
      "total_revenue": 125000.50,
      "total_orders": 450,
      "average_order_value": 277.78,
      "growth_rate": 23.5
    },
    "customer_metrics": {
      "total_customers": 320,
      "new_customers": 85,
      "repeat_rate": 28.5,
      "avg_ltv": 450.25,
      "avg_cac": 45.50,
      "ltv_cac_ratio": 9.89
    },
    "marketing_metrics": {
      "total_spent": 15000.00,
      "total_revenue": 58000.00,
      "overall_roas": 3.87,
      "by_channel": [
        {
          "channel": "facebook",
          "spent": 8000.00,
          "revenue": 32000.00,
          "roas": 4.0,
          "orders": 115
        },
        {
          "channel": "google",
          "spent": 7000.00,
          "revenue": 26000.00,
          "roas": 3.71,
          "orders": 94
        }
      ]
    },
    "shipping_metrics": {
      "total_shipments": 450,
      "delivered": 405,
      "in_transit": 30,
      "rto": 15,
      "delivery_rate": 90.0,
      "rto_rate": 3.33,
      "avg_delivery_days": 4.2
    },
    "channel_attribution": {
      "direct": 35.5,
      "facebook": 28.3,
      "google": 22.1,
      "email": 10.2,
      "whatsapp": 3.9
    },
    "top_products": [
      {
        "product_id": 123,
        "name": "Product A",
        "revenue": 25000.00,
        "units_sold": 150,
        "orders": 120
      }
    ],
    "insights": [
      "Facebook Ads showing strong ROAS of 4.0x - consider increasing budget",
      "RTO rate at 3.33% is healthy, below industry average of 10%",
      "Repeat purchase rate at 28.5% - implement loyalty program to boost to 35%"
    ]
  },
  "period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59",
    "days": 31
  }
}
```

### Get Revenue Metrics

```bash
curl -X GET "http://localhost:8000/api/v1/d2c/revenue?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Customer Metrics

```bash
curl -X GET "http://localhost:8000/api/v1/d2c/customers?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Marketing ROAS

```bash
curl -X GET "http://localhost:8000/api/v1/d2c/marketing?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Shipping Analytics

```bash
curl -X GET "http://localhost:8000/api/v1/d2c/shipping?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 3️⃣ AI Forecasting API

### Generate Demand Forecast

```bash
curl -X POST "http://localhost:8000/api/v1/forecast/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 123,
    "forecast_horizon_days": 30,
    "model_type": "auto",
    "confidence_interval": 0.95,
    "include_historical": true
  }'
```

**Response:**
```json
{
  "product_id": 123,
  "model_type": "prophet",
  "forecast_horizon_days": 30,
  "predictions": [
    {
      "date": "2024-02-01",
      "predicted_demand": 45.2,
      "lower_bound": 38.5,
      "upper_bound": 52.0
    },
    {
      "date": "2024-02-02",
      "predicted_demand": 47.8,
      "lower_bound": 40.1,
      "upper_bound": 55.5
    }
  ],
  "accuracy_metrics": {
    "mae": 3.2,
    "rmse": 4.5,
    "mape": 8.3
  },
  "recommendations": {
    "recommended_order_quantity": 1400,
    "reorder_point": 350,
    "safety_stock": 180,
    "demand_trend": "increasing",
    "confidence": "high"
  },
  "historical_data": [
    {
      "date": "2024-01-01",
      "actual_demand": 42
    }
  ]
}
```

**Model Types:**
- `auto` - Automatically selects best model
- `prophet` - Facebook Prophet (good for seasonality)
- `arima` - ARIMA model (good for trends)
- `lstm` - LSTM neural network (good for complex patterns)
- `xgboost` - XGBoost (good for feature-rich data)

### Bulk Forecast

```bash
curl -X POST "http://localhost:8000/api/v1/forecast/bulk" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": [123, 456, 789],
    "forecast_horizon_days": 30
  }'
```

### Get Forecast Accuracy

```bash
curl -X GET "http://localhost:8000/api/v1/forecast/accuracy/123?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4️⃣ Products API

### Create Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "PROD-001",
    "name": "Organic Tea - 100g",
    "category": "Beverages",
    "price": 299.00,
    "cost": 150.00,
    "is_active": true
  }'
```

### List Products

```bash
curl -X GET "http://localhost:8000/api/v1/products/?skip=0&limit=100&category=Beverages" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Product

```bash
curl -X GET "http://localhost:8000/api/v1/products/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Product

```bash
curl -X PUT "http://localhost:8000/api/v1/products/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 349.00,
    "is_active": true
  }'
```

### Delete Product

```bash
curl -X DELETE "http://localhost:8000/api/v1/products/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 5️⃣ Sales API

### Create Sales Record

```bash
curl -X POST "http://localhost:8000/api/v1/sales/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 123,
    "quantity": 10,
    "unit_price": 299.00,
    "total_amount": 2990.00,
    "sale_date": "2024-01-15T14:30:00"
  }'
```

### Bulk Create Sales

```bash
curl -X POST "http://localhost:8000/api/v1/sales/bulk" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "product_id": 123,
      "quantity": 10,
      "unit_price": 299.00,
      "total_amount": 2990.00,
      "sale_date": "2024-01-15T14:30:00"
    },
    {
      "product_id": 456,
      "quantity": 5,
      "unit_price": 499.00,
      "total_amount": 2495.00,
      "sale_date": "2024-01-15T15:00:00"
    }
  ]'
```

### List Sales

```bash
curl -X GET "http://localhost:8000/api/v1/sales/?product_id=123&start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 6️⃣ Analytics API

### Get Product Analytics

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/products/123?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Sales Trends

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/trends?period=monthly&start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔔 Webhooks

Webhooks are **public endpoints** (no authentication required) but verify platform signatures.

### Shopify Order Created

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/shopify/orders/create" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Hmac-Sha256: <shopify_hmac>" \
  -H "X-Shopify-Shop-Domain: mystore.myshopify.com" \
  -d '{
    "id": 123456789,
    "order_number": "1001",
    "total_price": "2990.00",
    "line_items": [...]
  }'
```

### WooCommerce Order

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/woocommerce/orders" \
  -H "Content-Type: application/json" \
  -H "X-WC-Webhook-Signature: <signature>" \
  -d '{
    "id": 123,
    "status": "completed",
    "total": "2990.00"
  }'
```

### Shiprocket Tracking Update

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/shiprocket/tracking" \
  -H "Content-Type: application/json" \
  -d '{
    "awb": "12345678901",
    "current_status": "Delivered",
    "delivered_date": "2024-01-15T18:30:00"
  }'
```

---

## 🔐 Integration Modules

### Shopify Integration (`app/integrations/shopify.py`)

**Features:**
- OAuth 2.0 authentication
- Order sync with UTM tracking
- Customer sync
- Product sync
- Webhook signature verification

**Key Methods:**
```python
ShopifyIntegration(shop_url, access_token)
.get_oauth_url(shop, client_id, redirect_uri, scopes)
.exchange_code_for_token(shop, code, client_id, client_secret)
.get_orders(since_date, limit, status)
.get_customers(since_date)
.get_products()
.sync_orders_to_db(db, store_id, since_date)
.verify_webhook(data, hmac_header, secret)
.create_webhook(topic, address)
```

### WooCommerce Integration (`app/integrations/woocommerce.py`)

**Features:**
- REST API authentication (consumer key/secret)
- Order sync with UTM metadata
- Customer sync
- Product sync
- Webhook support

**Key Methods:**
```python
WooCommerceIntegration(store_url, consumer_key, consumer_secret)
.get_orders(since_date, per_page, status)
.get_customers(since_date)
.get_products()
.sync_orders_to_db(db, store_id, since_date)
.verify_webhook(payload, signature, secret)
.create_webhook(topic, delivery_url)
```

### Facebook Ads Integration (`app/integrations/facebook_ads.py`)

**Features:**
- Marketing API integration
- Campaign performance metrics
- ROAS tracking
- Conversion tracking
- Instagram ads included

**Key Methods:**
```python
FacebookAdsIntegration(access_token, ad_account_id)
.get_campaigns(date_from, date_to, status)
.get_campaign_insights(campaign_id, date_from, date_to)
.sync_campaigns_to_db(db, store_id, date_from, date_to)
.get_ad_account_info()
.generate_auth_url(client_id, redirect_uri, scopes)
.exchange_code_for_token(code, client_id, client_secret, redirect_uri)
```

### Google Ads Integration (`app/integrations/google_ads.py`)

**Features:**
- Google Ads API integration
- Campaign metrics
- Shopping & Search ads
- Keyword performance
- YouTube ads support

**Key Methods:**
```python
GoogleAdsIntegration(developer_token, client_id, client_secret, refresh_token, customer_id)
.get_access_token()
.get_campaigns_summary(date_from, date_to)
.sync_campaigns_to_db(db, store_id, date_from, date_to)
.generate_oauth_url(client_id, redirect_uri)
```

### Shiprocket Integration (`app/integrations/shiprocket.py`)

**Features:**
- Shipment tracking
- RTO (Return to Origin) tracking
- Delivery performance
- Courier comparison
- COD reconciliation
- Shipping cost analysis

**Key Methods:**
```python
ShiprocketIntegration(email, password)
.get_shipments(page, per_page, filter_by_date)
.track_shipment(shipment_id)
.track_by_awb(awb_code)
.sync_shipments_to_db(db, store_id, since_date)
.get_courier_performance()
.get_ndr_details(awb_code)
.create_order(order_data)
.calculate_shipping_cost(pickup_pincode, delivery_pincode, weight, cod)
```

---

## 🤖 ML/AI Forecasting

### Forecasting Engine (`app/ml/forecasting_engine.py`)

The forecasting engine automatically selects the best model based on:
- Data availability (minimum 30 days historical data)
- Data patterns (trend, seasonality, noise)
- Model performance (cross-validation)

**Available Models:**

#### 1. Prophet (Facebook)
- **Best for**: Seasonal patterns, holidays, missing data
- **Algorithm**: Additive regression model with trend, seasonality, holidays
- **Pros**: Handles missing data, detects changepoints, interpretable
- **Cons**: Slower training

#### 2. ARIMA
- **Best for**: Stationary time series, trending data
- **Algorithm**: AutoRegressive Integrated Moving Average
- **Pros**: Well-established, good for trends
- **Cons**: Requires stationary data, sensitive to outliers

#### 3. LSTM (Neural Network)
- **Best for**: Complex non-linear patterns, large datasets
- **Algorithm**: Long Short-Term Memory recurrent neural network
- **Pros**: Captures complex patterns, learns from features
- **Cons**: Requires more data, longer training, black box

#### 4. XGBoost
- **Best for**: Feature-rich data, when you have promotions/events data
- **Algorithm**: Gradient boosting decision trees
- **Pros**: High accuracy, handles features well
- **Cons**: Requires feature engineering

### Model Selection Logic

```python
def auto_select_model(historical_data):
    if len(historical_data) < 30:
        return "insufficient_data"

    if has_strong_seasonality(historical_data):
        return "prophet"

    if has_trend_only(historical_data):
        return "arima"

    if len(historical_data) > 180:
        return "lstm"  # Enough data for neural network

    return "xgboost"  # Default for most cases
```

### Accuracy Metrics

- **MAE** (Mean Absolute Error): Average absolute difference
- **RMSE** (Root Mean Squared Error): Penalizes large errors
- **MAPE** (Mean Absolute Percentage Error): Error as percentage

### Inventory Recommendations

The engine provides:
- **Reorder Point**: When to place new order
- **Safety Stock**: Buffer to prevent stockouts
- **Recommended Order Quantity**: How much to order
- **Lead Time Consideration**: Accounts for supplier lead time
- **Demand Trend**: Increasing, stable, or decreasing

---

## 🔒 Authentication

### Current Implementation

**Token Type**: JWT (JSON Web Tokens)
**Algorithm**: HS256 (HMAC-SHA256)
**Access Token Expiry**: 30 minutes
**Refresh Token Expiry**: 7 days

### Token Structure

```json
{
  "user_id": 123,
  "store_id": 456,
  "email": "user@example.com",
  "role": "admin",
  "type": "access",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Getting a Token (Future Implementation)

**Note**: Login/registration endpoints are NOT yet implemented. See `AUTH_ARCHITECTURE.md` for planned implementation.

For testing, generate a token manually:

```python
from app.core.security import AuthService

token = AuthService.create_access_token({
    "user_id": 1,
    "store_id": 1,
    "email": "test@example.com",
    "role": "admin"
})
print(token)
```

### Using Token in Requests

```bash
curl -X GET "http://localhost:8000/api/v1/integrations/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## ⚙️ Environment Configuration

### Required Variables (`.env`)

```bash
# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=False

# API
API_V1_STR=/api/v1
API_URL=http://localhost:8000
PROJECT_NAME=D2C Analytics & Forecasting Platform

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=d2c_analytics
POSTGRES_PORT=5432

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=d2c_analytics

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# JWT
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Shopify
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret

# Google Ads
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_DEVELOPER_TOKEN=your_dev_token

# ML Models
ENABLE_PROPHET=true
ENABLE_ARIMA=true
ENABLE_LSTM=true
ENABLE_XGBOOST=true
```

---

## 🚀 Deployment

### Production with Docker

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

### Environment-Specific Settings

See `DEPLOYMENT.md` for detailed deployment guides:
- AWS (EC2, ECS, Lambda)
- Google Cloud Platform
- Azure
- DigitalOcean
- Heroku

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY` (32+ random characters)
- [ ] Configure PostgreSQL with SSL
- [ ] Set up Redis persistence
- [ ] Configure Sentry for error tracking
- [ ] Set up backup strategy
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Set up logging aggregation
- [ ] Configure rate limiting
- [ ] Set up SSL/TLS (Let's Encrypt)
- [ ] Configure CORS properly
- [ ] Set up CI/CD pipeline

---

## 📚 Additional Documentation

- **[API_GUIDE.md](API_GUIDE.md)** - Detailed API reference
- **[INTEGRATIONS_GUIDE.md](INTEGRATIONS_GUIDE.md)** - Platform setup guides
- **[AUTH_ARCHITECTURE.md](AUTH_ARCHITECTURE.md)** - Authentication design for microservices
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guides
- **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** - Production configuration

---

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=app tests/
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
open http://localhost:8000/docs
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check PostgreSQL is running
pg_isready

# Check credentials in .env
cat .env | grep POSTGRES
```

#### 2. Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 3. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 4. ML Model Errors
```bash
# Ensure sufficient historical data (30+ days)
# Check model is enabled in .env
cat .env | grep ENABLE_
```

---

## 📈 Performance

### Optimization Tips

1. **Database**:
   - Use connection pooling
   - Add indexes on frequently queried columns
   - Use database-level aggregations

2. **Caching**:
   - Enable Redis caching
   - Cache expensive computations (forecasts)
   - Set appropriate TTL

3. **Background Tasks**:
   - Use Celery for long-running tasks
   - Process integrations in background
   - Schedule daily syncs

4. **API**:
   - Use pagination for large datasets
   - Implement rate limiting
   - Use async endpoints where possible

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 💬 Support

- **Email**: support@yourplatform.com
- **Documentation**: https://docs.yourplatform.com
- **GitHub Issues**: https://github.com/your-repo/issues

---

## 🎯 Key Metrics & KPIs

### Business Metrics Tracked

- **Revenue**: Total revenue, AOV, growth rate
- **Customers**: LTV, CAC, LTV:CAC ratio, repeat rate
- **Marketing**: ROAS by channel, CPA, conversion rate
- **Shipping**: Delivery rate, RTO rate, avg delivery days
- **Inventory**: Stockout rate, inventory turnover, dead stock

### System Metrics

- **API Performance**: Response time, throughput, error rate
- **Forecast Accuracy**: MAE, RMSE, MAPE per model
- **Data Freshness**: Last sync time per integration
- **System Health**: CPU, memory, database connections

---

**Built with ❤️ for D2C founders who want to grow with data, not guesswork.**
