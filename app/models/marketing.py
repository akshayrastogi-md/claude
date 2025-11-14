"""
Marketing campaign model for multi-channel tracking
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class MarketingCampaign(Base):
    """Marketing campaign model - tracks campaigns across all channels"""

    __tablename__ = "marketing_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)

    # Campaign details
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)  # facebook, google, email, whatsapp
    campaign_type = Column(String(50), nullable=True)  # awareness, conversion, retargeting

    # External IDs
    platform_campaign_id = Column(String(100), nullable=True, index=True)

    # Budget and spend
    budget = Column(Float, nullable=True)
    spent = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")

    # Performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    # Calculated metrics
    ctr = Column(Float, default=0.0)  # Click-through rate
    cpc = Column(Float, default=0.0)  # Cost per click
    cpa = Column(Float, default=0.0)  # Cost per acquisition
    roas = Column(Float, default=0.0)  # Return on ad spend

    # Status
    status = Column(String(20), default="active")  # active, paused, completed

    # Dates
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Campaign configuration
    targeting = Column(JSON, nullable=True)
    creative_assets = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)

    # Relationships
    store = relationship("Store", back_populates="marketing_campaigns")
    orders = relationship("Order", back_populates="campaign")

    def __repr__(self):
        return f"<MarketingCampaign(name={self.name}, channel={self.channel}, roas={self.roas})>"
