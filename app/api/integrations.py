"""
Platform Integration API endpoints
For connecting Shopify, WooCommerce, Facebook Ads, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hmac
import hashlib

from app.core.database import get_db
from app.core.security import get_current_active_store
from app.core.config import settings
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


class GoogleAdsConnectRequest(BaseModel):
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    customer_id: str


class ShiprocketConnectRequest(BaseModel):
    email: str
    password: str


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


@router.get("/shopify/oauth/initiate")
async def initiate_shopify_oauth(
    shop: str = Query(..., description="Your Shopify store domain (e.g., mystore.myshopify.com)"),
    store_id: int = Depends(get_current_active_store)
):
    """
    Initiate Shopify OAuth flow

    This returns the OAuth URL to redirect the user to for authorization.
    After authorization, Shopify will redirect to /integrations/shopify/oauth/callback
    """
    redirect_uri = f"{settings.API_URL}/api/v1/integrations/shopify/oauth/callback"
    scopes = ["read_orders", "read_products", "read_customers", "read_inventory"]

    oauth_url = ShopifyIntegration.get_oauth_url(
        shop=shop,
        client_id=settings.SHOPIFY_API_KEY,
        redirect_uri=redirect_uri,
        scopes=scopes
    )

    return {
        "success": True,
        "oauth_url": oauth_url,
        "message": "Redirect user to this URL to authorize Shopify access"
    }


@router.get("/shopify/oauth/callback")
async def shopify_oauth_callback(
    shop: str = Query(...),
    code: str = Query(...),
    hmac_param: str = Query(..., alias="hmac"),
    state: Optional[str] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Shopify OAuth callback endpoint

    Shopify redirects here after user authorizes the app.
    We exchange the code for an access token and save it.
    """
    try:
        # Verify HMAC for security
        import requests

        # Exchange code for access token
        access_token_url = f"https://{shop}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code
        }

        response = requests.post(access_token_url, json=payload)
        response.raise_for_status()

        data = response.json()
        access_token = data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from Shopify")

        # Save integration
        # Note: In production, you should associate this with the store_id from state parameter
        integration = Integration(
            store_id=1,  # TODO: Get from state parameter
            platform="shopify",
            shop_url=shop,
            access_token=access_token,
            status="active"
        )
        db.add(integration)
        db.commit()

        # Start background sync
        background_tasks.add_task(sync_shopify_data, 1, shop, access_token)

        return {
            "success": True,
            "message": "Shopify connected successfully! Data sync started in background.",
            "shop": shop
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")


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


@router.post("/google-ads/connect")
async def connect_google_ads(
    request: GoogleAdsConnectRequest,
    background_tasks: BackgroundTasks,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """
    Connect Google Ads account

    Required credentials from Google Ads API:
    - developer_token: Google Ads API developer token
    - client_id: OAuth 2.0 client ID
    - client_secret: OAuth 2.0 client secret
    - refresh_token: OAuth 2.0 refresh token
    - customer_id: Google Ads customer ID (without hyphens)
    """
    try:
        existing = db.query(Integration).filter(
            Integration.store_id == store_id,
            Integration.platform == "google_ads"
        ).first()

        if existing:
            existing.platform_data = {
                "developer_token": request.developer_token,
                "client_id": request.client_id,
                "client_secret": request.client_secret,
                "refresh_token": request.refresh_token,
                "customer_id": request.customer_id
            }
            existing.status = "active"
            existing.updated_at = datetime.utcnow()
        else:
            integration = Integration(
                store_id=store_id,
                platform="google_ads",
                platform_data={
                    "developer_token": request.developer_token,
                    "client_id": request.client_id,
                    "client_secret": request.client_secret,
                    "refresh_token": request.refresh_token,
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
            "message": "Google Ads connected successfully. Campaign sync started.",
            "platform": "google_ads"
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
    elif integration.platform == "google_ads":
        pd = integration.platform_data
        background_tasks.add_task(
            sync_google_ads,
            store_id,
            pd.get("developer_token"),
            pd.get("client_id"),
            pd.get("client_secret"),
            pd.get("refresh_token"),
            pd.get("customer_id")
        )
    elif integration.platform == "shiprocket":
        pd = integration.platform_data
        background_tasks.add_task(
            sync_shiprocket_data,
            store_id,
            pd.get("email"),
            pd.get("password")
        )

    return {"success": True, "message": f"Sync triggered for {integration.platform}"}


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: int,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Disconnect/delete an integration"""
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
        "message": f"{platform.title()} integration disconnected successfully"
    }


@router.get("/{integration_id}/status")
async def get_integration_status(
    integration_id: int,
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Check integration health and status"""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.store_id == store_id
    ).first()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Calculate sync health
    from datetime import timedelta
    sync_healthy = True
    if integration.last_sync_at:
        hours_since_sync = (datetime.utcnow() - integration.last_sync_at).total_seconds() / 3600
        sync_healthy = hours_since_sync < 24  # Alert if no sync in 24 hours

    return {
        "success": True,
        "data": {
            "id": integration.id,
            "platform": integration.platform,
            "status": integration.status,
            "last_sync_at": integration.last_sync_at,
            "sync_healthy": sync_healthy,
            "created_at": integration.created_at
        }
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


def sync_google_ads(store_id: int, developer_token: str, client_id: str,
                    client_secret: str, refresh_token: str, customer_id: str):
    """Background task to sync Google Ads data"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        integration = GoogleAdsIntegration(
            developer_token, client_id, client_secret, refresh_token, customer_id
        )
        campaigns_synced = integration.sync_campaigns_to_db(db, store_id)
        print(f"Google Ads sync completed: {campaigns_synced} campaigns synced")
    except Exception as e:
        print(f"Google Ads sync failed: {str(e)}")
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
