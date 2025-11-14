"""
Shiprocket integration for shipping analytics
"""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class ShiprocketIntegration:
    """
    Shiprocket API integration for shipping management

    Features:
    - Shipment tracking
    - Delivery performance metrics
    - RTO (Return to Origin) tracking
    - Courier performance analytics
    - COD reconciliation
    - Shipping cost analysis
    """

    def __init__(self, email: str, password: str):
        """
        Initialize Shiprocket integration

        Args:
            email: Shiprocket account email
            password: Shiprocket account password
        """
        self.email = email
        self.password = password
        self.base_url = "https://apiv2.shiprocket.in/v1/external"
        self.token = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Shiprocket and get token"""
        url = f"{self.base_url}/auth/login"
        data = {
            "email": self.email,
            "password": self.password
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        self.token = response.json().get("token")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Shiprocket API"""
        if not self.token:
            self._authenticate()

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)

        # Re-authenticate if token expired
        if response.status_code == 401:
            self._authenticate()
            headers["Authorization"] = f"Bearer {self.token}"
            response = requests.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()
        return response.json()

    def get_shipments(
        self,
        page: int = 1,
        per_page: int = 50,
        filter_by_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get shipments from Shiprocket

        Args:
            page: Page number
            per_page: Items per page
            filter_by_date: Filter shipments from this date

        Returns:
            Shipments data
        """
        params = {
            "page": page,
            "per_page": per_page
        }

        if filter_by_date:
            params["filter_by_date"] = filter_by_date.strftime("%Y-%m-%d")

        response = self._make_request("GET", "shipments", params=params)
        return response

    def track_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Track shipment by ID

        Args:
            shipment_id: Shiprocket shipment ID

        Returns:
            Tracking information
        """
        response = self._make_request("GET", f"courier/track/shipment/{shipment_id}")
        return response

    def track_by_awb(self, awb_code: str) -> Dict[str, Any]:
        """
        Track shipment by AWB (Air Waybill) code

        Args:
            awb_code: AWB tracking number

        Returns:
            Tracking information
        """
        response = self._make_request("GET", f"courier/track/awb/{awb_code}")
        return response

    def sync_shipments_to_db(
        self,
        db,
        store_id: int,
        since_date: Optional[datetime] = None
    ):
        """
        Sync Shiprocket shipments to database

        Args:
            db: Database session
            store_id: Store ID
            since_date: Sync shipments from this date
        """
        from app.models import Shipment, Order

        if not since_date:
            since_date = datetime.now() - timedelta(days=30)

        page = 1
        total_synced = 0

        while True:
            response = self.get_shipments(page=page, filter_by_date=since_date)
            shipments = response.get("data", [])

            if not shipments:
                break

            for sr_shipment in shipments:
                # Find corresponding order
                order_id = sr_shipment.get("order_id")
                order = db.query(Order).filter(
                    Order.store_id == store_id,
                    Order.platform_order_id == str(order_id)
                ).first()

                if not order:
                    continue

                # Check if shipment exists
                existing = db.query(Shipment).filter(
                    Shipment.shiprocket_order_id == str(sr_shipment.get("id"))
                ).first()

                # Extract dates
                pickup_date = None
                delivered_date = None

                if sr_shipment.get("pickup_date"):
                    try:
                        pickup_date = datetime.fromisoformat(sr_shipment["pickup_date"].replace("Z", "+00:00"))
                    except:
                        pass

                if sr_shipment.get("delivered_date"):
                    try:
                        delivered_date = datetime.fromisoformat(sr_shipment["delivered_date"].replace("Z", "+00:00"))
                    except:
                        pass

                # Calculate delivery days
                delivery_days = None
                if pickup_date and delivered_date:
                    delivery_days = (delivered_date - pickup_date).days

                # Check status
                status = sr_shipment.get("status", "").lower()
                is_delivered = status in ["delivered", "delivered-out-for-delivery"]
                is_rto = "rto" in status.lower()

                if existing:
                    # Update existing shipment
                    existing.status = status
                    existing.current_status = sr_shipment.get("current_status")
                    existing.awb_code = sr_shipment.get("awb_code")
                    existing.courier_name = sr_shipment.get("courier_name")
                    existing.pickup_date = pickup_date
                    existing.delivered_date = delivered_date
                    existing.delivery_days = delivery_days
                    existing.is_delivered = is_delivered
                    existing.is_rto = is_rto
                    existing.shipping_charges = float(sr_shipment.get("shipping_charges", 0))
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new shipment
                    shipment = Shipment(
                        store_id=store_id,
                        order_id=order.id,
                        shiprocket_order_id=str(sr_shipment.get("id")),
                        shiprocket_shipment_id=str(sr_shipment.get("shipment_id")),
                        awb_code=sr_shipment.get("awb_code"),
                        courier_name=sr_shipment.get("courier_name"),
                        courier_id=str(sr_shipment.get("courier_id")) if sr_shipment.get("courier_id") else None,
                        weight=float(sr_shipment.get("weight", 0)),
                        dimensions=sr_shipment.get("dimensions"),
                        shipping_charges=float(sr_shipment.get("shipping_charges", 0)),
                        cod_charges=float(sr_shipment.get("cod_charges", 0)),
                        total_cost=float(sr_shipment.get("total", 0)),
                        pickup_date=pickup_date,
                        delivered_date=delivered_date,
                        delivery_days=delivery_days,
                        status=status,
                        current_status=sr_shipment.get("current_status"),
                        is_delivered=is_delivered,
                        is_rto=is_rto,
                        destination_city=sr_shipment.get("customer_city"),
                        destination_state=sr_shipment.get("customer_state"),
                        destination_pincode=sr_shipment.get("customer_pincode")
                    )
                    db.add(shipment)

                total_synced += 1

            # Check if there are more pages
            if len(shipments) < 50:
                break

            page += 1

        db.commit()
        return total_synced

    def get_courier_performance(self) -> List[Dict[str, Any]]:
        """Get courier performance metrics"""
        response = self._make_request("GET", "courier/serviceability")
        return response.get("data", {}).get("available_courier_companies", [])

    def get_ndr_details(self, awb_code: str) -> Dict[str, Any]:
        """
        Get NDR (Non-Delivery Report) details

        Args:
            awb_code: AWB tracking code

        Returns:
            NDR information
        """
        response = self._make_request("GET", f"courier/track/awb/{awb_code}")
        return response.get("tracking_data", {}).get("ndr_status_code", {})

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new shipment order in Shiprocket

        Args:
            order_data: Order details

        Returns:
            Created order information
        """
        response = self._make_request("POST", "orders/create/adhoc", json=order_data)
        return response

    def calculate_shipping_cost(
        self,
        pickup_pincode: str,
        delivery_pincode: str,
        weight: float,
        cod: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate shipping cost

        Args:
            pickup_pincode: Pickup PIN code
            delivery_pincode: Delivery PIN code
            weight: Package weight in kg
            cod: Is Cash on Delivery

        Returns:
            Shipping cost details
        """
        params = {
            "pickup_postcode": pickup_pincode,
            "delivery_postcode": delivery_pincode,
            "weight": weight,
            "cod": 1 if cod else 0
        }

        response = self._make_request("GET", "courier/serviceability", params=params)
        return response.get("data", {})
