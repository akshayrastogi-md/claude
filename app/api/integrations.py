"""
Platform Integration API endpoints
For connecting Shopify, WooCommerce, Facebook Ads, Google Ads, and Shiprocket
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_store
from app.models import Integration
from app.integrations import (
    ShopifyIntegration,
    WooCommerceIntegration,
    FacebookAdsIntegration,
    GoogleAdsIntegration,
    ShiprocketIntegration
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class ShopifyConnectRequest(BaseModel):
    shop_url: str
    access_token: str


class WooCommerceConnectRequest(BaseModel):
    store_url: str
    consumer_key: str
    consumer_secret: str


class FacebookAdsConnectRequest(BaseModel):
    access_token: str
    ad_account_id: str


class ShiprocketConnectRequest(BaseModel):
    email: str
    password: str


class GoogleAdsConnectRequest(BaseModel):
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    customer_id: str


class OAuthInitRequest(BaseModel):
    platform: str  # shopify, facebook, google
    redirect_uri: str
    shop_url: Optional[str] = None  # Required for Shopify


@router.get("/")
async def list_integrations(
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """List all connected integrations"""
    integrations = db.query(Integration).filter(
        Integration.store_id == store_id
    ).all()

    return {
        "success": True,
        "data": [
            {
                "id": i.id,
                "platform": i.platform,
                "status": i.status,
                "last_sync_at": i.last_sync_at,
                "created_at": i.created_at
            }
            for i in integrations
        ]
    }


@router.post("/shopify/connect")
async def connect_shopify(
    request: ShopifyConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """
    Connect Shopify store

    This will:
    1. Save integration credentials
    2. Start background sync of orders, customers, products
    3. Set up webhooks for real-time updates
    """
    try:
        # Check if already connected
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "shopify"
        ).first()

        if existing:
            # Update existing
            existing.access_token = request.access_token
            existing.shop_url = request.shop_url
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            integration = Integration(
                store_id=store_id,
                platform="shopify",
                access_token=request.access_token,
                shop_url=request.shop_url,
                status="active"
            )
            db.add(integration)

        db.commit()

        # Start background sync
        background_tasks.add_task(
            sync_shopify_data,
            store_id,
            request.shop_url,
            request.access_token
        )

        return {
            "success": True,
            "message": "Shopify connected successfully. Data sync started in background.",
            "platform": "shopify"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Shopify connection failed: {str(e)}")


@router.post("/woocommerce/connect")
async def connect_woocommerce(
    request: WooCommerceConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Connect WooCommerce store"""
    try:
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "woocommerce"
        ).first()

        if existing:
            existing.shop_url = request.store_url
            existing.access_token = request.consumer_key
            existing.platform_data = {"consumer_secret": request.consumer_secret}
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            integration = Integration(
                store_id=store_id,
                platform="woocommerce",
                shop_url=request.store_url,
                access_token=request.consumer_key,
                platform_data={"consumer_secret": request.consumer_secret},
                status="active"
            )
            db.add(integration)

        db.commit()

        # Start background sync
        background_tasks.add_task(
            sync_woocommerce_data,
            store_id,
            request.store_url,
            request.consumer_key,
            request.consumer_secret
        )

        return {
            "success": True,
            "message": "WooCommerce connected successfully. Data sync started.",
            "platform": "woocommerce"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/facebook/connect")
async def connect_facebook_ads(
    request: FacebookAdsConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Connect Facebook Ads account"""
    try:
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "facebook"
        ).first()

        if existing:
            existing.access_token = request.access_token
            existing.platform_data = {"ad_account_id": request.ad_account_id}
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            integration = Integration(
                store_id=store_id,
                platform="facebook",
                access_token=request.access_token,
                platform_data={"ad_account_id": request.ad_account_id},
                status="active"
            )
            db.add(integration)

        db.commit()

        # Start background sync
        background_tasks.add_task(
            sync_facebook_ads,
            store_id,
            request.access_token,
            request.ad_account_id
        )

        return {
            "success": True,
            "message": "Facebook Ads connected successfully.",
            "platform": "facebook"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shiprocket/connect")
async def connect_shiprocket(
    request: ShiprocketConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Connect Shiprocket account"""
    try:
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "shiprocket"
        ).first()

        if existing:
            existing.platform_data = {
                "email": request.email,
                "password": request.password  # In production, encrypt this!
            }
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            integration = Integration(
                store_id=store_id,
                platform="shiprocket",
                platform_data={
                    "email": request.email,
                    "password": request.password
                },
                status="active"
            )
            db.add(integration)

        db.commit()

        # Start background sync
        background_tasks.add_task(
            sync_shiprocket_data,
            store_id,
            request.email,
            request.password
        )

        return {
            "success": True,
            "message": "Shiprocket connected successfully.",
            "platform": "shiprocket"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/google-ads/connect")
async def connect_google_ads(
    request: GoogleAdsConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Connect Google Ads account"""
    try:
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "google"
        ).first()

        if existing:
            existing.access_token = request.developer_token
            existing.refresh_token = request.refresh_token
            existing.platform_data = {
                "client_id": request.client_id,
                "client_secret": request.client_secret,
                "customer_id": request.customer_id
            }
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            integration = Integration(
                store_id=store_id,
                platform="google",
                access_token=request.developer_token,
                refresh_token=request.refresh_token,
                platform_data={
                    "client_id": request.client_id,
                    "client_secret": request.client_secret,
                    "customer_id": request.customer_id
                },
                status="active"
            )
            db.add(integration)

        db.commit()

        # Start background sync
        background_tasks.add_task(
            sync_google_ads,
            store_id,
            request.developer_token,
            request.client_id,
            request.client_secret,
            request.refresh_token,
            request.customer_id
        )

        return {
            "success": True,
            "message": "Google Ads connected successfully.",
            "platform": "google"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{integration_id}/sync")
async def trigger_sync(
    integration_id: int,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Manually trigger data sync for an integration"""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.store_id == store_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Trigger sync based on platform
    if integration.platform == "shopify":
        background_tasks.add_task(
            sync_shopify_data,
            store_id,
            integration.shop_url,
            integration.access_token
        )
    elif integration.platform == "woocommerce":
        background_tasks.add_task(
            sync_woocommerce_data,
            store_id,
            integration.shop_url,
            integration.access_token,
            integration.platform_data.get("consumer_secret")
        )
    elif integration.platform == "facebook":
        background_tasks.add_task(
            sync_facebook_ads,
            store_id,
            integration.access_token,
            integration.platform_data.get("ad_account_id")
        )
    elif integration.platform == "google":
        background_tasks.add_task(
            sync_google_ads,
            store_id,
            integration.access_token,
            integration.platform_data.get("client_id"),
            integration.platform_data.get("client_secret"),
            integration.refresh_token,
            integration.platform_data.get("customer_id")
        )
    elif integration.platform == "shiprocket":
        background_tasks.add_task(
            sync_shiprocket_data,
            store_id,
            integration.platform_data.get("email"),
            integration.platform_data.get("password")
        )

    return {"success": True, "message": f"Sync triggered for {integration.platform}"}


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: int,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Disconnect and delete an integration"""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.store_id == store_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    platform = integration.platform
    db.delete(integration)
    db.commit()

    return {
        "success": True,
        "message": f"{platform.capitalize()} integration disconnected successfully"
    }


@router.post("/oauth/init")
async def init_oauth_flow(request: OAuthInitRequest):
    """
    Initialize OAuth flow for a platform
    Returns the authorization URL to redirect the user to
    """
    import os

    if request.platform == "shopify":
        if not request.shop_url:
            raise HTTPException(status_code=400, detail="shop_url is required for Shopify")

        client_id = os.getenv("SHOPIFY_API_KEY")
        scopes = ["read_orders", "read_products", "read_customers", "read_fulfillments"]

        auth_url = ShopifyIntegration.get_oauth_url(
            shop=request.shop_url,
            client_id=client_id,
            redirect_uri=request.redirect_uri,
            scopes=scopes
        )

        return {
            "success": True,
            "platform": "shopify",
            "authorization_url": auth_url
        }

    elif request.platform == "facebook":
        client_id = os.getenv("FACEBOOK_APP_ID")
        scopes = ["ads_read", "ads_management", "business_management"]

        auth_url = FacebookAdsIntegration.generate_auth_url(
            client_id=client_id,
            redirect_uri=request.redirect_uri,
            scopes=scopes
        )

        return {
            "success": True,
            "platform": "facebook",
            "authorization_url": auth_url
        }

    elif request.platform == "google":
        client_id = os.getenv("GOOGLE_CLIENT_ID")

        auth_url = GoogleAdsIntegration.generate_oauth_url(
            client_id=client_id,
            redirect_uri=request.redirect_uri
        )

        return {
            "success": True,
            "platform": "google",
            "authorization_url": auth_url
        }

    else:
        raise HTTPException(status_code=400, detail=f"OAuth not supported for platform: {request.platform}")


@router.get("/oauth/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str,
    shop: Optional[str] = None,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from platforms
    Exchange authorization code for access token
    """
    import os

    try:
        if platform == "shopify":
            if not shop:
                raise HTTPException(status_code=400, detail="shop parameter is required")

            client_id = os.getenv("SHOPIFY_API_KEY")
            client_secret = os.getenv("SHOPIFY_API_SECRET")

            integration_obj = ShopifyIntegration(shop, "")
            access_token = integration_obj.exchange_code_for_token(
                shop=shop,
                code=code,
                client_id=client_id,
                client_secret=client_secret
            )

            # Save integration
            existing = db.query(Integration).filter(
                Integration.store_id == store_id,
                Integration.platform == "shopify"
            ).first()

            if existing:
                existing.access_token = access_token
                existing.shop_url = shop
                existing.status = "active"
                existing.updated_at = datetime.utcnow()
            else:
                integration = Integration(
                    store_id=store_id,
                    platform="shopify",
                    access_token=access_token,
                    shop_url=shop,
                    status="active"
                )
                db.add(integration)

            db.commit()

            return {
                "success": True,
                "message": "Shopify connected successfully",
                "platform": "shopify"
            }

        elif platform == "facebook":
            client_id = os.getenv("FACEBOOK_APP_ID")
            client_secret = os.getenv("FACEBOOK_APP_SECRET")
            redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")

            integration_obj = FacebookAdsIntegration("", "")
            access_token = integration_obj.exchange_code_for_token(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri
            )

            # Save integration (ad_account_id needs to be set separately)
            existing = db.query(Integration).filter(
                Integration.store_id == store_id,
                Integration.platform == "facebook"
            ).first()

            if existing:
                existing.access_token = access_token
                existing.status = "active"
                existing.updated_at = datetime.utcnow()
            else:
                integration = Integration(
                    store_id=store_id,
                    platform="facebook",
                    access_token=access_token,
                    status="pending"  # User needs to select ad account
                )
                db.add(integration)

            db.commit()

            return {
                "success": True,
                "message": "Facebook Ads connected. Please select your ad account.",
                "platform": "facebook",
                "next_step": "Call /integrations/facebook/select-account with ad_account_id"
            }

        else:
            raise HTTPException(status_code=400, detail=f"OAuth callback not supported for: {platform}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")


@router.post("/facebook/select-account")
async def select_facebook_ad_account(
    ad_account_id: str,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Select Facebook ad account after OAuth"""
    integration = db.query(Integration).filter(
        Integration.store_id == store_id,
        Integration.platform == "facebook"
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Facebook integration not found")

    integration.platform_data = {"ad_account_id": ad_account_id}
    integration.status = "active"
    integration.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "Facebook ad account selected successfully"
    }


# Background sync functions
def sync_shopify_data(store_id: int, shop_url: str, access_token: str):
    """Background task to sync Shopify data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = ShopifyIntegration(shop_url, access_token)
        orders_synced = integration.sync_orders_to_db(db, store_id)
        print(f"Shopify sync completed: {orders_synced} orders synced")
    except Exception as e:
        print(f"Shopify sync failed: {str(e)}")
    finally:
        db.close()


def sync_woocommerce_data(store_id: int, store_url: str, consumer_key: str, consumer_secret: str):
    """Background task to sync WooCommerce data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = WooCommerceIntegration(store_url, consumer_key, consumer_secret)
        orders_synced = integration.sync_orders_to_db(db, store_id)
        print(f"WooCommerce sync completed: {orders_synced} orders synced")
    except Exception as e:
        print(f"WooCommerce sync failed: {str(e)}")
    finally:
        db.close()


def sync_facebook_ads(store_id: int, access_token: str, ad_account_id: str):
    """Background task to sync Facebook Ads data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = FacebookAdsIntegration(access_token, ad_account_id)
        campaigns_synced = integration.sync_campaigns_to_db(db, store_id)
        print(f"Facebook Ads sync completed: {campaigns_synced} campaigns synced")
    except Exception as e:
        print(f"Facebook Ads sync failed: {str(e)}")
    finally:
        db.close()


def sync_shiprocket_data(store_id: int, email: str, password: str):
    """Background task to sync Shiprocket data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = ShiprocketIntegration(email, password)
        shipments_synced = integration.sync_shipments_to_db(db, store_id)
        print(f"Shiprocket sync completed: {shipments_synced} shipments synced")
    except Exception as e:
        print(f"Shiprocket sync failed: {str(e)}")
    finally:
        db.close()


def sync_google_ads(store_id: int, developer_token: str, client_id: str, client_secret: str, refresh_token: str, customer_id: str):
    """Background task to sync Google Ads data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = GoogleAdsIntegration(
            developer_token=developer_token,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            customer_id=customer_id
        )
        campaigns_synced = integration.sync_campaigns_to_db(db, store_id)
        print(f"Google Ads sync completed: {campaigns_synced} campaigns synced")
    except Exception as e:
        print(f"Google Ads sync failed: {str(e)}")
    finally:
        db.close()


# ============================================
# WEBHOOK HANDLERS
# ============================================

@router.post("/webhooks/shopify/orders")
async def shopify_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """
    Handle Shopify webhooks for real-time order updates

    Shopify sends webhooks for:
    - orders/create
    - orders/updated
    - orders/cancelled
    """
    import os

    # Verify webhook signature
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")

    if not hmac_header or not shop_domain:
        raise HTTPException(status_code=401, detail="Missing webhook headers")

    body = await request.body()
    webhook_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")

    if not ShopifyIntegration.verify_webhook(body, hmac_header, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Find integration by shop domain
    integration = db.query(Integration).filter(
        Integration.platform == "shopify",
        Integration.shop_url == shop_domain
    ).first()

    if not integration:
        return {"success": False, "message": "Integration not found"}

    # Process webhook data
    import json
    webhook_data = json.loads(body)

    # Sync this specific order
    shopify_integration = ShopifyIntegration(integration.shop_url, integration.access_token)

    # You can add specific order sync logic here
    # For now, just acknowledge receipt

    return {"success": True, "message": "Webhook received"}


@router.post("/webhooks/woocommerce/orders")
async def woocommerce_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """
    Handle WooCommerce webhooks for real-time order updates

    Topics: order.created, order.updated, order.deleted
    """
    # Get webhook signature
    signature = request.headers.get("X-WC-Webhook-Signature")

    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    body = await request.body()

    # You'll need to store webhook secret in integration settings
    # For now, just acknowledge

    return {"success": True, "message": "Webhook received"}


@router.post("/webhooks/shiprocket/tracking")
async def shiprocket_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """
    Handle Shiprocket webhooks for shipment tracking updates

    Events:
    - Order picked up
    - In transit
    - Out for delivery
    - Delivered
    - RTO initiated
    - RTO delivered
    """
    import json

    body = await request.body()
    webhook_data = json.loads(body)

    # Extract shipment info
    awb = webhook_data.get("awb")
    current_status = webhook_data.get("current_status")

    # Update shipment in database
    from app.models import Shipment

    shipment = db.query(Shipment).filter(Shipment.awb_code == awb).first()

    if shipment:
        shipment.status = current_status
        shipment.current_status = webhook_data.get("current_status_body")

        if "delivered" in current_status.lower():
            shipment.is_delivered = True
            shipment.delivered_date = datetime.utcnow()
        elif "rto" in current_status.lower():
            shipment.is_rto = True

        shipment.updated_at = datetime.utcnow()
        db.commit()

    return {"success": True, "message": "Tracking update received"}
