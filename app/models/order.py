"""
Order model - unified orders from all platforms
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Order(Base):
    """Order model - unified order data from Shopify, WooCommerce, etc."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

    # External order IDs
    platform = Column(String(50), nullable=False)  # shopify, woocommerce
    platform_order_id = Column(String(100), nullable=False, index=True)
    order_number = Column(String(100), nullable=True)

    # Financial
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")

    # Order details
    line_items = Column(JSON, nullable=True)  # Array of products
    item_count = Column(Integer, default=0)

    # Status
    financial_status = Column(String(50), nullable=True)  # paid, pending, refunded
    fulfillment_status = Column(String(50), nullable=True)  # fulfilled, partial, unfulfilled

    # Customer info snapshot
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)

    # Shipping address
    shipping_address = Column(JSON, nullable=True)
    billing_address = Column(JSON, nullable=True)

    # Attribution - which channel brought this order
    utm_source = Column(String(100), nullable=True, index=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    referrer = Column(String(255), nullable=True)
    landing_page = Column(String(255), nullable=True)

    # Channel attribution
    attributed_channel = Column(String(50), nullable=True)  # facebook, google, email, organic, direct
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=True)

    # Dates
    order_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    campaign = relationship("MarketingCampaign", back_populates="orders")
    shipment = relationship("Shipment", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order(platform={self.platform}, order_id={self.platform_order_id}, total={self.total})>"
