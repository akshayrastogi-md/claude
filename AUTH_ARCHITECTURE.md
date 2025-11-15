# Authentication Architecture - Current Implementation & Microservice Design

## Current Authentication Implementation (FastAPI Service)

### Overview
This FastAPI service currently has **basic JWT authentication** built-in but **NO actual login/registration endpoints implemented yet**. The authentication layer is prepared but waiting for implementation.

---

## 🔑 Current Auth Components

### 1. **JWT Token System** (app/core/security.py)

#### Token Types:
1. **Access Token**
   - Algorithm: `HS256` (HMAC with SHA-256)
   - Expiry: `30 minutes` (configurable)
   - Type: `"access"`
   - Used for: API authentication

2. **Refresh Token**
   - Algorithm: `HS256`
   - Expiry: `7 days` (configurable)
   - Type: `"refresh"`
   - Used for: Getting new access tokens

#### Token Payload Structure:
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

### 2. **Password Hashing**
- Library: `passlib` with `bcrypt`
- Rounds: `12` (configurable)
- Functions:
  - `get_password_hash(password)` - Hash password
  - `verify_password(plain, hashed)` - Verify password

### 3. **Token Authentication Flow**
```
Client Request
   ↓
Header: Authorization: Bearer <JWT_TOKEN>
   ↓
HTTPBearer Security (FastAPI)
   ↓
get_current_user() dependency
   ↓
Decode JWT → Validate → Extract user_id, store_id
   ↓
get_current_active_store() dependency
   ↓
Verify store exists & is_active=True
   ↓
Return store_id to endpoint
```

### 4. **Dependencies (FastAPI Middleware)**

#### `get_current_user()`
- Extracts JWT from `Authorization: Bearer <token>`
- Decodes and validates token
- Returns user data: `{user_id, store_id, email, role}`

#### `get_current_active_store()`
- Depends on `get_current_user()`
- Validates store exists and is active
- Returns `store_id`

#### `require_role(role)`
- Role-based access control
- Checks user role matches required role

### 5. **Configuration** (app/core/config.py)
```python
# JWT Settings
SECRET_KEY: str = "your-secret-key-change-in-production"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
BCRYPT_ROUNDS: int = 12
```

---

## 🏗️ Multi-Tenant Model (Current Database)

### Store Model (app/models/store.py)
```python
class Store:
    id: int
    name: str
    domain: str
    email: str (unique)
    plan: str  # free, starter, pro, enterprise
    is_active: bool
    currency: str
    timezone: str
    created_at: datetime
    updated_at: datetime
```

**Note:** Currently, there's NO User table - authentication is directly tied to Store.

---

## 🚀 Recommended Microservice Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Frontend)                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   API GATEWAY (Optional)                     │
│              - Rate limiting                                 │
│              - Request routing                               │
└─────────────────────────────────────────────────────────────┘
            │                                    │
            ▼                                    ▼
┌─────────────────────────┐      ┌─────────────────────────────┐
│   AUTH SERVICE (Go)     │      │  ANALYTICS SERVICE (FastAPI)│
│                         │      │  (Current Service)           │
│  - User Registration    │      │                              │
│  - Login/Logout         │      │  - Integrations              │
│  - JWT Generation       │◄─────┤  - Forecasting               │
│  - Token Validation     │      │  - Analytics                 │
│  - Subscription Mgmt    │      │  - Orders/Customers          │
│  - User Management      │      │  - Webhooks                  │
│  - API Keys             │      │                              │
│                         │      │  Protected by JWT            │
└─────────────────────────┘      └─────────────────────────────┘
            │                                    │
            ▼                                    ▼
┌─────────────────────────┐      ┌─────────────────────────────┐
│   PostgreSQL (Auth DB)  │      │  PostgreSQL (Analytics DB)  │
│  - users                │      │  - stores                    │
│  - stores               │      │  - orders                    │
│  - subscriptions        │      │  - customers                 │
│  - api_keys             │      │  - integrations              │
└─────────────────────────┘      └─────────────────────────────┘
```

---

## 🔐 Auth Service Design (Go)

### 1. Database Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stores table (mirror from analytics service)
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    owner_id INTEGER REFERENCES users(id),
    plan VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    currency VARCHAR(10) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User-Store relationship (multi-tenant support)
CREATE TABLE user_stores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    store_id INTEGER REFERENCES stores(id),
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, store_id)
);

-- Subscriptions
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id),
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, cancelled, expired, past_due
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API Keys (for programmatic access)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES stores(id),
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL, -- First 8 chars for display
    name VARCHAR(100),
    scopes JSONB, -- ["read:orders", "write:products"]
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Refresh tokens (for security)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. JWT Token Strategy

#### Shared Secret Approach (Simple)
- **Pros**: Easy to implement
- **Cons**: Both services need same SECRET_KEY
- **Use when**: Services are in same organization

```go
// Shared configuration
SECRET_KEY = "same-secret-in-both-services"
ALGORITHM = "HS256"
```

#### Public/Private Key Approach (Recommended)
- **Pros**: More secure, auth service signs with private key, analytics verifies with public key
- **Cons**: Slightly more complex
- **Use when**: Better security needed

```go
// Auth Service (Go)
PRIVATE_KEY = "RSA private key"
ALGORITHM = "RS256"

