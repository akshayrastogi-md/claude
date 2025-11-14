"""
Production configuration and settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Production-ready application settings"""

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "D2C Analytics & Forecasting Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Complete AI-powered analytics platform for D2C brands"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # PostgreSQL Database (Transactional Data)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "d2c_analytics"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB (Analytics, Logs, Cache)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "d2c_analytics"

    # Redis (Session, Cache)
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"  # CHANGE THIS!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    BCRYPT_ROUNDS: int = 12
    RATE_LIMIT_PER_MINUTE: int = 60
    API_KEY_HEADER: str = "X-API-Key"

    # AI/ML Settings
    FORECAST_HORIZON_DAYS: int = 30
    MIN_HISTORICAL_DAYS: int = 30
    CONFIDENCE_INTERVAL: float = 0.95

    # Model Settings
    ENABLE_PROPHET: bool = True
    ENABLE_ARIMA: bool = True
    ENABLE_LSTM: bool = True
    ENABLE_XGBOOST: bool = True

    # Shopify Integration
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_WEBHOOK_SECRET: Optional[str] = None
    SHOPIFY_SCOPES: List[str] = [
        "read_orders",
        "read_products",
        "read_customers",
        "read_inventory"
    ]

    # Facebook Integration
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_SCOPES: List[str] = [
        "ads_read",
        "ads_management",
        "business_management"
    ]

    # Google Ads Integration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_DEVELOPER_TOKEN: Optional[str] = None

    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Workers
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Subscription Plans
    FREE_TIER_ORDER_LIMIT: int = 100
    STARTER_TIER_ORDER_LIMIT: int = 1000
    PRO_TIER_ORDER_LIMIT: int = 10000

    # Feature Flags
    ENABLE_WEBHOOKS: bool = True
    ENABLE_ANALYTICS_CACHE: bool = True
    ENABLE_FORECAST_CACHE: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
