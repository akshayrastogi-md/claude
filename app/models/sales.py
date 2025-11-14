"""
Sales model
"""
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SalesRecord(Base):
    """Sales record model for tracking product sales"""

    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Sale information
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_revenue = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)

    # Order information
    order_id = Column(String(100), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True, index=True)

    # Channel and location
    sales_channel = Column(String(50), default="online")  # online, retail, wholesale
    region = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Status
    is_returned = Column(Boolean, default=False)
    return_date = Column(DateTime, nullable=True)

    # Metadata
    sale_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="sales_records")

    def __repr__(self):
        return f"<SalesRecord(product_id={self.product_id}, quantity={self.quantity_sold}, date={self.sale_date})>"
