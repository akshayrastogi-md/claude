"""
D2C Analytics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_active_store
from app.services.d2c_analytics import D2CAnalyticsService

router = APIRouter(prefix="/d2c", tags=["D2C Analytics"])


@router.get("/dashboard")
async def get_d2c_dashboard(
    start_date: Optional[datetime] = Query(None, description="Start date (default: 30 days ago)"),
    end_date: Optional[datetime] = Query(None, description="End date (default: now)"),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive D2C dashboard metrics

    Returns:
        - Revenue metrics with growth
        - Customer LTV and CAC
        - Marketing ROAS by channel
        - Shipping performance
        - Multi-channel attribution
        - Top products
        - Cohort analysis
        - AI-generated insights
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    try:
        service = D2CAnalyticsService(db, store_id)
        dashboard = service.get_dashboard_metrics(start_date, end_date)

        return {
            "success": True,
            "data": dashboard,
            "period": {
                "start": start_date,
                "end": end_date,
                "days": (end_date - start_date).days
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")


@router.get("/revenue")
async def get_revenue_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get detailed revenue metrics"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    metrics = service.get_revenue_metrics(start_date, end_date)

    return {"success": True, "data": metrics}


@router.get("/customers")
async def get_customer_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get customer analytics including LTV and CAC"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    metrics = service.get_customer_metrics(start_date, end_date)

    return {"success": True, "data": metrics}


@router.get("/marketing")
async def get_marketing_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get marketing performance across all channels"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    metrics = service.get_marketing_metrics(start_date, end_date)

    return {"success": True, "data": metrics}


@router.get("/shipping")
async def get_shipping_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get shipping and logistics performance"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    metrics = service.get_shipping_metrics(start_date, end_date)

    return {"success": True, "data": metrics}


@router.get("/attribution")
async def get_channel_attribution(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get multi-channel attribution analysis"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    attribution = service.get_channel_attribution(start_date, end_date)

    return {"success": True, "data": attribution}


@router.get("/cohorts")
async def get_cohort_analysis(
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get customer cohort retention analysis"""
    service = D2CAnalyticsService(db, store_id)
    cohorts = service.get_cohort_retention()

    return {"success": True, "data": cohorts}


@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: int = Depends(get_current_active_store),
    db: Session = Depends(get_db)
):
    """Get top selling products"""
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = D2CAnalyticsService(db, store_id)
    products = service.get_top_products(start_date, end_date, limit)

    return {"success": True, "data": products}
