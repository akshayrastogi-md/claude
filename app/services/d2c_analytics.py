"""
Comprehensive D2C Analytics Service
Multi-channel analytics for D2C brands
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import (
    Store, Order, Customer, MarketingCampaign,
    Shipment, Integration
)


class D2CAnalyticsService:
    """
    Comprehensive analytics service for D2C brands

    Provides:
    - Multi-channel revenue attribution
    - Customer lifetime value (LTV)
    - Marketing ROI and ROAS
    - Shipping performance
    - Customer cohort analysis
    - Product performance across channels
    """

    def __init__(self, db: Session, store_id: int):
        self.db = db
        self.store_id = store_id

    def get_dashboard_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics for D2C brand

        Returns:
            Dict with all key metrics
        """
        return {
            "revenue_metrics": self.get_revenue_metrics(start_date, end_date),
            "customer_metrics": self.get_customer_metrics(start_date, end_date),
            "marketing_metrics": self.get_marketing_metrics(start_date, end_date),
            "shipping_metrics": self.get_shipping_metrics(start_date, end_date),
            "channel_attribution": self.get_channel_attribution(start_date, end_date),
            "top_products": self.get_top_products(start_date, end_date, limit=10),
            "cohort_analysis": self.get_cohort_retention(),
            "insights": self.generate_ai_insights(start_date, end_date)
        }

    def get_revenue_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate revenue metrics"""

        orders = self.db.query(Order).filter(
            Order.store_id == self.store_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()

        if not orders:
            return {
                "total_revenue": 0,
                "total_orders": 0,
                "average_order_value": 0,
                "revenue_growth": None
            }

        total_revenue = sum(o.total - o.discount for o in orders)
        total_orders = len(orders)
        aov = total_revenue / total_orders if total_orders > 0 else 0

        # Calculate growth vs previous period
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)

        prev_orders = self.db.query(Order).filter(
            Order.store_id == self.store_id,
            Order.order_date >= prev_start,
            Order.order_date < start_date
        ).all()

        prev_revenue = sum(o.total - o.discount for o in prev_orders) if prev_orders else 0
        growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else None

        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "average_order_value": float(aov),
            "revenue_growth": float(growth) if growth is not None else None,
            "total_items_sold": sum(o.item_count for o in orders),
            "total_discount_given": sum(o.discount for o in orders),
            "average_items_per_order": sum(o.item_count for o in orders) / total_orders if total_orders > 0 else 0
        }

    def get_customer_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate customer metrics"""

        # New customers in period
        new_customers = self.db.query(Customer).filter(
            Customer.store_id == self.store_id,
            Customer.first_order_date >= start_date,
            Customer.first_order_date <= end_date
        ).count()

        # Repeat customers
        repeat_customers = self.db.query(Customer).filter(
            Customer.store_id == self.store_id,
            Customer.total_orders > 1
        ).count()

        # Total customers
        total_customers = self.db.query(Customer).filter(
            Customer.store_id == self.store_id
        ).count()

        # Average LTV
        avg_ltv = self.db.query(func.avg(Customer.lifetime_value)).filter(
            Customer.store_id == self.store_id
        ).scalar() or 0

        # Customer acquisition cost (CAC)
        marketing_spend = self.db.query(func.sum(MarketingCampaign.spent)).filter(
            MarketingCampaign.store_id == self.store_id
        ).scalar() or 0

        cac = (marketing_spend / new_customers) if new_customers > 0 else 0

        # LTV:CAC ratio
        ltv_cac_ratio = (avg_ltv / cac) if cac > 0 else 0

        return {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "repeat_customers": repeat_customers,
            "repeat_rate": (repeat_customers / total_customers * 100) if total_customers > 0 else 0,
            "average_ltv": float(avg_ltv),
            "customer_acquisition_cost": float(cac),
            "ltv_cac_ratio": float(ltv_cac_ratio)
        }

    def get_marketing_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate marketing metrics across all channels"""

        campaigns = self.db.query(MarketingCampaign).filter(
            MarketingCampaign.store_id == self.store_id
        ).all()

        if not campaigns:
            return {
                "total_spend": 0,
                "total_revenue": 0,
                "overall_roas": 0,
                "channels": []
            }

        total_spend = sum(c.spent for c in campaigns)
        total_revenue = sum(c.revenue for c in campaigns)
        overall_roas = (total_revenue / total_spend) if total_spend > 0 else 0

        # Group by channel
        channel_metrics = {}
        for campaign in campaigns:
            if campaign.channel not in channel_metrics:
                channel_metrics[campaign.channel] = {
                    "spend": 0,
                    "revenue": 0,
                    "conversions": 0,
                    "impressions": 0,
                    "clicks": 0
                }

            channel_metrics[campaign.channel]["spend"] += campaign.spent
            channel_metrics[campaign.channel]["revenue"] += campaign.revenue
            channel_metrics[campaign.channel]["conversions"] += campaign.conversions
            channel_metrics[campaign.channel]["impressions"] += campaign.impressions
            channel_metrics[campaign.channel]["clicks"] += campaign.clicks

        # Calculate ROAS for each channel
        channels = []
        for channel, metrics in channel_metrics.items():
            roas = (metrics["revenue"] / metrics["spend"]) if metrics["spend"] > 0 else 0
            ctr = (metrics["clicks"] / metrics["impressions"] * 100) if metrics["impressions"] > 0 else 0

            channels.append({
                "channel": channel,
                "spend": metrics["spend"],
                "revenue": metrics["revenue"],
                "conversions": metrics["conversions"],
                "roas": roas,
                "ctr": ctr,
                "impressions": metrics["impressions"],
                "clicks": metrics["clicks"]
            })

        # Sort by revenue
        channels.sort(key=lambda x: x["revenue"], reverse=True)

        return {
            "total_spend": float(total_spend),
            "total_revenue": float(total_revenue),
            "overall_roas": float(overall_roas),
            "total_conversions": sum(c.conversions for c in campaigns),
            "channels": channels
        }

    def get_shipping_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate shipping and logistics metrics"""

        shipments = self.db.query(Shipment).filter(
            Shipment.store_id == self.store_id,
            Shipment.created_at >= start_date,
            Shipment.created_at <= end_date
        ).all()

        if not shipments:
            return {
                "total_shipments": 0,
                "delivered": 0,
                "in_transit": 0,
                "rto": 0,
                "average_delivery_days": 0,
                "total_shipping_cost": 0
            }

        delivered = sum(1 for s in shipments if s.is_delivered)
        rto = sum(1 for s in shipments if s.is_rto)
        in_transit = len(shipments) - delivered - rto

        delivery_days = [s.delivery_days for s in shipments if s.delivery_days is not None]
        avg_delivery = sum(delivery_days) / len(delivery_days) if delivery_days else 0

        total_cost = sum(s.total_cost for s in shipments)

        # Group by courier
        courier_performance = {}
        for shipment in shipments:
            if shipment.courier_name:
                if shipment.courier_name not in courier_performance:
                    courier_performance[shipment.courier_name] = {
                        "total": 0,
                        "delivered": 0,
                        "rto": 0,
                        "avg_days": []
                    }

                courier_performance[shipment.courier_name]["total"] += 1
                if shipment.is_delivered:
                    courier_performance[shipment.courier_name]["delivered"] += 1
                if shipment.is_rto:
                    courier_performance[shipment.courier_name]["rto"] += 1
                if shipment.delivery_days:
                    courier_performance[shipment.courier_name]["avg_days"].append(shipment.delivery_days)

        couriers = []
        for courier, perf in courier_performance.items():
            delivery_rate = (perf["delivered"] / perf["total"] * 100) if perf["total"] > 0 else 0
            rto_rate = (perf["rto"] / perf["total"] * 100) if perf["total"] > 0 else 0
            avg_days = sum(perf["avg_days"]) / len(perf["avg_days"]) if perf["avg_days"] else 0

            couriers.append({
                "courier": courier,
                "total_shipments": perf["total"],
                "delivery_rate": delivery_rate,
                "rto_rate": rto_rate,
                "avg_delivery_days": avg_days
            })

        return {
            "total_shipments": len(shipments),
            "delivered": delivered,
            "in_transit": in_transit,
            "rto": rto,
            "delivery_rate": (delivered / len(shipments) * 100) if shipments else 0,
            "rto_rate": (rto / len(shipments) * 100) if shipments else 0,
            "average_delivery_days": float(avg_delivery),
            "total_shipping_cost": float(total_cost),
            "courier_performance": couriers
        }

    def get_channel_attribution(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Multi-channel attribution analysis

        Shows which channels are driving sales
        """
        orders = self.db.query(Order).filter(
            Order.store_id == self.store_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()

        channel_data = {}

        for order in orders:
            channel = order.attributed_channel or "direct"

            if channel not in channel_data:
                channel_data[channel] = {
                    "orders": 0,
                    "revenue": 0,
                    "customers": set()
                }

            channel_data[channel]["orders"] += 1
            channel_data[channel]["revenue"] += (order.total - order.discount)
            if order.customer_id:
                channel_data[channel]["customers"].add(order.customer_id)

        channels = []
        total_revenue = sum(data["revenue"] for data in channel_data.values())

        for channel, data in channel_data.items():
            share = (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0

            channels.append({
                "channel": channel,
                "orders": data["orders"],
                "revenue": float(data["revenue"]),
                "market_share": float(share),
                "unique_customers": len(data["customers"]),
                "avg_order_value": float(data["revenue"] / data["orders"]) if data["orders"] > 0 else 0
            })

        channels.sort(key=lambda x: x["revenue"], reverse=True)

        return {
            "channels": channels,
            "total_revenue": float(total_revenue)
        }

    def get_top_products(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top selling products across all channels"""

        orders = self.db.query(Order).filter(
            Order.store_id == self.store_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()

        product_stats = {}

        for order in orders:
            for item in order.line_items or []:
                product_id = item.get("product_id")
                if not product_id:
                    continue

                product_name = item.get("title") or item.get("name", "Unknown")

                if product_id not in product_stats:
                    product_stats[product_id] = {
                        "name": product_name,
                        "units_sold": 0,
                        "revenue": 0
                    }

                quantity = item.get("quantity", 0)
                price = float(item.get("price", 0))

                product_stats[product_id]["units_sold"] += quantity
                product_stats[product_id]["revenue"] += quantity * price

        products = [
            {
                "product_id": pid,
                "name": stats["name"],
                "units_sold": stats["units_sold"],
                "revenue": float(stats["revenue"])
            }
            for pid, stats in product_stats.items()
        ]

        products.sort(key=lambda x: x["revenue"], reverse=True)
        return products[:limit]

    def get_cohort_retention(self) -> Dict[str, Any]:
        """
        Customer cohort retention analysis

        Groups customers by first purchase month and tracks repeat purchases
        """
        customers = self.db.query(Customer).filter(
            Customer.store_id == self.store_id,
            Customer.first_order_date.isnot(None)
        ).all()

        cohorts = {}

        for customer in customers:
            cohort_month = customer.first_order_date.strftime("%Y-%m")

            if cohort_month not in cohorts:
                cohorts[cohort_month] = {
                    "total_customers": 0,
                    "repeat_customers": 0
                }

            cohorts[cohort_month]["total_customers"] += 1
            if customer.total_orders > 1:
                cohorts[cohort_month]["repeat_customers"] += 1

        cohort_list = []
        for month, data in sorted(cohorts.items()):
            retention = (data["repeat_customers"] / data["total_customers"] * 100) if data["total_customers"] > 0 else 0

            cohort_list.append({
                "cohort_month": month,
                "total_customers": data["total_customers"],
                "repeat_customers": data["repeat_customers"],
                "retention_rate": float(retention)
            })

        return {
            "cohorts": cohort_list
        }

    def generate_ai_insights(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """Generate AI-powered business insights"""

        insights = []

        # Get all metrics
        revenue = self.get_revenue_metrics(start_date, end_date)
        marketing = self.get_marketing_metrics(start_date, end_date)
        shipping = self.get_shipping_metrics(start_date, end_date)
        customer = self.get_customer_metrics(start_date, end_date)

        # Revenue insights
        if revenue["revenue_growth"] and revenue["revenue_growth"] > 20:
            insights.append(f"🚀 Strong growth! Revenue increased by {revenue['revenue_growth']:.1f}% vs previous period")
        elif revenue["revenue_growth"] and revenue["revenue_growth"] < -10:
            insights.append(f"⚠️ Revenue declined by {abs(revenue['revenue_growth']):.1f}% - review marketing spend and product offerings")

        # Marketing insights
        if marketing["overall_roas"] > 4:
            insights.append(f"💰 Excellent ROAS of {marketing['overall_roas']:.2f}x - marketing is highly profitable")
        elif marketing["overall_roas"] < 2:
            insights.append(f"📉 Low ROAS ({marketing['overall_roas']:.2f}x) - optimize ad campaigns and targeting")

        # Best performing channel
        if marketing["channels"]:
            best_channel = marketing["channels"][0]
            insights.append(f"⭐ {best_channel['channel'].title()} is your best channel with ${best_channel['revenue']:,.0f} revenue and {best_channel['roas']:.2f}x ROAS")

        # Customer insights
        if customer["ltv_cac_ratio"] > 3:
            insights.append(f"✅ Healthy LTV:CAC ratio of {customer['ltv_cac_ratio']:.1f}:1 - sustainable growth")
        elif customer["ltv_cac_ratio"] < 1:
            insights.append(f"⚠️ LTV:CAC ratio is {customer['ltv_cac_ratio']:.1f}:1 - improve retention or reduce acquisition cost")

        # Shipping insights
        if shipping["rto_rate"] > 10:
            insights.append(f"📦 High RTO rate of {shipping['rto_rate']:.1f}% - improve address verification and customer communication")

        if shipping["average_delivery_days"] > 7:
            insights.append(f"🚚 Average delivery time is {shipping['average_delivery_days']:.1f} days - consider faster shipping options")

        # AOV insights
        if revenue["average_order_value"]:
            insights.append(f"💵 Current AOV is ${revenue['average_order_value']:.2f} - consider upsells and bundles to increase")

        return insights
