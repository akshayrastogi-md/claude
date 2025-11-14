"""
Production-ready FastAPI application for D2C Analytics & Forecasting Platform
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration

from app.core.config import settings
from app.core.database import init_db
from app.core.mongodb import init_mongodb, close_mongo_connection
from app.core.logging import logger
from app.api import (
    products, inventory, sales, forecast, analytics,
    d2c_analytics, integrations, webhooks
)

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastAPIIntegration()],
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
    )

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler

    Startup:
    - Initialize PostgreSQL database
    - Initialize MongoDB
    - Set up indexes
    - Load configurations

    Shutdown:
    - Close database connections
    - Clean up resources
    """
    # Startup
    logger.info(f"🚀 Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    try:
        # Initialize PostgreSQL
        init_db()
        logger.info("✅ PostgreSQL initialized")

        # Initialize MongoDB
        await init_mongodb()
        logger.info("✅ MongoDB initialized")

        logger.info(f"📊 AI Models enabled: Prophet, ARIMA, LSTM, XGBoost")
        logger.info(f"🔗 Integrations: Shopify, WooCommerce, Facebook, Google, Shiprocket")
        logger.info(f"🌍 Server ready at http://localhost:8000")

    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("👋 Shutting down...")
    await close_mongo_connection()
    logger.info("✅ Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request ID and processing time to response headers"""
    import uuid

    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    response = await call_next(request)

    # Add headers
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    # Log request
    logger.info(
        "API Request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
        request_id=request_id
    )

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers"""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "validation_error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    logger.error(f"Value error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "bad_request",
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "internal_server_error",
                "detail": str(exc)
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "internal_server_error",
                "detail": "An internal error occurred. Please try again later."
            }
        )


# Root endpoint
@app.get("/", tags=["Health"])
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "docs": "/docs" if settings.DEBUG else "disabled",
            "redoc": "/redoc" if settings.DEBUG else "disabled",
            "health": "/health",
            "api": settings.API_V1_STR
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with database connectivity"""
    from app.core.database import SessionLocal
    from app.core.mongodb import get_mongo_database

    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {}
    }

    # Check PostgreSQL
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["postgresql"] = "healthy"
    except Exception as e:
        health_status["components"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check MongoDB
    try:
        mongo_db = await get_mongo_database()
        await mongo_db.command("ping")
        health_status["components"]["mongodb"] = "healthy"
    except Exception as e:
        health_status["components"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # AI Models
    health_status["components"]["ai_models"] = {
        "prophet": settings.ENABLE_PROPHET,
        "arima": settings.ENABLE_ARIMA,
        "lstm": settings.ENABLE_LSTM,
        "xgboost": settings.ENABLE_XGBOOST
    }

    return health_status


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include API routers
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(inventory.router, prefix=settings.API_V1_STR)
app.include_router(sales.router, prefix=settings.API_V1_STR)
app.include_router(forecast.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

# D2C-specific endpoints
app.include_router(d2c_analytics.router, prefix=settings.API_V1_STR)
app.include_router(integrations.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
