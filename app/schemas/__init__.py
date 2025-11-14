"""
Pydantic schemas for request/response validation
"""
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.inventory import InventoryRecordCreate, InventoryRecordResponse
from app.schemas.sales import SalesRecordCreate, SalesRecordResponse
from app.schemas.forecast import ForecastRequest, ForecastResponse, ForecastResultResponse
from app.schemas.analytics import AnalyticsResponse, SalesMetrics, InventoryMetrics

__all__ = [
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "InventoryRecordCreate",
    "InventoryRecordResponse",
    "SalesRecordCreate",
    "SalesRecordResponse",
    "ForecastRequest",
    "ForecastResponse",
    "ForecastResultResponse",
    "AnalyticsResponse",
    "SalesMetrics",
    "InventoryMetrics",
]