// Analytics Service (FastAPI)
PUBLIC_KEY = "RSA public key"
ALGORITHM = "RS256"
```

### 3. Auth Service API Endpoints (Go)

#### Authentication Endpoints

```go
// POST /api/auth/register
type RegisterRequest struct {
    Email     string `json:"email" validate:"required,email"`
    Password  string `json:"password" validate:"required,min=8"`
    FirstName string `json:"first_name"`
    LastName  string `json:"last_name"`
    StoreName string `json:"store_name" validate:"required"`
}

type RegisterResponse struct {
    User        User   `json:"user"`
    Store       Store  `json:"store"`
    AccessToken string `json:"access_token"`
    RefreshToken string `json:"refresh_token"`
}

// POST /api/auth/login
type LoginRequest struct {
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required"`
}

type LoginResponse struct {
    User         User   `json:"user"`
    AccessToken  string `json:"access_token"`
    RefreshToken string `json:"refresh_token"`
    Stores       []Store `json:"stores"` // User's accessible stores
}

// POST /api/auth/refresh
type RefreshRequest struct {
    RefreshToken string `json:"refresh_token" validate:"required"`
}

type RefreshResponse struct {
    AccessToken string `json:"access_token"`
}

// POST /api/auth/logout
// Revokes refresh token

// POST /api/auth/verify-email
// POST /api/auth/forgot-password
// POST /api/auth/reset-password
```

#### Token Validation (Internal - Service to Service)

```go
// POST /internal/auth/validate
// Used by Analytics service to validate tokens
type ValidateRequest struct {
    Token string `json:"token"`
}

type ValidateResponse struct {
    Valid   bool   `json:"valid"`
    UserID  int    `json:"user_id"`
    StoreID int    `json:"store_id"`
    Email   string `json:"email"`
    Role    string `json:"role"`
}
```

#### Store Management

```go
// POST /api/stores
// Create new store

// GET /api/stores
// List user's stores

// PUT /api/stores/{store_id}
// Update store

// POST /api/stores/{store_id}/members
// Invite team member
```

#### Subscription Management

```go
// GET /api/subscriptions/{store_id}
// Get subscription details

// POST /api/subscriptions/{store_id}/checkout
// Create Stripe checkout session

// POST /api/subscriptions/{store_id}/portal
// Create Stripe customer portal session

// POST /webhooks/stripe
// Stripe webhook handler
```

#### API Key Management

```go
// POST /api/api-keys
// Create API key

// GET /api/api-keys
// List API keys

// DELETE /api/api-keys/{key_id}
// Revoke API key
```

### 4. Go Implementation Libraries

```go
// go.mod
require (
    github.com/golang-jwt/jwt/v5 v5.2.0
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
    golang.org/x/crypto v0.17.0
    github.com/stripe/stripe-go/v76 v76.8.0
    github.com/go-redis/redis/v8 v8.11.5
)
```

### 5. JWT Generation (Go)

```go
package auth

import (
    "time"
    "github.com/golang-jwt/jwt/v5"
)

type Claims struct {
    UserID  int    `json:"user_id"`
    StoreID int    `json:"store_id"`
    Email   string `json:"email"`
    Role    string `json:"role"`
    Type    string `json:"type"` // "access" or "refresh"
    jwt.RegisteredClaims
}

func GenerateAccessToken(userID, storeID int, email, role string) (string, error) {
    claims := Claims{
        UserID:  userID,
        StoreID: storeID,
        Email:   email,
        Role:    role,
        Type:    "access",
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(30 * time.Minute)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(os.Getenv("JWT_SECRET")))
}

func GenerateRefreshToken(userID, storeID int, email, role string) (string, error) {
    claims := Claims{
        UserID:  userID,
        StoreID: storeID,
        Email:   email,
        Role:    role,
        Type:    "refresh",
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(7 * 24 * time.Hour)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(os.Getenv("JWT_SECRET")))
}
```

---

## 🔄 Service Communication

### Option 1: JWT Validation (Recommended)

Analytics service validates JWT locally without calling Auth service:

```python
# FastAPI (Analytics Service)
from jose import jwt

