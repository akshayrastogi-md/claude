# Platform Integrations Guide

Complete guide for integrating your D2C brand's platforms with the Analytics & Forecasting SaaS.

---

## Table of Contents

1. [Overview](#overview)
2. [Shopify Integration](#shopify-integration)
3. [WooCommerce Integration](#woocommerce-integration)
4. [Facebook Ads Integration](#facebook-ads-integration)
5. [Google Ads Integration](#google-ads-integration)
6. [Shiprocket Integration](#shiprocket-integration)
7. [Webhooks Setup](#webhooks-setup)
8. [API Reference](#api-reference)

---

## Overview

Our platform supports integration with:

- **E-commerce**: Shopify, WooCommerce
- **Marketing**: Facebook Ads, Google Ads
- **Shipping**: Shiprocket

All integrations use secure OAuth 2.0 authentication (where supported) and store credentials encrypted in the database.

---

## Shopify Integration

### Prerequisites

1. Create a Shopify App in your Partner Dashboard
2. Get your API Key and API Secret
3. Configure OAuth redirect URI

### Setup Steps

#### Step 1: Configure Environment Variables

```bash
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_REDIRECT_URI=https://yourapp.com/api/v1/integrations/oauth/callback/shopify
```

#### Step 2: Initiate OAuth Flow

```bash
POST /api/v1/integrations/oauth/init
{
  "platform": "shopify",
  "shop_url": "mystore.myshopify.com",
  "redirect_uri": "https://yourapp.com/callback"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "shopify",
  "authorization_url": "https://mystore.myshopify.com/admin/oauth/authorize?client_id=..."
}
```

#### Step 3: User Authorizes

Redirect user to the `authorization_url`. After authorization, Shopify redirects to your callback with a `code`.

#### Step 4: Exchange Code for Token

This happens automatically when Shopify redirects to:
```
GET /api/v1/integrations/oauth/callback/shopify?code=xxx&shop=mystore.myshopify.com
```

The platform automatically:
- Exchanges code for access token
- Saves integration to database
- Starts background sync of orders, products, customers

#### Step 5: Manual Sync (Optional)

```bash
POST /api/v1/integrations/{integration_id}/sync
```

### What Gets Synced

- **Orders**: All orders with UTM tracking, customer data, line items
- **Customers**: Customer profiles, total orders, total spent
- **Products**: Product catalog with variants
- **Attribution**: UTM parameters, referrer, landing page

### Webhooks

Set up webhooks in Shopify for real-time updates:

**Webhook URL:** `https://yourapp.com/api/v1/integrations/webhooks/shopify/orders`

**Topics:**
- `orders/create` - New order created
- `orders/updated` - Order updated
- `orders/cancelled` - Order cancelled

---

## WooCommerce Integration

### Prerequisites

1. WooCommerce REST API enabled
2. Generate API keys in WooCommerce > Settings > Advanced > REST API

### Setup Steps

#### Step 1: Get API Credentials

In WooCommerce admin:
1. Go to WooCommerce > Settings > Advanced > REST API
2. Click "Add Key"
3. Select "Read/Write" permissions
4. Copy the Consumer Key and Consumer Secret

#### Step 2: Connect WooCommerce

```bash
POST /api/v1/integrations/woocommerce/connect
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

#### Step 3: Verify Connection

```bash
GET /api/v1/integrations/
```

### What Gets Synced

- **Orders**: All orders with metadata, customer data
- **Customers**: Customer profiles with billing/shipping info
- **Products**: Product catalog
- **UTM Tracking**: From order metadata (if plugin installed)

### UTM Tracking Setup

Install a WooCommerce plugin that captures UTM parameters:
- WooCommerce Google Analytics Integration
- UTM Tracking for WooCommerce

The plugin should store UTM data in order meta with keys:
- `utm_source`
- `utm_medium`
- `utm_campaign`

### Webhooks

**Webhook URL:** `https://yourapp.com/api/v1/integrations/webhooks/woocommerce/orders`

**Topics:**
- `order.created`
- `order.updated`
- `order.deleted`

Configure in: WooCommerce > Settings > Advanced > Webhooks

---

## Facebook Ads Integration

### Prerequisites

1. Facebook Business Manager account
2. Facebook App created
3. Ad Account ID

### Setup Steps

#### Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add "Marketing API" product
4. Get App ID and App Secret

#### Step 2: Configure Environment

```bash
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_REDIRECT_URI=https://yourapp.com/api/v1/integrations/oauth/callback/facebook
```

#### Step 3: Initiate OAuth

```bash
POST /api/v1/integrations/oauth/init
{
  "platform": "facebook",
  "redirect_uri": "https://yourapp.com/callback"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "facebook",
  "authorization_url": "https://www.facebook.com/v18.0/dialog/oauth?..."
}
```

#### Step 4: User Authorizes

Redirect user to `authorization_url`. Facebook redirects back with code.

#### Step 5: Select Ad Account

After OAuth callback, select which ad account to track:

```bash
POST /api/v1/integrations/facebook/select-account
{
  "ad_account_id": "act_123456789"
}
```

### What Gets Synced

- **Campaigns**: All active and paused campaigns
- **Performance Metrics**:
  - Spend
  - Impressions
  - Clicks
  - CTR, CPC, CPM
  - Conversions
  - Revenue (if conversion tracking set up)
  - ROAS calculation

### Required Facebook Setup

For revenue tracking, set up Facebook Pixel and Conversion API with purchase events.

---

## Google Ads Integration

### Prerequisites

1. Google Ads account
2. Google Cloud Project with OAuth credentials
3. Google Ads Developer Token

### Setup Steps

#### Step 1: Get Developer Token

1. Go to [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Apply for developer token
3. Wait for approval (can take a few days)

#### Step 2: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Ads API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://yourapp.com/api/v1/integrations/oauth/callback/google`

#### Step 3: Configure Environment

```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_DEVELOPER_TOKEN=your_developer_token
GOOGLE_REDIRECT_URI=https://yourapp.com/api/v1/integrations/oauth/callback/google
```

#### Step 4: OAuth Flow

```bash
POST /api/v1/integrations/oauth/init
{
  "platform": "google",
  "redirect_uri": "https://yourapp.com/callback"
}
```

Follow authorization URL, then connect with credentials:

```bash
POST /api/v1/integrations/google-ads/connect
{
  "developer_token": "your_developer_token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "your_refresh_token",
  "customer_id": "1234567890"
}
```

### What Gets Synced

- **Campaigns**: All campaigns (Search, Shopping, Display, Video)
- **Performance Metrics**:
  - Cost
  - Impressions
  - Clicks
  - CTR, CPC
  - Conversions
  - Conversion value
  - ROAS

### Notes

Google Ads uses a more complex API. For production, we recommend using the official `google-ads` Python library which is included in `requirements.txt`.

---

## Shiprocket Integration

### Prerequisites

1. Shiprocket account
2. Email and password

### Setup Steps

#### Connect Shiprocket

```bash
POST /api/v1/integrations/shiprocket/connect
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

### What Gets Synced

- **Shipments**: All shipment records
- **Tracking Data**:
  - AWB (tracking number)
  - Courier name
  - Current status
  - Pickup date
  - Delivery date
  - Delivery days
- **Performance Metrics**:
  - RTO (Return to Origin) tracking
  - Delivery success rate
  - Average delivery time
  - Shipping costs
  - COD charges

### Webhooks

**Webhook URL:** `https://yourapp.com/api/v1/integrations/webhooks/shiprocket/tracking`

Configure in Shiprocket dashboard to get real-time tracking updates for:
- Order picked up
- In transit
- Out for delivery
- Delivered
- RTO initiated
- RTO delivered

---

## Webhooks Setup

### Security

All webhooks verify signatures to ensure authenticity:

- **Shopify**: HMAC SHA256 verification
- **WooCommerce**: Base64 HMAC SHA256
- **Shiprocket**: Platform-specific verification

### Webhook Endpoints

| Platform | Endpoint | Method |
|----------|----------|--------|
| Shopify | `/api/v1/integrations/webhooks/shopify/orders` | POST |
| WooCommerce | `/api/v1/integrations/webhooks/woocommerce/orders` | POST |
| Shiprocket | `/api/v1/integrations/webhooks/shiprocket/tracking` | POST |

### Example: Setting up Shopify Webhook

```bash
POST https://{shop}.myshopify.com/admin/api/2024-01/webhooks.json
{
  "webhook": {
    "topic": "orders/create",
    "address": "https://yourapp.com/api/v1/integrations/webhooks/shopify/orders",
    "format": "json"
  }
}
```

---

## API Reference

### List All Integrations

```bash
GET /api/v1/integrations/
Authorization: Bearer {token}
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

### Disconnect Integration

```bash
DELETE /api/v1/integrations/{integration_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Shopify integration disconnected successfully"
}
```

### Manual Sync

```bash
POST /api/v1/integrations/{integration_id}/sync
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Sync triggered for shopify"
}
```

---

## Troubleshooting

### Common Issues

#### 1. OAuth Callback Fails

**Solution:**
- Verify redirect URI matches exactly in platform settings
- Check environment variables are set correctly
- Ensure HTTPS is used (most platforms require it)

#### 2. Webhook Not Receiving Data

**Solution:**
- Verify webhook URL is publicly accessible
- Check webhook secret is configured correctly
- Test webhook signature verification
- Check platform webhook logs

#### 3. Data Not Syncing

**Solution:**
- Check integration status: `GET /api/v1/integrations/`
- Trigger manual sync: `POST /api/v1/integrations/{id}/sync`
- Check API credentials are valid
- Review application logs for errors

#### 4. Facebook/Google OAuth Expired

**Solution:**
- Most platforms provide refresh tokens
- Implement token refresh logic
- User may need to re-authorize

---

## Best Practices

1. **Security**
   - Always use HTTPS for OAuth callbacks
   - Store credentials encrypted in production
   - Rotate API keys regularly
   - Use environment variables for secrets

2. **Data Sync**
   - Set up webhooks for real-time updates
   - Run daily background sync as backup
   - Implement retry logic for failed syncs
   - Log all sync operations

3. **Error Handling**
   - Implement exponential backoff for API rate limits
   - Log all integration errors
   - Notify users of failed integrations
   - Provide clear error messages

4. **Testing**
   - Test OAuth flow end-to-end
   - Verify webhook signature validation
   - Test with sandbox/development accounts first
   - Monitor sync performance

---

## Need Help?

- Check platform-specific documentation
- Review API logs for detailed error messages
- Contact support: support@yourplatform.com
- Report issues: https://github.com/your-repo/issues

---

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Shopify integration with OAuth
- WooCommerce REST API integration
- Facebook Ads Marketing API
- Google Ads API (basic implementation)
- Shiprocket logistics integration
- Webhook handlers for all platforms
