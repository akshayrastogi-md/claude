"""
Application configuration and settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Inventory Forecasting & Analytics"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Complete AI-powered inventory forecasting and ecommerce analytics service"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    # Database
    DATABASE_URL: str = "sqlite:///./inventory_forecast.db"

    # AI/ML Settings
    FORECAST_HORIZON_DAYS: int = 30
    MIN_HISTORICAL_DAYS: int = 30
    CONFIDENCE_INTERVAL: float = 0.95

    # Model Settings
    ENABLE_PROPHET: bool = True
    ENABLE_ARIMA: bool = True
    ENABLE_LSTM: bool = True
    ENABLE_XGBOOST: bool = True

    # Cache Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
