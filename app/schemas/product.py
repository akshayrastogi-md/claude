"""
Product schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema"""

    sku: str = Field(..., description="Product SKU (Stock Keeping Unit)")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    sub_category: Optional[str] = Field(None, description="Product sub-category")
    brand: Optional[str] = Field(None, description="Product brand")
    unit_price: float = Field(..., gt=0, description="Unit price")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price")
    reorder_point: int = Field(10, ge=0, description="Reorder point threshold")
    reorder_quantity: int = Field(100, ge=0, description="Reorder quantity")
    safety_stock: int = Field(5, ge=0, description="Safety stock level")
    weight: Optional[float] = Field(None, ge=0, description="Product weight")
    dimensions: Optional[str] = Field(None, description="Product dimensions")
    is_active: bool = Field(True, description="Is product active")
    is_seasonal: bool = Field(False, description="Is product seasonal")


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    unit_price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[str] = None
    is_active: Optional[bool] = None
    is_seasonal: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
