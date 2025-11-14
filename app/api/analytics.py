"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/comprehensive", response_model=AnalyticsResponse)
def get_comprehensive_analytics(
    start_date: datetime = Query(None, description="Start date for analysis (default: 30 days ago)"),
    end_date: datetime = Query(None, description="End date for analysis (default: now)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive ecommerce analytics

    Includes sales metrics, inventory metrics, top products, category performance,
    time series data, and AI-generated insights.
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.utcnow()

    if not start_date:
        start_date = end_date - timedelta(days=30)

    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )

    try:
        service = AnalyticsService(db)
        analytics = service.get_comprehensive_analytics(start_date, end_date)

        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics generation failed: {str(e)}"
        )


@router.get("/sales-metrics")
def get_sales_metrics(
    start_date: datetime = Query(None, description="Start date"),
    end_date: datetime = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Get sales metrics for a specific period"""

    if not end_date:
        end_date = datetime.utcnow()

    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = AnalyticsService(db)
    metrics = service.get_sales_metrics(start_date, end_date)

    return metrics


@router.get("/inventory-metrics")
def get_inventory_metrics(db: Session = Depends(get_db)):
    """Get current inventory metrics"""

    service = AnalyticsService(db)
    metrics = service.get_inventory_metrics()

    return metrics


@router.get("/top-products")
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top products"),
    start_date: datetime = Query(None, description="Start date"),
    end_date: datetime = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Get top performing products"""

    if not end_date:
        end_date = datetime.utcnow()

    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = AnalyticsService(db)
    top_products = service.get_top_products(start_date, end_date, limit)

    return {"products": top_products}


@router.get("/category-performance")
def get_category_performance(
    start_date: datetime = Query(None, description="Start date"),
    end_date: datetime = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Get performance metrics by category"""

    if not end_date:
        end_date = datetime.utcnow()

    if not start_date:
        start_date = end_date - timedelta(days=30)

    service = AnalyticsService(db)
    performance = service.get_category_performance(start_date, end_date)

    return {"categories": performance}


@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get quick dashboard summary with key metrics

    Optimized for dashboard displays with the most important KPIs.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    service = AnalyticsService(db)

    sales_metrics = service.get_sales_metrics(start_date, end_date)
    inventory_metrics = service.get_inventory_metrics()
    top_products = service.get_top_products(start_date, end_date, limit=5)

    return {
        "period": {
            "start": start_date,
            "end": end_date,
            "days": 30
        },
        "sales": {
            "total_revenue": sales_metrics.total_revenue,
            "total_orders": sales_metrics.total_orders,
            "average_order_value": sales_metrics.average_order_value,
            "growth_rate": sales_metrics.revenue_growth_rate
        },
        "inventory": {
            "total_products": inventory_metrics.total_products,
            "stock_value": inventory_metrics.total_stock_value,
            "out_of_stock": inventory_metrics.out_of_stock_count,
            "low_stock": inventory_metrics.low_stock_count
        },
        "top_products": [
            {
                "name": p.name,
                "sku": p.sku,
                "revenue": p.total_revenue,
                "sales": p.total_sales
            }
            for p in top_products
        ]
    }