def decode_token(token: str):
    # Decode JWT using shared secret or public key
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,  # Same as Auth service
        algorithms=["HS256"]
    )
    return payload
```

**Pros:**
- Fast (no network call)
- Works offline
- Scalable

**Cons:**
- Can't revoke tokens immediately
- Both services need secret/public key

### Option 2: Token Validation API

Analytics service calls Auth service to validate:

```python
# FastAPI (Analytics Service)
import httpx

async def validate_token(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/internal/auth/validate",
            json={"token": token}
        )
        return response.json()
```

**Pros:**
- Immediate token revocation
- Centralized validation logic

**Cons:**
- Network latency
- Auth service becomes dependency

### Option 3: Hybrid (Best)

1. Validate JWT locally for performance
2. Cache token validation results in Redis (5-10 min TTL)
3. Check Redis blacklist for revoked tokens

```python
import redis
from jose import jwt

redis_client = redis.Redis(...)

async def validate_token(token: str):
    # Check if token is blacklisted
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(401, "Token revoked")

    # Validate JWT locally
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return payload
```

---

## 📊 Data Sync Between Services

### Store Data Sync

When store is created/updated in Auth service, sync to Analytics service:

```go
// Auth Service (Go)
func CreateStore(store Store) error {
    // 1. Save to Auth DB
    db.Create(&store)

    // 2. Publish event to message queue
    publishEvent("store.created", store)

    // 3. Or call Analytics API directly
    syncStoreToAnalytics(store)

    return nil
}
```

```python
# Analytics Service (FastAPI)
@router.post("/internal/stores/sync")
async def sync_store(store_data: dict, db: Session = Depends(get_db)):
    """Internal endpoint called by Auth service"""

    # Verify request from Auth service
    # Could use API key or internal JWT

    store = Store(**store_data)
    db.merge(store)  # Insert or update
    db.commit()

    return {"success": True}
```

### Recommended: Event-Driven Architecture

```
Auth Service (Go)
    ↓ publishes event
Redis Pub/Sub or RabbitMQ
    ↓ consumes event
Analytics Service (FastAPI)
    ↓ updates local store copy
```

---

## 🔒 Security Best Practices

### 1. Environment Variables

```bash
# Auth Service (Go)
JWT_SECRET=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_COST=12
ANALYTICS_SERVICE_URL=http://analytics:8000
ANALYTICS_API_KEY=internal-api-key-for-service-to-service

# Analytics Service (FastAPI)
JWT_SECRET=same-as-auth-service
JWT_ALGORITHM=HS256
AUTH_SERVICE_URL=http://auth:3000
```

### 2. API Key for Service-to-Service

```python
# Analytics Service validates internal requests
@router.post("/internal/stores/sync")
async def sync_store(
    request: Request,
    store_data: dict
):
    api_key = request.headers.get("X-Internal-API-Key")
    if api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(403, "Forbidden")

    # Process...
```

### 3. Rate Limiting

Implement rate limiting in both services:
- Auth Service: Login attempts, registration
- Analytics Service: API calls per store/plan

---

## 📝 Migration Strategy

### Phase 1: Setup Auth Service (Go)
1. Create Go service with endpoints
2. Implement JWT generation
3. Create database schema
4. Add registration/login endpoints

### Phase 2: Update Analytics Service (FastAPI)
1. Keep JWT validation logic
2. Update `get_current_user()` to handle new token format
3. Add internal sync endpoints
4. Add service-to-service authentication

### Phase 3: Data Migration
1. Migrate existing Store data to Auth service
2. Create default users for existing stores
3. Generate API keys for existing integrations

### Phase 4: Testing
1. Test auth flows end-to-end
2. Test service communication
3. Load testing
4. Security testing

### Phase 5: Deployment
1. Deploy Auth service
2. Update frontend to use Auth service
3. Update Analytics service configuration
4. Monitor and optimize

---

## 🎯 Summary

### Current State
- JWT-based authentication prepared but **NO login/registration implemented**
- Token validation in place
- Multi-tenant store model exists
- No user management

### Recommended Architecture
- **Auth Service (Go)**: User auth, subscriptions, API keys
- **Analytics Service (FastAPI)**: Core features, integrations, forecasting
- **Communication**: JWT tokens validated locally + Redis for revocation
- **Data Sync**: Event-driven or direct API calls with internal auth

### Key Decisions Needed
1. **JWT Strategy**: Shared secret (HS256) or public/private keys (RS256)?
2. **Token Validation**: Local validation or API calls?
3. **Data Sync**: Events (RabbitMQ/Redis) or direct API calls?
4. **User Model**: Single user per store or team-based?
5. **API Gateway**: Use gateway or direct service calls?

This architecture allows you to scale auth and analytics independently while maintaining security and performance.
