"""
Main forecasting engine that orchestrates different AI models
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.ml.models import ProphetModel, ARIMAModel, XGBoostModel, LSTMModel
from app.ml.base_model import BaseForecastModel


class ForecastingEngine:
    """
    Main forecasting engine that manages multiple AI models
    and selects the best one for each product
    """

    def __init__(self):
        self.models = {
            'prophet': ProphetModel,
            'arima': ARIMAModel,
            'xgboost': XGBoostModel,
            'lstm': LSTMModel
        }

    def forecast(
        self,
        sales_data: pd.DataFrame,
        forecast_horizon_days: int = 30,
        model_type: Optional[str] = None,
        confidence_interval: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecast for product demand

        Args:
            sales_data: DataFrame with sales history (columns: date, quantity)
            forecast_horizon_days: Number of days to forecast
            model_type: Specific model to use (None = auto-select best)
            confidence_interval: Confidence interval for predictions

        Returns:
            Dictionary with forecast results and metadata
        """
        # Prepare data
        df = self._prepare_sales_data(sales_data)

        if len(df) < 30:
            raise ValueError("Insufficient historical data (minimum 30 days required)")

        # Select and train model
        if model_type and model_type in self.models:
            best_model, metrics = self._train_single_model(df, model_type)
        else:
            best_model, metrics = self._select_best_model(df)

        # Generate forecast
        forecast_df = best_model.predict(forecast_horizon_days, confidence_interval)

        # Calculate recommendations
        recommendations = self._generate_recommendations(df, forecast_df)

        return {
            'forecasts': forecast_df.to_dict('records'),
            'model_type': best_model.model_name,
            'model_metrics': metrics,
            'recommendations': recommendations,
            'confidence_interval': confidence_interval
        }

    def _prepare_sales_data(self, sales_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare sales data for forecasting

        Args:
            sales_data: Raw sales data

        Returns:
            Prepared DataFrame with 'ds' and 'y' columns
        """
        df = sales_data.copy()

        # Ensure we have the right columns
        if 'date' in df.columns and 'quantity' in df.columns:
            df = df.rename(columns={'date': 'ds', 'quantity': 'y'})
        elif 'sale_date' in df.columns and 'quantity_sold' in df.columns:
            df = df.rename(columns={'sale_date': 'ds', 'quantity_sold': 'y'})

        # Convert to datetime
        df['ds'] = pd.to_datetime(df['ds'])

        # Aggregate by day
        df = df.groupby('ds').agg({'y': 'sum'}).reset_index()

        # Fill missing dates with zero
        date_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
        df = df.set_index('ds').reindex(date_range, fill_value=0).reset_index()
        df.columns = ['ds', 'y']

        return df

    def _train_single_model(self, df: pd.DataFrame, model_type: str) -> tuple:
        """Train a single model and return it with metrics"""
        model_class = self.models[model_type]
        model = model_class()

        try:
            model.train(df)
            metrics = model.evaluate(df)
        except Exception as e:
            metrics = {'error': str(e), 'mae': float('inf')}

        return model, metrics

    def _select_best_model(self, df: pd.DataFrame) -> tuple:
        """
        Select the best forecasting model based on historical performance

        Args:
            df: Historical data

        Returns:
            Tuple of (best_model, metrics)
        """
        results = []

        # Try each model
        for model_name, model_class in self.models.items():
            try:
                model = model_class()
                model.train(df)
                metrics = model.evaluate(df)
                metrics['model_name'] = model_name

                results.append({
                    'model': model,
                    'metrics': metrics,
                    'mae': metrics.get('mae', float('inf'))
                })
            except Exception as e:
                # Skip models that fail
                continue

        if not results:
            # Fallback to Prophet if all models fail
            model = ProphetModel()
            model.train(df)
            return model, {'model_name': 'prophet', 'note': 'fallback_model'}

        # Select model with lowest MAE
        best_result = min(results, key=lambda x: x['mae'])

        return best_result['model'], best_result['metrics']

    def _generate_recommendations(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate inventory recommendations based on forecast

        Args:
            historical_df: Historical sales data
            forecast_df: Forecast data

        Returns:
            Dictionary with recommendations
        """
        # Calculate statistics
        avg_demand = historical_df['y'].mean()
        max_demand = historical_df['y'].max()
        forecast_total = forecast_df['yhat'].sum()
        forecast_avg = forecast_df['yhat'].mean()
        forecast_max = forecast_df['yhat'].max()

        # Calculate safety stock (using 1.65 for 95% service level)
        demand_std = historical_df['y'].std()
        lead_time_days = 7  # Assume 7 days lead time
        safety_stock = 1.65 * demand_std * np.sqrt(lead_time_days)

        # Recommended order quantity (for forecast period)
        recommended_order = int(forecast_total + safety_stock)

        # Reorder point
        reorder_point = int((forecast_avg * lead_time_days) + safety_stock)

        # Stock level recommendations
        min_stock = int(forecast_avg * 7)  # 1 week of average demand
        max_stock = int(forecast_max * 14)  # 2 weeks of max demand

        return {
            'recommended_order_quantity': max(recommended_order, 0),
            'reorder_point': max(reorder_point, 0),
            'safety_stock': max(int(safety_stock), 0),
            'min_stock_level': max(min_stock, 0),
            'max_stock_level': max(max_stock, 0),
            'forecasted_total_demand': float(forecast_total),
            'forecasted_avg_daily_demand': float(forecast_avg),
            'historical_avg_daily_demand': float(avg_demand),
            'demand_trend': 'increasing' if forecast_avg > avg_demand else 'decreasing'
        }

    def ensemble_forecast(
        self,
        sales_data: pd.DataFrame,
        forecast_horizon_days: int = 30,
        confidence_interval: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate ensemble forecast using multiple models

        Args:
            sales_data: DataFrame with sales history
            forecast_horizon_days: Number of days to forecast
            confidence_interval: Confidence interval for predictions

        Returns:
            Dictionary with ensemble forecast results
        """
        df = self._prepare_sales_data(sales_data)

        forecasts = []
        weights = []

        # Generate forecasts from each model
        for model_name, model_class in self.models.items():
            try:
                model = model_class()
                model.train(df)

                # Evaluate to get weight
                metrics = model.evaluate(df)
                mae = metrics.get('mae', float('inf'))

                if mae < float('inf'):
                    forecast = model.predict(forecast_horizon_days, confidence_interval)
                    forecasts.append(forecast)

                    # Weight is inverse of MAE
                    weights.append(1.0 / (mae + 1))

            except Exception:
                continue

        if not forecasts:
            raise RuntimeError("All models failed to generate forecasts")

        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()

        # Weighted average of forecasts
        ensemble_forecast = forecasts[0].copy()
        ensemble_forecast['yhat'] = sum(
            f['yhat'] * w for f, w in zip(forecasts, weights)
        )
        ensemble_forecast['lower'] = sum(
            f['lower'] * w for f, w in zip(forecasts, weights)
        )
        ensemble_forecast['upper'] = sum(
            f['upper'] * w for f, w in zip(forecasts, weights)
        )

        recommendations = self._generate_recommendations(df, ensemble_forecast)

        return {
            'forecasts': ensemble_forecast.to_dict('records'),
            'model_type': 'ensemble',
            'model_metrics': {'models_used': len(forecasts), 'weights': weights.tolist()},
            'recommendations': recommendations,
            'confidence_interval': confidence_interval
        }
