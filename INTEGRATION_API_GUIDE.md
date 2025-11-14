# 🔗 Integration API Guide

Complete guide for connecting Shopify, WooCommerce, Facebook Ads, Google Ads, and Shiprocket to your D2C Analytics Platform.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Shopify Integration](#shopify-integration)
- [WooCommerce Integration](#woocommerce-integration)
- [Facebook Ads Integration](#facebook-ads-integration)
- [Google Ads Integration](#google-ads-integration)
- [Shiprocket Integration](#shiprocket-integration)
- [Managing Integrations](#managing-integrations)
- [Webhooks](#webhooks)
- [Error Handling](#error-handling)

## 🔐 Authentication

All integration endpoints require JWT authentication. Include your access token in the Authorization header:

```bash
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## 🛍️ Shopify Integration

### Method 1: OAuth Flow (Recommended)

#### Step 1: Initiate OAuth

```http
GET /api/v1/integrations/shopify/oauth/initiate?shop=mystore.myshopify.com
```

**Response:**
```json
{
  "success": true,
  "oauth_url": "https://mystore.myshopify.com/admin/oauth/authorize?client_id=...",
  "message": "Redirect user to this URL to authorize Shopify access"
}
```

#### Step 2: User Authorization

Redirect the user to the `oauth_url`. After authorization, Shopify will redirect to your callback URL with the access token.

#### Step 3: Automatic Connection

The callback endpoint will automatically:
- Exchange the code for an access token
- Save the integration to the database
- Start syncing orders, products, and customers in the background

### Method 2: Direct Connection (If you already have access token)

```http
POST /api/v1/integrations/shopify/connect
Content-Type: application/json

{
  "shop_url": "mystore.myshopify.com",
  "access_token": "shpat_xxxxxxxxxxxxx"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Shopify connected successfully. Data sync started in background.",
  "platform": "shopify"
}
```

### What Gets Synced

- **Orders**: All order details with UTM tracking for attribution
- **Products**: Product catalog with inventory levels
- **Customers**: Customer information and purchase history
- **Real-time Updates**: Webhooks for order creation/updates

## 🛒 WooCommerce Integration

### Prerequisites

1. Go to WooCommerce → Settings → Advanced → REST API
2. Generate REST API keys (Consumer Key & Secret)
3. Set permissions to "Read"

### Connect WooCommerce Store

```http
POST /api/v1/integrations/woocommerce/connect
Content-Type: application/json

{
  "store_url": "https://mystore.com",
  "consumer_key": "ck_xxxxxxxxxxxxx",
  "consumer_secret": "cs_xxxxxxxxxxxxx"
}
```

**Response:**
```json
{
  "success": true,
  "message": "WooCommerce connected successfully. Data sync started.",
  "platform": "woocommerce"
}
```

### What Gets Synced

- **Orders**: Complete order details with meta data
- **Products**: Product catalog with variations
- **Customers**: Customer profiles
- **UTM Tracking**: Attribution data from order meta

## 📢 Facebook Ads Integration

### Prerequisites

1. Create a Facebook App at developers.facebook.com
2. Add "Marketing API" permission
3. Get your Ad Account ID (format: act_123456789)
4. Generate a user access token with `ads_read` permission

### Connect Facebook Ads

```http
POST /api/v1/integrations/facebook/connect
Content-Type: application/json

{
  "access_token": "EAAxxxxxxxxxx",
  "ad_account_id": "act_123456789"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Facebook Ads connected successfully.",
  "platform": "facebook"
}
```

### What Gets Synced

- **Campaign Performance**: Impressions, clicks, conversions
- **Ad Spend**: Daily spend by campaign
- **ROAS**: Return on ad spend calculations
- **Attribution**: Sales attribution to Facebook campaigns

## 🎯 Google Ads Integration

### Prerequisites

1. Enable Google Ads API in Google Cloud Console
2. Create OAuth 2.0 credentials
3. Get your Google Ads Customer ID (10 digits, no hyphens)
4. Generate a developer token from Google Ads account
5. Obtain a refresh token via OAuth

### Connect Google Ads

```http
POST /api/v1/integrations/google-ads/connect
Content-Type: application/json

{
  "developer_token": "xxxxxxxxxxxxx",
  "client_id": "xxxxx.apps.googleusercontent.com",
  "client_secret": "xxxxxxxxxxxxx",
  "refresh_token": "1//xxxxxxxxxxxxx",
  "customer_id": "1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Google Ads connected successfully. Campaign sync started.",
  "platform": "google_ads"
}
```

### What Gets Synced

- **Campaign Metrics**: Impressions, clicks, conversions, cost
- **Keyword Performance**: Top performing keywords
- **ROAS**: Return on ad spend
- **Conversion Tracking**: Sales attribution

## 📦 Shiprocket Integration

### Prerequisites

1. Have an active Shiprocket account
2. Get your Shiprocket login credentials (email & password)

### Connect Shiprocket

```http
POST /api/v1/integrations/shiprocket/connect
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Shiprocket connected successfully.",
  "platform": "shiprocket"
}
```

**Note:** Shiprocket credentials are used to obtain an API token which is refreshed automatically.

### What Gets Synced

- **Shipments**: All shipment details and tracking info
- **Delivery Performance**: Delivery times by courier
- **RTO Analysis**: Return to origin tracking
- **Courier Comparison**: Performance metrics by courier partner

## 📊 Managing Integrations

### List All Integrations

```http
GET /api/v1/integrations/
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
      "created_at": "2024-01-10T08:00:00Z"
    },
    {
      "id": 2,
      "platform": "facebook",
      "status": "active",
      "last_sync_at": "2024-01-15T10:25:00Z",
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### Check Integration Health

```http
GET /api/v1/integrations/{integration_id}/status
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
    "created_at": "2024-01-10T08:00:00Z"
  }
}
```

**Note:** `sync_healthy` is false if no sync in last 24 hours.

### Manually Trigger Sync

```http
POST /api/v1/integrations/{integration_id}/sync
```

**Response:**
```json
{
  "success": true,
  "message": "Sync triggered for shopify"
}
```

### Disconnect Integration

```http
DELETE /api/v1/integrations/{integration_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Shopify integration disconnected successfully"
}
```

## 🔔 Webhooks

Webhooks provide real-time updates from platforms. Configure these URLs in your platform settings:

### Shopify Webhooks

Configure in Shopify Admin → Settings → Notifications → Webhooks

**Order Created:**
```
POST https://yourdomain.com/api/v1/webhooks/shopify/orders/create
```

**Order Updated:**
```
POST https://yourdomain.com/api/v1/webhooks/shopify/orders/update
```

**Format:** JSON
**API Version:** 2024-01

### WooCommerce Webhooks

Configure in WooCommerce → Settings → Advanced → Webhooks

**Orders Webhook:**
```
POST https://yourdomain.com/api/v1/webhooks/woocommerce/orders
```

**Events:** order.created, order.updated, order.deleted

### Shiprocket Webhooks

Configure in Shiprocket Dashboard → Settings → Webhooks

**Tracking Updates:**
```
POST https://yourdomain.com/api/v1/webhooks/shiprocket/tracking
```

## ⚠️ Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "error_code",
  "detail": "Human readable error message"
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 401 | Unauthorized | Check your JWT token |
| 400 | Bad Request | Verify request parameters |
| 404 | Not Found | Integration doesn't exist |
| 422 | Validation Error | Check request body format |
| 500 | Server Error | Contact support |

### Platform-Specific Errors

**Shopify:**
- `invalid_shop`: Shop URL is incorrect
- `oauth_failed`: OAuth authorization failed
- `invalid_token`: Access token is invalid or expired

**WooCommerce:**
- `invalid_credentials`: Consumer key/secret incorrect
- `connection_failed`: Cannot connect to store

**Facebook Ads:**
- `invalid_ad_account`: Ad account ID is incorrect
- `permission_denied`: Token lacks required permissions

**Google Ads:**
- `invalid_customer_id`: Customer ID format incorrect
- `authentication_failed`: Refresh token expired

**Shiprocket:**
- `login_failed`: Invalid email/password
- `token_expired`: Need to reconnect

## 🔄 Sync Frequency

- **Automatic Sync:** Every 6 hours for all integrations
- **Manual Sync:** Trigger anytime via API
- **Webhooks:** Real-time updates (when configured)

## 🛡️ Security Best Practices

1. **Never expose access tokens** in client-side code
2. **Use HTTPS** for all webhook URLs
3. **Verify webhook signatures** (automatically handled)
4. **Rotate tokens regularly** (especially for production)
5. **Use environment variables** for sensitive credentials
6. **Enable rate limiting** on webhook endpoints

## 📞 Support

For integration issues:
1. Check integration status endpoint
2. Review logs: `docker-compose logs api`
3. Verify credentials in platform dashboard
4. Check webhook configuration
5. Contact platform support if API issues persist

## 🎉 Next Steps

After connecting your platforms:

1. ✅ View unified dashboard: `GET /api/v1/d2c-analytics/dashboard`
2. ✅ Analyze marketing ROAS: `GET /api/v1/d2c-analytics/marketing`
3. ✅ Track shipping performance: `GET /api/v1/d2c-analytics/shipping`
4. ✅ Get AI forecasts: `GET /api/v1/forecast/{product_id}`
5. ✅ Monitor attribution: `GET /api/v1/d2c-analytics/attribution`

Happy integrating! 🚀
