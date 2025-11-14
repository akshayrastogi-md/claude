"""
WooCommerce integration module
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from requests.auth import HTTPBasicAuth


class WooCommerceIntegration:
    """
    WooCommerce REST API integration

    Features:
    - REST API authentication
    - Order sync with UTM tracking
    - Customer sync
    - Product sync
    - Webhook support
    """

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        """
        Initialize WooCommerce integration

        Args:
            store_url: WooCommerce store URL (e.g., 'https://mystore.com')
            consumer_key: WooCommerce API consumer key
            consumer_secret: WooCommerce API consumer secret
        """
        self.store_url = store_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = "wc/v3"
        self.base_url = f"{self.store_url}/wp-json/{self.api_version}"
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to WooCommerce API"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, auth=self.auth, **kwargs)
        response.raise_for_status()

        return response.json()

    def get_orders(
        self,
        since_date: Optional[datetime] = None,
        per_page: int = 100,
        status: str = "any"
    ) -> List[Dict[str, Any]]:
        """
        Fetch orders from WooCommerce

        Args:
            since_date: Fetch orders created after this date
            per_page: Number of orders per page (max 100)
            status: Order status filter

        Returns:
            List of orders
        """
        params = {
            "per_page": min(per_page, 100),
            "status": status,
            "orderby": "date",
            "order": "desc"
        }

        if since_date:
            params["after"] = since_date.isoformat()

        all_orders = []
        page = 1

        while True:
            params["page"] = page
            orders = self._make_request("GET", "orders", params=params)

            if not orders:
                break

            all_orders.extend(orders)

            # WooCommerce returns empty array when no more pages
            if len(orders) < per_page:
                break

            page += 1

        return all_orders

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get single order by ID"""
        return self._make_request("GET", f"orders/{order_id}")

    def get_customers(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch customers from WooCommerce"""
        params = {"per_page": 100}

        if since_date:
            params["after"] = since_date.isoformat()

        all_customers = []
        page = 1

        while True:
            params["page"] = page
            customers = self._make_request("GET", "customers", params=params)

            if not customers:
                break

            all_customers.extend(customers)

            if len(customers) < 100:
                break

            page += 1

        return all_customers

    def get_products(self) -> List[Dict[str, Any]]:
        """Fetch products from WooCommerce"""
        params = {"per_page": 100}
        all_products = []
        page = 1

        while True:
            params["page"] = page
            products = self._make_request("GET", "products", params=params)

            if not products:
                break

            all_products.extend(products)

            if len(products) < 100:
                break

            page += 1

        return all_products

    def sync_orders_to_db(self, db, store_id: int, since_date: Optional[datetime] = None):
        """
        Sync WooCommerce orders to database

        Args:
            db: Database session
            store_id: Store ID in our database
            since_date: Sync orders from this date
        """
        from app.models import Order, Customer

        wc_orders = self.get_orders(since_date=since_date)

        for wc_order in wc_orders:
            # Check if order already exists
            existing = db.query(Order).filter(
                Order.platform == "woocommerce",
                Order.platform_order_id == str(wc_order["id"])
            ).first()

            if existing:
                continue

            # Extract customer data
            customer = None
            billing = wc_order.get("billing", {})
            customer_email = billing.get("email")

            if customer_email:
                customer = db.query(Customer).filter(
                    Customer.store_id == store_id,
                    Customer.email == customer_email
                ).first()

                if not customer:
                    customer = Customer(
                        store_id=store_id,
                        email=customer_email,
                        first_name=billing.get("first_name"),
                        last_name=billing.get("last_name"),
                        phone=billing.get("phone"),
                        woocommerce_customer_id=str(wc_order.get("customer_id", 0)),
                        city=billing.get("city"),
                        state=billing.get("state"),
                        country=billing.get("country"),
                        postal_code=billing.get("postcode")
                    )
                    db.add(customer)
                    db.flush()

            # Extract UTM from meta data
            utm_source = None
            utm_medium = None
            utm_campaign = None

            for meta in wc_order.get("meta_data", []):
                key = meta.get("key", "")
                value = meta.get("value", "")

                if key == "_utm_source" or key == "utm_source":
                    utm_source = value
                elif key == "_utm_medium" or key == "utm_medium":
                    utm_medium = value
                elif key == "_utm_campaign" or key == "utm_campaign":
                    utm_campaign = value

            # Determine attributed channel
            attributed_channel = self._determine_channel(utm_source, utm_medium)

            # Calculate totals
            subtotal = float(wc_order.get("total", 0))
            tax = float(wc_order.get("total_tax", 0))
            shipping = float(wc_order.get("shipping_total", 0))
            discount = float(wc_order.get("discount_total", 0))

            # Create order
            order = Order(
                store_id=store_id,
                customer_id=customer.id if customer else None,
                platform="woocommerce",
                platform_order_id=str(wc_order["id"]),
                order_number=wc_order.get("number"),
                subtotal=subtotal - tax - shipping,
                tax=tax,
                shipping_cost=shipping,
                discount=discount,
                total=subtotal,
                currency=wc_order.get("currency"),
                line_items=[{
                    "product_id": item.get("product_id"),
                    "variant_id": item.get("variation_id"),
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "price": item.get("price"),
                    "total": item.get("total")
                } for item in wc_order.get("line_items", [])],
                item_count=sum(item.get("quantity", 0) for item in wc_order.get("line_items", [])),
                financial_status=wc_order.get("status"),
                fulfillment_status=wc_order.get("status"),
                customer_email=customer_email,
                shipping_address=wc_order.get("shipping"),
                billing_address=billing,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                attributed_channel=attributed_channel,
                order_date=datetime.fromisoformat(wc_order["date_created"].replace("Z", "+00:00"))
            )

            db.add(order)

        db.commit()
        return len(wc_orders)

    def _determine_channel(self, utm_source: str, utm_medium: str) -> str:
        """Determine marketing channel from UTM data"""
        if utm_source:
            utm_source_lower = utm_source.lower()
            if "facebook" in utm_source_lower or "fb" in utm_source_lower or "instagram" in utm_source_lower:
                return "facebook"
            elif "google" in utm_source_lower:
                return "google"
            elif "email" in utm_source_lower:
                return "email"
            elif "whatsapp" in utm_source_lower:
                return "whatsapp"

        return "direct"

    def create_webhook(self, topic: str, delivery_url: str) -> Dict[str, Any]:
        """
        Create webhook subscription

        Args:
            topic: Webhook topic (e.g., 'order.created', 'order.updated')
            delivery_url: Callback URL

        Returns:
            Webhook details
        """
        data = {
            "name": f"Order {topic}",
            "topic": topic,
            "delivery_url": delivery_url
        }

        return self._make_request("POST", "webhooks", json=data)

    @staticmethod
    def verify_webhook(payload: str, signature: str, secret: str) -> bool:
        """
        Verify WooCommerce webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib
        import base64

        computed_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(computed_signature, signature)
