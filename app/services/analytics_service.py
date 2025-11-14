"""
Advanced ecommerce analytics service
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Product, SalesRecord, InventoryRecord
from app.schemas.analytics import (
    AnalyticsResponse,
    SalesMetrics,
    InventoryMetrics,
    ProductPerformance,
    CategoryPerformance,
    TimeSeriesMetric
)


class AnalyticsService:
    """Service for advanced ecommerce analytics"""

    def __init__(self, db: Session):
        self.db = db

    def get_comprehensive_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> AnalyticsResponse:
        """
        Generate comprehensive analytics for the specified period

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            AnalyticsResponse with all metrics
        """
        sales_metrics = self.get_sales_metrics(start_date, end_date)
        inventory_metrics = self.get_inventory_metrics()
        top_products = self.get_top_products(start_date, end_date, limit=10)
        category_performance = self.get_category_performance(start_date, end_date)
        time_series_data = self.get_sales_time_series(start_date, end_date)
        insights = self.generate_insights(sales_metrics, inventory_metrics, top_products)

        return AnalyticsResponse(
            period_start=start_date,
            period_end=end_date,
            sales_metrics=sales_metrics,
            inventory_metrics=inventory_metrics,
            top_products=top_products,
            category_performance=category_performance,
            time_series_data=time_series_data,
            insights=insights
        )

    def get_sales_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> SalesMetrics:
        """Calculate sales metrics for the period"""

        # Get sales data
        sales = self.db.query(SalesRecord).filter(
            and_(
                SalesRecord.sale_date >= start_date,
                SalesRecord.sale_date <= end_date
            )
        ).all()

        if not sales:
            return SalesMetrics(
                total_revenue=0.0,
                total_units_sold=0,
                average_order_value=0.0,
                total_orders=0,
                return_rate=0.0,
                revenue_growth_rate=None
            )

        # Calculate metrics
        total_revenue = sum(s.total_revenue - s.discount_amount for s in sales)
        total_units_sold = sum(s.quantity_sold for s in sales)
        unique_orders = len(set(s.order_id for s in sales if s.order_id))
        total_orders = unique_orders if unique_orders > 0 else len(sales)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0

        # Calculate return rate
        returned_sales = sum(1 for s in sales if s.is_returned)
        return_rate = (returned_sales / len(sales) * 100) if len(sales) > 0 else 0.0

        # Calculate growth rate (compare to previous period)
        period_length = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_length)
        previous_end = start_date

        previous_sales = self.db.query(SalesRecord).filter(
            and_(
                SalesRecord.sale_date >= previous_start,
                SalesRecord.sale_date < previous_end
            )
        ).all()

        if previous_sales:
            previous_revenue = sum(s.total_revenue - s.discount_amount for s in previous_sales)
            if previous_revenue > 0:
                revenue_growth_rate = ((total_revenue - previous_revenue) / previous_revenue) * 100
            else:
                revenue_growth_rate = 100.0 if total_revenue > 0 else 0.0
        else:
            revenue_growth_rate = None

        return SalesMetrics(
            total_revenue=float(total_revenue),
            total_units_sold=int(total_units_sold),
            average_order_value=float(average_order_value),
            total_orders=int(total_orders),
            return_rate=float(return_rate),
            revenue_growth_rate=float(revenue_growth_rate) if revenue_growth_rate is not None else None
        )

    def get_inventory_metrics(self) -> InventoryMetrics:
        """Calculate current inventory metrics"""

        # Get latest inventory record for each product
        subquery = self.db.query(
            InventoryRecord.product_id,
            func.max(InventoryRecord.recorded_at).label('max_date')
        ).group_by(InventoryRecord.product_id).subquery()

        latest_inventory = self.db.query(InventoryRecord).join(
            subquery,
            and_(
                InventoryRecord.product_id == subquery.c.product_id,
                InventoryRecord.recorded_at == subquery.c.max_date
            )
        ).all()

        # Get products
        products = self.db.query(Product).all()
        total_products = len(products)

        # Calculate metrics
        total_stock_value = 0.0
        out_of_stock_count = 0
        low_stock_count = 0
        total_stock = 0

        inventory_dict = {inv.product_id: inv for inv in latest_inventory}

        for product in products:
            inv = inventory_dict.get(product.id)

            if inv:
                stock_level = inv.quantity_available
                total_stock += stock_level

                if stock_level == 0:
                    out_of_stock_count += 1
                elif stock_level <= product.reorder_point:
                    low_stock_count += 1

                total_stock_value += stock_level * (product.cost_price or product.unit_price)
            else:
                out_of_stock_count += 1

        average_stock_level = total_stock / total_products if total_products > 0 else 0.0

        # Calculate inventory turnover (simplified)
        # Turnover = COGS / Average Inventory Value
        # Using last 30 days of sales as approximation
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sales = self.db.query(SalesRecord).filter(
            SalesRecord.sale_date >= thirty_days_ago
        ).all()

        cogs = sum(
            s.quantity_sold * (s.product.cost_price or s.unit_price)
            for s in recent_sales
            if hasattr(s, 'product') and s.product
        )

        inventory_turnover_ratio = (cogs / total_stock_value * 12) if total_stock_value > 0 else None

        return InventoryMetrics(
            total_products=total_products,
            total_stock_value=float(total_stock_value),
            out_of_stock_count=out_of_stock_count,
            low_stock_count=low_stock_count,
            average_stock_level=float(average_stock_level),
            inventory_turnover_ratio=float(inventory_turnover_ratio) if inventory_turnover_ratio else None
        )

    def get_top_products(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[ProductPerformance]:
        """Get top performing products"""

        # Get sales aggregated by product
        sales_by_product = self.db.query(
            SalesRecord.product_id,
            func.sum(SalesRecord.quantity_sold).label('total_sales'),
            func.sum(SalesRecord.total_revenue - SalesRecord.discount_amount).label('total_revenue')
        ).filter(
            and_(
                SalesRecord.sale_date >= start_date,
                SalesRecord.sale_date <= end_date
            )
        ).group_by(SalesRecord.product_id).order_by(
            func.sum(SalesRecord.total_revenue - SalesRecord.discount_amount).desc()
        ).limit(limit).all()

        result = []
        days_in_period = (end_date - start_date).days or 1

        for product_id, total_sales, total_revenue in sales_by_product:
            product = self.db.query(Product).filter(Product.id == product_id).first()

            if not product:
                continue

            # Get current stock level
            latest_inventory = self.db.query(InventoryRecord).filter(
                InventoryRecord.product_id == product_id
            ).order_by(InventoryRecord.recorded_at.desc()).first()

            stock_level = latest_inventory.quantity_available if latest_inventory else 0
            avg_daily_sales = total_sales / days_in_period
            days_of_supply = (stock_level / avg_daily_sales) if avg_daily_sales > 0 else None

            result.append(ProductPerformance(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                total_sales=int(total_sales),
                total_revenue=float(total_revenue),
                average_daily_sales=float(avg_daily_sales),
                stock_level=stock_level,
                days_of_supply=float(days_of_supply) if days_of_supply else None
            ))

        return result

    def get_category_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CategoryPerformance]:
        """Get performance metrics by category"""

        # Join sales with products to get categories
        category_sales = self.db.query(
            Product.category,
            func.count(func.distinct(Product.id)).label('product_count'),
            func.sum(SalesRecord.total_revenue - SalesRecord.discount_amount).label('total_revenue'),
            func.sum(SalesRecord.quantity_sold).label('total_units')
        ).join(
            SalesRecord,
            Product.id == SalesRecord.product_id
        ).filter(
            and_(
                SalesRecord.sale_date >= start_date,
                SalesRecord.sale_date <= end_date
            )
        ).group_by(Product.category).all()

        # Calculate total revenue for market share
        total_revenue = sum(cs[2] for cs in category_sales if cs[2])

        result = []
        for category, product_count, revenue, units in category_sales:
            market_share = (revenue / total_revenue * 100) if total_revenue > 0 else 0.0

            result.append(CategoryPerformance(
                category=category,
                total_products=int(product_count),
                total_revenue=float(revenue or 0),
                total_units_sold=int(units or 0),
                market_share_percentage=float(market_share)
            ))

        return sorted(result, key=lambda x: x.total_revenue, reverse=True)

    def get_sales_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: str = 'daily'
    ) -> List[TimeSeriesMetric]:
        """Get time series data for sales"""

        sales = self.db.query(SalesRecord).filter(
            and_(
                SalesRecord.sale_date >= start_date,
                SalesRecord.sale_date <= end_date
            )
        ).all()

        if not sales:
            return []

        # Create DataFrame
        df = pd.DataFrame([
            {
                'date': s.sale_date.date(),
                'revenue': s.total_revenue - s.discount_amount,
                'quantity': s.quantity_sold
            }
            for s in sales
        ])

        # Group by date
        daily_sales = df.groupby('date').agg({
            'revenue': 'sum',
            'quantity': 'sum'
        }).reset_index()

        # Create time series
        result = []
        for _, row in daily_sales.iterrows():
            result.append(TimeSeriesMetric(
                date=datetime.combine(row['date'], datetime.min.time()),
                value=float(row['revenue']),
                metric_name='revenue'
            ))

        return result

    def generate_insights(
        self,
        sales_metrics: SalesMetrics,
        inventory_metrics: InventoryMetrics,
        top_products: List[ProductPerformance]
    ) -> List[str]:
        """Generate AI-powered insights"""

        insights = []

        # Revenue growth insight
        if sales_metrics.revenue_growth_rate is not None:
            if sales_metrics.revenue_growth_rate > 10:
                insights.append(
                    f"Strong revenue growth of {sales_metrics.revenue_growth_rate:.1f}% compared to previous period"
                )
            elif sales_metrics.revenue_growth_rate < -10:
                insights.append(
                    f"Revenue declined by {abs(sales_metrics.revenue_growth_rate):.1f}% - investigate market conditions"
                )

        # Return rate insight
        if sales_metrics.return_rate > 5:
            insights.append(
                f"High return rate of {sales_metrics.return_rate:.1f}% - review product quality and descriptions"
            )

        # Stock level insights
        if inventory_metrics.out_of_stock_count > 0:
            insights.append(
                f"{inventory_metrics.out_of_stock_count} products are out of stock - replenish immediately"
            )

        if inventory_metrics.low_stock_count > 0:
            insights.append(
                f"{inventory_metrics.low_stock_count} products have low stock - consider reordering"
            )

        # Inventory turnover insight
        if inventory_metrics.inventory_turnover_ratio is not None:
            if inventory_metrics.inventory_turnover_ratio < 4:
                insights.append(
                    f"Low inventory turnover ({inventory_metrics.inventory_turnover_ratio:.1f}x annually) - optimize stock levels"
                )
            elif inventory_metrics.inventory_turnover_ratio > 12:
                insights.append(
                    f"High inventory turnover ({inventory_metrics.inventory_turnover_ratio:.1f}x annually) - ensure adequate stock"
                )

        # Top product insights
        if top_products:
            top_product = top_products[0]
            total_revenue = sales_metrics.total_revenue

            if total_revenue > 0:
                contribution = (top_product.total_revenue / total_revenue) * 100
                if contribution > 30:
                    insights.append(
                        f"Top product '{top_product.name}' contributes {contribution:.1f}% of revenue - high dependency risk"
                    )

            # Check for stockout risk
            if top_product.days_of_supply is not None and top_product.days_of_supply < 7:
                insights.append(
                    f"Best seller '{top_product.name}' has only {top_product.days_of_supply:.0f} days of supply remaining"
                )

        return insights
