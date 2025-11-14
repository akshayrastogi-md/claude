"""
Forecasting service
"""
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Product, SalesRecord, ForecastResult
from app.ml.forecasting_engine import ForecastingEngine
from app.schemas.forecast import ForecastResponse, ForecastPoint


class ForecastService:
    """Service for inventory forecasting"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = ForecastingEngine()

    def generate_forecast(
        self,
        product_id: int,
        forecast_horizon_days: int = 30,
        model_type: Optional[str] = None,
        confidence_interval: float = 0.95,
        include_historical: bool = True
    ) -> ForecastResponse:
        """
        Generate demand forecast for a product

        Args:
            product_id: Product ID
            forecast_horizon_days: Number of days to forecast
            model_type: Specific model to use (None = auto-select)
            confidence_interval: Confidence interval
            include_historical: Include historical data in response

        Returns:
            ForecastResponse with predictions
        """
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        # Get sales history
        sales = self.db.query(SalesRecord).filter(
            SalesRecord.product_id == product_id
        ).order_by(SalesRecord.sale_date).all()

        if len(sales) < 30:
            raise ValueError(
                f"Insufficient sales history for product {product.sku}. "
                f"Minimum 30 days required, found {len(sales)} records."
            )

        # Prepare sales data
        sales_df = pd.DataFrame([
            {
                'sale_date': s.sale_date,
                'quantity_sold': s.quantity_sold
            }
            for s in sales
        ])

        # Generate forecast
        if model_type == 'ensemble':
            forecast_result = self.engine.ensemble_forecast(
                sales_df,
                forecast_horizon_days,
                confidence_interval
            )
        else:
            forecast_result = self.engine.forecast(
                sales_df,
                forecast_horizon_days,
                model_type,
                confidence_interval
            )

        # Save forecast to database
        self._save_forecast_results(product_id, forecast_result)

        # Prepare response
        forecast_points = [
            ForecastPoint(
                date=f['ds'],
                predicted_demand=f['yhat'],
                lower_bound=f.get('lower'),
                upper_bound=f.get('upper')
            )
            for f in forecast_result['forecasts']
        ]

        historical_data = None
        if include_historical:
            historical_data = [
                {
                    'date': s.sale_date.isoformat(),
                    'quantity': s.quantity_sold,
                    'revenue': s.total_revenue
                }
                for s in sales[-90:]  # Last 90 days
            ]

        return ForecastResponse(
            product_id=product.id,
            product_sku=product.sku,
            product_name=product.name,
            model_type=forecast_result['model_type'],
            forecast_horizon_days=forecast_horizon_days,
            confidence_interval=confidence_interval,
            forecasts=forecast_points,
            model_metrics=forecast_result.get('model_metrics'),
            recommendations=forecast_result.get('recommendations'),
            historical_data=historical_data
        )

    def _save_forecast_results(self, product_id: int, forecast_result: Dict[str, Any]) -> None:
        """Save forecast results to database"""

        for forecast_point in forecast_result['forecasts']:
            forecast_record = ForecastResult(
                product_id=product_id,
                forecast_date=forecast_point['ds'],
                predicted_demand=forecast_point['yhat'],
                lower_bound=forecast_point.get('lower'),
                upper_bound=forecast_point.get('upper'),
                confidence_interval=forecast_result['confidence_interval'],
                model_type=forecast_result['model_type'],
                model_version='1.0',
                forecast_horizon_days=len(forecast_result['forecasts']),
                model_metrics=forecast_result.get('model_metrics'),
                created_at=datetime.utcnow()
            )

            self.db.add(forecast_record)

        self.db.commit()

    def get_forecast_accuracy(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculate forecast accuracy by comparing predictions to actual sales

        Args:
            product_id: Product ID
            days: Number of days to analyze

        Returns:
            Dictionary with accuracy metrics
        """
        from datetime import timedelta

        # Get forecasts from 'days' ago
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        forecasts = self.db.query(ForecastResult).filter(
            ForecastResult.product_id == product_id,
            ForecastResult.created_at >= cutoff_date,
            ForecastResult.forecast_date <= datetime.utcnow()
        ).all()

        if not forecasts:
            return {"error": "No forecasts available for accuracy calculation"}

        # Get actual sales for the same period
        actual_sales = {}
        sales = self.db.query(SalesRecord).filter(
            SalesRecord.product_id == product_id,
            SalesRecord.sale_date >= cutoff_date
        ).all()

        for sale in sales:
            date_key = sale.sale_date.date()
            actual_sales[date_key] = actual_sales.get(date_key, 0) + sale.quantity_sold

        # Compare forecasts to actuals
        errors = []
        for forecast in forecasts:
            forecast_date = forecast.forecast_date.date()
            if forecast_date in actual_sales:
                actual = actual_sales[forecast_date]
                predicted = forecast.predicted_demand
                errors.append(abs(actual - predicted))

        if not errors:
            return {"error": "No matching forecast-actual pairs found"}

        mae = sum(errors) / len(errors)
        rmse = (sum(e ** 2 for e in errors) / len(errors)) ** 0.5

        return {
            "mae": mae,
            "rmse": rmse,
            "samples": len(errors),
            "period_days": days
        }
