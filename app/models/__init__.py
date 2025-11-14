"""
Updated database models for SaaS platform
"""
from app.models.store import Store, Integration
from app.models.customer import Customer
from app.models.order import Order
from app.models.marketing import MarketingCampaign
from app.models.shipment import Shipment

# Keep forecast model for demand forecasting
from app.models.forecast import ForecastResult

__all__ = [
    "Store",
    "Integration",
    "Customer",
    "Order",
    "MarketingCampaign",
    "Shipment",
    "ForecastResult"
]
