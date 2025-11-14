"""
Inventory schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InventoryRecordBase(BaseModel):
    """Base inventory record schema"""

    product_id: int = Field(..., description="Product ID")
    quantity_on_hand: int = Field(..., ge=0, description="Quantity on hand")
    quantity_reserved: int = Field(0, ge=0, description="Quantity reserved")
    quantity_available: int = Field(0, ge=0, description="Quantity available")
    warehouse_id: Optional[str] = Field(None, description="Warehouse ID")
    location: Optional[str] = Field(None, description="Storage location")
    notes: Optional[str] = Field(None, max_length=500, description="Notes")


class InventoryRecordCreate(InventoryRecordBase):
    """Schema for creating an inventory record"""
    pass


class InventoryRecordResponse(InventoryRecordBase):
    """Schema for inventory record response"""

    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True
