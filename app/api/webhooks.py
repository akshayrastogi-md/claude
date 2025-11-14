"""
Webhook endpoints for real-time platform updates
Handles webhooks from Shopify, WooCommerce, Facebook, etc.
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import json

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.models import Integration, Order
from app.integrations import ShopifyIntegration

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/shopify/orders/create")
async def shopify_order_created_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """
    Handle Shopify order creation webhook

    Shopify sends this webhook when a new order is created.
    We verify the HMAC signature and sync the order to our database.
    """
    try:
        # Read raw body for HMAC verification
        body = await request.body()

        # Verify webhook signature
        if x_shopify_hmac_sha256 and settings.SHOPIFY_WEBHOOK_SECRET:
            is_valid = ShopifyIntegration.verify_webhook(
                body,
                x_shopify_hmac_sha256,
                settings.SHOPIFY_WEBHOOK_SECRET
            )
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse order data
        order_data = json.loads(body)

        # Process order in background
        background_tasks.add_task(
            process_shopify_order_webhook,
            x_shopify_shop_domain,
            order_data
        )

        return {"success": True, "message": "Webhook received"}

    except Exception as e:
        print(f"Shopify webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shopify/orders/update")
async def shopify_order_updated_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None)
):
    """Handle Shopify order update webhook"""
    try:
        body = await request.body()

        # Verify signature
        if x_shopify_hmac_sha256 and settings.SHOPIFY_WEBHOOK_SECRET:
            is_valid = ShopifyIntegration.verify_webhook(
                body,
                x_shopify_hmac_sha256,
                settings.SHOPIFY_WEBHOOK_SECRET
            )
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        order_data = json.loads(body)

        background_tasks.add_task(
            update_shopify_order_webhook,
            x_shopify_shop_domain,
            order_data
        )

        return {"success": True}

    except Exception as e:
        print(f"Shopify order update webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/woocommerce/orders")
async def woocommerce_order_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_wc_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle WooCommerce order webhooks

    WooCommerce sends webhooks for order.created, order.updated, order.deleted
    """
    try:
        body = await request.body()
        order_data = json.loads(body)

        # Verify signature if configured
        # WooCommerce uses HMAC SHA256

        # Extract store from webhook data
        store_url = order_data.get("_links", {}).get("self", [{}])[0].get("href", "")

        background_tasks.add_task(
            process_woocommerce_order_webhook,
            store_url,
            order_data
        )

        return {"success": True, "message": "Webhook received"}

    except Exception as e:
        print(f"WooCommerce webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shiprocket/tracking")
async def shiprocket_tracking_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Shiprocket tracking updates

    Shiprocket sends webhooks for shipment status changes
    """
    try:
        body = await request.body()
        tracking_data = json.loads(body)

        background_tasks.add_task(
            process_shiprocket_tracking_webhook,
            tracking_data
        )

        return {"success": True, "message": "Tracking update received"}

    except Exception as e:
        print(f"Shiprocket webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Background webhook processors

def process_shopify_order_webhook(shop_domain: str, order_data: dict):
    """Process Shopify order creation webhook in background"""
    db = SessionLocal()
    try:
        # Find integration by shop domain
        integration = db.query(Integration).filter(
            Integration.platform == "shopify",
            Integration.shop_url == shop_domain,
            Integration.status == "active"
        ).first()

        if not integration:
            print(f"No active Shopify integration found for {shop_domain}")
            return

        # Extract order details
        from app.models import Order, Customer

        # Check if order already exists
        existing_order = db.query(Order).filter(
            Order.platform == "shopify",
            Order.platform_order_id == str(order_data["id"])
        ).first()

        if existing_order:
            print(f"Order {order_data['id']} already exists, skipping")
            return

        # Create order
        order = Order(
            store_id=integration.store_id,
            platform="shopify",
            platform_order_id=str(order_data["id"]),
            order_number=order_data.get("order_number"),
            total_amount=float(order_data.get("total_price", 0)),
            currency=order_data.get("currency", "USD"),
            status=order_data.get("financial_status", "pending"),
            # Extract UTM parameters if available
            utm_source=order_data.get("source_name"),
            attributed_channel="shopify",
            order_date=order_data.get("created_at")
        )

        db.add(order)
        db.commit()

        print(f"Shopify order {order_data['id']} synced successfully via webhook")

    except Exception as e:
        print(f"Error processing Shopify order webhook: {str(e)}")
        db.rollback()
    finally:
        db.close()


def update_shopify_order_webhook(shop_domain: str, order_data: dict):
    """Update existing Shopify order from webhook"""
    db = SessionLocal()
    try:
        # Find the order
        order = db.query(Order).filter(
            Order.platform == "shopify",
            Order.platform_order_id == str(order_data["id"])
        ).first()

        if order:
            # Update order fields
            order.status = order_data.get("financial_status", order.status)
            order.total_amount = float(order_data.get("total_price", order.total_amount))
            db.commit()
            print(f"Shopify order {order_data['id']} updated via webhook")

    except Exception as e:
        print(f"Error updating Shopify order webhook: {str(e)}")
        db.rollback()
    finally:
        db.close()


def process_woocommerce_order_webhook(store_url: str, order_data: dict):
    """Process WooCommerce order webhook in background"""
    db = SessionLocal()
    try:
        # Find integration
        integration = db.query(Integration).filter(
            Integration.platform == "woocommerce",
            Integration.status == "active"
        ).first()

        if not integration:
            print(f"No active WooCommerce integration found")
            return

        # Check if order exists
        from app.models import Order

        existing_order = db.query(Order).filter(
            Order.platform == "woocommerce",
            Order.platform_order_id == str(order_data["id"])
        ).first()

        if existing_order:
            # Update existing order
            existing_order.status = order_data.get("status", existing_order.status)
            existing_order.total_amount = float(order_data.get("total", existing_order.total_amount))
        else:
            # Create new order
            order = Order(
                store_id=integration.store_id,
                platform="woocommerce",
                platform_order_id=str(order_data["id"]),
                order_number=order_data.get("number"),
                total_amount=float(order_data.get("total", 0)),
                currency=order_data.get("currency", "USD"),
                status=order_data.get("status", "pending"),
                order_date=order_data.get("date_created")
            )
            db.add(order)

        db.commit()
        print(f"WooCommerce order {order_data['id']} synced via webhook")

    except Exception as e:
        print(f"Error processing WooCommerce order webhook: {str(e)}")
        db.rollback()
    finally:
        db.close()


def process_shiprocket_tracking_webhook(tracking_data: dict):
    """Process Shiprocket tracking update webhook"""
    db = SessionLocal()
    try:
        from app.models import Shipment

        awb_code = tracking_data.get("awb_code")
        if not awb_code:
            return

        # Find shipment
        shipment = db.query(Shipment).filter(
            Shipment.awb_code == awb_code
        ).first()

        if shipment:
            # Update tracking status
            shipment.status = tracking_data.get("current_status")
            shipment.tracking_data = tracking_data

            # Check if RTO
            if tracking_data.get("current_status") in ["RTO Delivered", "RTO In Transit"]:
                shipment.is_rto = True

            db.commit()
            print(f"Shipment {awb_code} tracking updated via webhook")

    except Exception as e:
        print(f"Error processing Shiprocket tracking webhook: {str(e)}")
        db.rollback()
    finally:
        db.close()
