"""
Forecast schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Available forecasting models"""
    PROPHET = "prophet"
    ARIMA = "arima"
    LSTM = "lstm"
    XGBOOST = "xgboost"
    ENSEMBLE = "ensemble"


class ForecastRequest(BaseModel):
    """Schema for forecast request"""

    product_id: int = Field(..., description="Product ID to forecast")
    forecast_horizon_days: int = Field(30, ge=1, le=365, description="Number of days to forecast")
    model_type: Optional[ModelType] = Field(None, description="Model type (default: auto-select best)")
    confidence_interval: float = Field(0.95, ge=0.5, le=0.99, description="Confidence interval")
    include_historical: bool = Field(True, description="Include historical data in response")


class ForecastPoint(BaseModel):
    """Single forecast point"""

    date: datetime = Field(..., description="Forecast date")
    predicted_demand: float = Field(..., description="Predicted demand")
    lower_bound: Optional[float] = Field(None, description="Lower confidence bound")
    upper_bound: Optional[float] = Field(None, description="Upper confidence bound")


class ForecastResponse(BaseModel):
    """Schema for forecast response"""

    product_id: int
    product_sku: str
    product_name: str
    model_type: str
    forecast_horizon_days: int
    confidence_interval: float
    forecasts: List[ForecastPoint]
    model_metrics: Optional[Dict[str, Any]] = Field(None, description="Model performance metrics")
    recommendations: Optional[Dict[str, Any]] = Field(None, description="Inventory recommendations")
    historical_data: Optional[List[Dict[str, Any]]] = Field(None, description="Historical sales data")


class ForecastResultResponse(BaseModel):
    """Schema for stored forecast result"""

    id: int
    product_id: int
    forecast_date: datetime
    predicted_demand: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    confidence_interval: float
    model_type: str
    accuracy_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
