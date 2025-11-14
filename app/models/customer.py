"""
Customer model for D2C analytics
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Customer(Base):
    """Customer model - unified customer data across platforms"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)

    # Customer details
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # External IDs from platforms
    shopify_customer_id = Column(String(100), nullable=True, index=True)
    woocommerce_customer_id = Column(String(100), nullable=True, index=True)

    # Location
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Customer metrics
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    average_order_value = Column(Float, default=0.0)
    lifetime_value = Column(Float, default=0.0)

    # Segmentation
    customer_segment = Column(String(50), nullable=True)  # vip, loyal, at_risk, new, etc.
    rfm_score = Column(String(10), nullable=True)  # RFM analysis score

    # Engagement
    first_order_date = Column(DateTime, nullable=True)
    last_order_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Marketing preferences
    accepts_marketing = Column(Boolean, default=False)
    marketing_channels = Column(JSON, nullable=True)  # Channels customer came from

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(email={self.email}, ltv={self.lifetime_value})>"
