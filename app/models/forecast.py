"""
Forecast result model
"""
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ForecastResult(Base):
    """Forecast result model for storing prediction results"""

    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Forecast information
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_demand = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    confidence_interval = Column(Float, default=0.95)

    # Model information
    model_type = Column(String(50), nullable=False)  # prophet, arima, lstm, xgboost
    model_version = Column(String(50), nullable=True)
    accuracy_score = Column(Float, nullable=True)

    # Metadata
    forecast_horizon_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional model metrics
    model_metrics = Column(JSON, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="forecast_results")

    def __repr__(self):
        return f"<ForecastResult(product_id={self.product_id}, model={self.model_type}, date={self.forecast_date})>"
