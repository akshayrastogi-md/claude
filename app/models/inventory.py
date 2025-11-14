"""
Inventory model
"""
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class InventoryRecord(Base):
    """Inventory record model for tracking stock levels"""

    __tablename__ = "inventory_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Stock information
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)

    # Location
    warehouse_id = Column(String(50), nullable=True, index=True)
    location = Column(String(100), nullable=True)

    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(String(500), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="inventory_records")

    def __repr__(self):
        return f"<InventoryRecord(product_id={self.product_id}, quantity={self.quantity_on_hand})>"
