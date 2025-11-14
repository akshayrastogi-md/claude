"""
Analytics schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SalesMetrics(BaseModel):
    """Sales metrics"""

    total_revenue: float = Field(..., description="Total revenue")
    total_units_sold: int = Field(..., description="Total units sold")
    average_order_value: float = Field(..., description="Average order value")
    total_orders: int = Field(..., description="Total number of orders")
    return_rate: float = Field(..., description="Return rate percentage")
    revenue_growth_rate: Optional[float] = Field(None, description="Revenue growth rate")


class InventoryMetrics(BaseModel):
    """Inventory metrics"""

    total_products: int = Field(..., description="Total number of products")
    total_stock_value: float = Field(..., description="Total stock value")
    out_of_stock_count: int = Field(..., description="Number of out-of-stock products")
    low_stock_count: int = Field(..., description="Number of low-stock products")
    average_stock_level: float = Field(..., description="Average stock level")
    inventory_turnover_ratio: Optional[float] = Field(None, description="Inventory turnover ratio")


class ProductPerformance(BaseModel):
    """Product performance metrics"""

    product_id: int
    sku: str
    name: str
    total_sales: int
    total_revenue: float
    average_daily_sales: float
    stock_level: int
    days_of_supply: Optional[float]


class CategoryPerformance(BaseModel):
    """Category performance metrics"""

    category: str
    total_products: int
    total_revenue: float
    total_units_sold: int
    market_share_percentage: float


class TimeSeriesMetric(BaseModel):
    """Time series metric point"""

    date: datetime
    value: float
    metric_name: str


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response"""

    period_start: datetime = Field(..., description="Analysis period start date")
    period_end: datetime = Field(..., description="Analysis period end date")
    sales_metrics: SalesMetrics
    inventory_metrics: InventoryMetrics
    top_products: List[ProductPerformance] = Field(..., description="Top performing products")
    category_performance: List[CategoryPerformance] = Field(..., description="Category performance")
    time_series_data: Optional[List[TimeSeriesMetric]] = Field(None, description="Time series trends")
    insights: Optional[List[str]] = Field(None, description="AI-generated insights")
