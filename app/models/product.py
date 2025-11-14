"""
Product model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Product(Base):
    """Product model for storing product information"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True)
    sub_category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)

    # Pricing
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=True)

    # Inventory thresholds
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=100)
    safety_stock = Column(Integer, default=5)

    # Product attributes
    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_seasonal = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inventory_records = relationship("InventoryRecord", back_populates="product", cascade="all, delete-orphan")
    sales_records = relationship("SalesRecord", back_populates="product", cascade="all, delete-orphan")
    forecast_results = relationship("ForecastResult", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(sku={self.sku}, name={self.name})>"
