"""
Shopify integration module
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hmac
import hashlib
import base64


class ShopifyIntegration:
    """
    Shopify API integration for syncing orders, products, and customers

    Features:
    - OAuth 2.0 authentication
    - Webhook handling for real-time updates
    - Order sync with full attribution data
    - Customer sync
    - Product sync
    """

    def __init__(self, shop_url: str, access_token: str):
        """
        Initialize Shopify integration

        Args:
            shop_url: Shopify store URL (e.g., 'mystore.myshopify.com')
            access_token: Shopify access token
        """
        self.shop_url = shop_url.replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.api_version = "2024-01"  # Update to latest stable version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Shopify API"""
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()

        return response.json()

    def get_orders(
        self,
        since_date: Optional[datetime] = None,
        limit: int = 250,
        status: str = "any"
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from Shopify

        Args:
            since_date: Fetch orders created after this date
            limit: Number of orders per page (max 250)
            status: Order status filter (any, open, closed, cancelled)

        Returns:
            List of orders
        """
        params = {
            "limit": min(limit, 250),
            "status": status
        }

        if since_date:
            params["created_at_min"] = since_date.isoformat()

        orders = []
        next_page = None

        while True:
            if next_page:
                response = requests.get(next_page, headers={
                    "X-Shopify-Access-Token": self.access_token
                })
            else:
                response = self._make_request("GET", "orders.json", params=params)

            batch = response.get("orders", [])
            orders.extend(batch)

            # Check for next page
            link_header = response.headers.get("Link", "")
            if 'rel="next"' in link_header:
                # Parse next URL from Link header
                next_page = link_header.split(";")[0].strip("<>")
            else:
                break

        return orders

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get single order by ID"""
        response = self._make_request("GET", f"orders/{order_id}.json")
        return response.get("order", {})

    def get_customers(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch customers from Shopify"""
        params = {"limit": 250}

        if since_date:
            params["created_at_min"] = since_date.isoformat()

        response = self._make_request("GET", "customers.json", params=params)
        return response.get("customers", [])

    def get_products(self) -> List[Dict[str, Any]]:
        """Fetch products from Shopify"""
        response = self._make_request("GET", "products.json", params={"limit": 250})
        return response.get("products", [])

    def sync_orders_to_db(self, db, store_id: int, since_date: Optional[datetime] = None):
        """
        Sync Shopify orders to database

        Args:
            db: Database session
            store_id: Store ID in our database
            since_date: Sync orders from this date
        """
        from app.models import Order, Customer

        shopify_orders = self.get_orders(since_date=since_date)

        for shopify_order in shopify_orders:
            # Check if order already exists
            existing = db.query(Order).filter(
                Order.platform == "shopify",
                Order.platform_order_id == str(shopify_order["id"])
            ).first()

            if existing:
                continue  # Skip if already synced

            # Extract customer data
            customer_data = shopify_order.get("customer", {})
            customer = None

            if customer_data:
                customer_email = customer_data.get("email")
                if customer_email:
                    customer = db.query(Customer).filter(
                        Customer.store_id == store_id,
                        Customer.email == customer_email
                    ).first()

                    if not customer:
                        customer = Customer(
                            store_id=store_id,
                            email=customer_email,
                            first_name=customer_data.get("first_name"),
                            last_name=customer_data.get("last_name"),
                            phone=customer_data.get("phone"),
                            shopify_customer_id=str(customer_data.get("id")),
                            total_orders=customer_data.get("orders_count", 0),
                            total_spent=float(customer_data.get("total_spent", 0))
                        )
                        db.add(customer)
                        db.flush()

            # Extract UTM parameters and attribution
            landing_site = shopify_order.get("landing_site", "")
            referring_site = shopify_order.get("referring_site", "")

            # Parse UTM from landing site
            utm_source = None
            utm_medium = None
            utm_campaign = None

            if "utm_source=" in landing_site:
                for param in landing_site.split("&"):
                    if "utm_source=" in param:
                        utm_source = param.split("=")[1]
                    elif "utm_medium=" in param:
                        utm_medium = param.split("=")[1]
                    elif "utm_campaign=" in param:
                        utm_campaign = param.split("=")[1]

            # Determine attributed channel
            attributed_channel = self._determine_channel(utm_source, utm_medium, referring_site)

            # Create order
            order = Order(
                store_id=store_id,
                customer_id=customer.id if customer else None,
                platform="shopify",
                platform_order_id=str(shopify_order["id"]),
                order_number=shopify_order.get("order_number"),
                subtotal=float(shopify_order.get("subtotal_price", 0)),
                tax=float(shopify_order.get("total_tax", 0)),
                shipping_cost=float(shopify_order.get("total_shipping_price_set", {}).get("shop_money", {}).get("amount", 0)),
                discount=float(shopify_order.get("total_discounts", 0)),
                total=float(shopify_order.get("total_price", 0)),
                currency=shopify_order.get("currency"),
                line_items=[{
                    "product_id": item.get("product_id"),
                    "variant_id": item.get("variant_id"),
                    "title": item.get("title"),
                    "quantity": item.get("quantity"),
                    "price": item.get("price")
                } for item in shopify_order.get("line_items", [])],
                item_count=sum(item.get("quantity", 0) for item in shopify_order.get("line_items", [])),
                financial_status=shopify_order.get("financial_status"),
                fulfillment_status=shopify_order.get("fulfillment_status"),
                customer_email=customer_data.get("email") if customer_data else None,
                shipping_address=shopify_order.get("shipping_address"),
                billing_address=shopify_order.get("billing_address"),
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                referrer=referring_site,
                landing_page=landing_site,
                attributed_channel=attributed_channel,
                order_date=datetime.fromisoformat(shopify_order["created_at"].replace("Z", "+00:00"))
            )

            db.add(order)

        db.commit()
        return len(shopify_orders)

    def _determine_channel(self, utm_source: str, utm_medium: str, referrer: str) -> str:
        """Determine marketing channel from attribution data"""
        if utm_source:
            utm_source_lower = utm_source.lower()
            if "facebook" in utm_source_lower or "fb" in utm_source_lower or "instagram" in utm_source_lower:
                return "facebook"
            elif "google" in utm_source_lower or "goog" in utm_source_lower:
                return "google"
            elif "email" in utm_source_lower or "newsletter" in utm_source_lower:
                return "email"
            elif "whatsapp" in utm_source_lower:
                return "whatsapp"

        if referrer:
            referrer_lower = referrer.lower()
            if "facebook.com" in referrer_lower or "instagram.com" in referrer_lower:
                return "facebook"
            elif "google.com" in referrer_lower:
                return "google"

        return "direct"

    @staticmethod
    def verify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
        """
        Verify Shopify webhook signature

        Args:
            data: Raw webhook payload
            hmac_header: HMAC header from Shopify
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        computed_hmac = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(computed_hmac, hmac_header)

    def create_webhook(self, topic: str, address: str) -> Dict[str, Any]:
        """
        Create webhook subscription

        Args:
            topic: Webhook topic (e.g., 'orders/create', 'orders/updated')
            address: Callback URL

        Returns:
            Webhook details
        """
        data = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json"
            }
        }

        response = self._make_request("POST", "webhooks.json", json=data)
        return response.get("webhook", {})

    @staticmethod
    def get_oauth_url(shop: str, client_id: str, redirect_uri: str, scopes: List[str]) -> str:
        """
        Generate OAuth authorization URL

        Args:
            shop: Shop domain (e.g., 'mystore.myshopify.com')
            client_id: Shopify API key
            redirect_uri: OAuth redirect URI
            scopes: List of permission scopes

        Returns:
            Authorization URL
        """
        scope_string = ",".join(scopes)
        return (
            f"https://{shop}/admin/oauth/authorize?"
            f"client_id={client_id}&"
            f"scope={scope_string}&"
            f"redirect_uri={redirect_uri}"
        )

    def exchange_code_for_token(self, shop: str, code: str, client_id: str, client_secret: str) -> str:
        """
        Exchange authorization code for access token

        Args:
            shop: Shop domain
            code: Authorization code
            client_id: Shopify API key
            client_secret: Shopify API secret

        Returns:
            Access token
        """
        url = f"https://{shop}/admin/oauth/access_token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        return response.json().get("access_token")
