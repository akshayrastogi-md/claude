"""
MongoDB connection and configuration
For analytics, logs, and time-series data
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Async MongoDB client for FastAPI
_async_mongo_client: Optional[AsyncIOMotorClient] = None

# Sync MongoDB client for background tasks
_sync_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Get async MongoDB client"""
    global _async_mongo_client

    if _async_mongo_client is None:
        _async_mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        logger.info("MongoDB async client initialized")

    return _async_mongo_client


def get_sync_mongo_client() -> MongoClient:
    """Get sync MongoDB client for background tasks"""
    global _sync_mongo_client

    if _sync_mongo_client is None:
        _sync_mongo_client = MongoClient(settings.MONGODB_URL)
        logger.info("MongoDB sync client initialized")

    return _sync_mongo_client


async def get_mongo_database():
    """Get MongoDB database for FastAPI dependency injection"""
    client = get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


async def close_mongo_connection():
    """Close MongoDB connection"""
    global _async_mongo_client, _sync_mongo_client

    if _async_mongo_client:
        _async_mongo_client.close()
        _async_mongo_client = None
        logger.info("MongoDB async client closed")

    if _sync_mongo_client:
        _sync_mongo_client.close()
        _sync_mongo_client = None
        logger.info("MongoDB sync client closed")


class MongoCollections:
    """MongoDB collection names"""

    # Analytics collections
    ANALYTICS_EVENTS = "analytics_events"
    USER_SESSIONS = "user_sessions"
    API_LOGS = "api_logs"

    # Time-series data
    METRICS_TIMESERIES = "metrics_timeseries"
    CAMPAIGN_PERFORMANCE = "campaign_performance"

    # Audit logs
    AUDIT_LOGS = "audit_logs"
    INTEGRATION_LOGS = "integration_logs"

    # Cache
    FORECAST_CACHE = "forecast_cache"
    ANALYTICS_CACHE = "analytics_cache"


async def init_mongodb():
    """Initialize MongoDB indexes and collections"""
    try:
        db = await get_mongo_database()

        # Create indexes for analytics events
        await db[MongoCollections.ANALYTICS_EVENTS].create_index([("store_id", 1), ("timestamp", -1)])
        await db[MongoCollections.ANALYTICS_EVENTS].create_index([("event_type", 1)])

        # Create indexes for API logs
        await db[MongoCollections.API_LOGS].create_index([("timestamp", -1)])
        await db[MongoCollections.API_LOGS].create_index([("store_id", 1), ("timestamp", -1)])
        await db[MongoCollections.API_LOGS].create_index([("endpoint", 1)])

        # Create TTL index for cache (expire after 1 hour)
        await db[MongoCollections.FORECAST_CACHE].create_index(
            [("created_at", 1)],
            expireAfterSeconds=3600
        )
        await db[MongoCollections.ANALYTICS_CACHE].create_index(
            [("created_at", 1)],
            expireAfterSeconds=3600
        )

        # Create indexes for audit logs
        await db[MongoCollections.AUDIT_LOGS].create_index([("store_id", 1), ("timestamp", -1)])
        await db[MongoCollections.AUDIT_LOGS].create_index([("user_id", 1), ("timestamp", -1)])

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise
