"""
Sales schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SalesRecordBase(BaseModel):
    """Base sales record schema"""

    product_id: int = Field(..., description="Product ID")
    quantity_sold: int = Field(..., gt=0, description="Quantity sold")
    unit_price: float = Field(..., gt=0, description="Unit price at time of sale")
    total_revenue: float = Field(..., ge=0, description="Total revenue")
    discount_amount: float = Field(0.0, ge=0, description="Discount amount")
    order_id: Optional[str] = Field(None, description="Order ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    sales_channel: str = Field("online", description="Sales channel (online, retail, wholesale)")
    region: Optional[str] = Field(None, description="Region")
    country: Optional[str] = Field(None, description="Country")
    is_returned: bool = Field(False, description="Is order returned")
    return_date: Optional[datetime] = Field(None, description="Return date if returned")
    sale_date: datetime = Field(..., description="Sale date")


class SalesRecordCreate(SalesRecordBase):
    """Schema for creating a sales record"""
    pass


class SalesRecordResponse(SalesRecordBase):
    """Schema for sales record response"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
