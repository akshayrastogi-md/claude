"""
Shipment model for logistics analytics
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Shipment(Base):
    """Shipment model - tracks shipping via Shiprocket and other carriers"""

    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    # Shiprocket details
    shiprocket_order_id = Column(String(100), nullable=True, index=True)
    shiprocket_shipment_id = Column(String(100), nullable=True, index=True)
    awb_code = Column(String(100), nullable=True)  # Air Waybill tracking number

    # Carrier details
    courier_name = Column(String(100), nullable=True)
    courier_id = Column(String(100), nullable=True)

    # Shipping details
    weight = Column(Float, nullable=True)  # in kg
    dimensions = Column(JSON, nullable=True)  # length, width, height

    # Costs
    shipping_charges = Column(Float, default=0.0)
    cod_charges = Column(Float, default=0.0)  # Cash on Delivery charges
    total_cost = Column(Float, default=0.0)

    # Pickup and delivery
    pickup_scheduled_date = Column(DateTime, nullable=True)
    pickup_date = Column(DateTime, nullable=True)
    expected_delivery_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String(50), default="pending")  # pending, picked_up, in_transit, delivered, rto, cancelled
    current_status = Column(String(100), nullable=True)

    # Delivery metrics
    delivery_days = Column(Integer, nullable=True)
    is_delivered = Column(Boolean, default=False)
    is_rto = Column(Boolean, default=False)  # Return to Origin

    # Location
    origin_city = Column(String(100), nullable=True)
    destination_city = Column(String(100), nullable=True)
    destination_state = Column(String(100), nullable=True)
    destination_pincode = Column(String(20), nullable=True)

    # Tracking history
    tracking_data = Column(JSON, nullable=True)  # Array of tracking updates

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    store = relationship("Store", back_populates="shipments")
    order = relationship("Order", back_populates="shipment")

    def __repr__(self):
        return f"<Shipment(awb={self.awb_code}, status={self.status}, courier={self.courier_name})>"
