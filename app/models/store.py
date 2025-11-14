"""
Store/Tenant model for multi-tenant SaaS
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Store(Base):
    """Store/Tenant model - each D2C brand is a store"""

    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)

    # Store details
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)

    # Subscription
    plan = Column(String(50), default="free")  # free, starter, pro, enterprise
    is_active = Column(Boolean, default=True)

    # Store settings
    currency = Column(String(10), default="USD")
    timezone = Column(String(50), default="UTC")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    integrations = relationship("Integration", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="store", cascade="all, delete-orphan")
    marketing_campaigns = relationship("MarketingCampaign", back_populates="store", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="store", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Store(name={self.name}, domain={self.domain})>"


class Integration(Base):
    """Integration model - tracks connected platforms"""

    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)

    # Integration details
    platform = Column(String(50), nullable=False)  # shopify, woocommerce, facebook, google, etc.
    status = Column(String(20), default="active")  # active, inactive, error

    # OAuth tokens and credentials (encrypted in production)
    access_token = Column(String(500), nullable=True)
    refresh_token = Column(String(500), nullable=True)
    shop_url = Column(String(255), nullable=True)

    # Platform-specific data
    platform_data = Column(JSON, nullable=True)  # Store platform-specific config

    # Sync status
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="pending")  # pending, syncing, completed, error

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="integrations")

    def __repr__(self):
        return f"<Integration(platform={self.platform}, store_id={self.store_id})>"
