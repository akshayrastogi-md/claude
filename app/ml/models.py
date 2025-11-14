"""
Forecasting model implementations
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from app.ml.base_model import BaseForecastModel
import warnings
warnings.filterwarnings('ignore')


class ProphetModel(BaseForecastModel):
    """Facebook Prophet forecasting model"""

    def __init__(self):
        super().__init__()
        self.model_name = "prophet"

    def train(self, df: pd.DataFrame) -> None:
        """Train Prophet model"""
        try:
            from prophet import Prophet

            df = self.prepare_data(df)

            self.model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                interval_width=0.95,
                changepoint_prior_scale=0.05
            )

            self.model.fit(df)
            self.is_trained = True

        except Exception as e:
            raise RuntimeError(f"Prophet training failed: {str(e)}")

    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """Generate Prophet forecasts"""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)

        # Return last 'periods' rows (the actual forecast)
        forecast = forecast.tail(periods)

        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
            columns={'ds': 'ds', 'yhat': 'yhat', 'yhat_lower': 'lower', 'yhat_upper': 'upper'}
        )


class ARIMAModel(BaseForecastModel):
    """ARIMA forecasting model"""

    def __init__(self):
        super().__init__()
        self.model_name = "arima"
        self.order = (1, 1, 1)  # Default ARIMA order

    def train(self, df: pd.DataFrame) -> None:
        """Train ARIMA model"""
        try:
            from statsmodels.tsa.arima.model import ARIMA

            df = self.prepare_data(df)
            values = df['y'].values

            # Auto-select best order (simplified)
            self.model = ARIMA(values, order=self.order)
            self.model = self.model.fit()
            self.is_trained = True
            self.last_date = df['ds'].max()

        except Exception as e:
            raise RuntimeError(f"ARIMA training failed: {str(e)}")

    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """Generate ARIMA forecasts"""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        forecast = self.model.forecast(steps=periods)
        conf_int = self.model.get_forecast(steps=periods).conf_int(alpha=1 - confidence_interval)

        # Generate future dates
        future_dates = pd.date_range(start=self.last_date + pd.Timedelta(days=1), periods=periods, freq='D')

        result = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecast.values,
            'lower': conf_int.iloc[:, 0].values,
            'upper': conf_int.iloc[:, 1].values
        })

        return result


class XGBoostModel(BaseForecastModel):
    """XGBoost forecasting model"""

    def __init__(self):
        super().__init__()
        self.model_name = "xgboost"
        self.lookback = 7  # Use last 7 days for prediction

    def train(self, df: pd.DataFrame) -> None:
        """Train XGBoost model"""
        try:
            import xgboost as xgb

            df = self.prepare_data(df)

            # Create features
            X, y = self._create_features(df)

            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )

            self.model.fit(X, y)
            self.is_trained = True
            self.last_values = df['y'].tail(self.lookback).values
            self.last_date = df['ds'].max()

        except Exception as e:
            raise RuntimeError(f"XGBoost training failed: {str(e)}")

    def _create_features(self, df: pd.DataFrame):
        """Create lag features for XGBoost"""
        features = []
        targets = []

        values = df['y'].values

        for i in range(self.lookback, len(values)):
            features.append(values[i - self.lookback:i])
            targets.append(values[i])

        return np.array(features), np.array(targets)

    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """Generate XGBoost forecasts"""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = []
        current_values = list(self.last_values)

        for _ in range(periods):
            X = np.array([current_values[-self.lookback:]])
            pred = self.model.predict(X)[0]
            predictions.append(pred)
            current_values.append(pred)

        # Generate confidence intervals (simplified using std)
        std = np.std(predictions)
        z_score = 1.96 if confidence_interval == 0.95 else 2.576

        future_dates = pd.date_range(start=self.last_date + pd.Timedelta(days=1), periods=periods, freq='D')

        result = pd.DataFrame({
            'ds': future_dates,
            'yhat': predictions,
            'lower': [p - z_score * std for p in predictions],
            'upper': [p + z_score * std for p in predictions]
        })

        return result


class LSTMModel(BaseForecastModel):
    """LSTM neural network forecasting model"""

    def __init__(self):
        super().__init__()
        self.model_name = "lstm"
        self.lookback = 14
        self.scaler = None

    def train(self, df: pd.DataFrame) -> None:
        """Train LSTM model"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from sklearn.preprocessing import MinMaxScaler

            df = self.prepare_data(df)

            # Scale data
            self.scaler = MinMaxScaler()
            values = df['y'].values.reshape(-1, 1)
            scaled_values = self.scaler.fit_transform(values)

            # Create sequences
            X, y = self._create_sequences(scaled_values)

            # Build LSTM model
            self.model = keras.Sequential([
                keras.layers.LSTM(50, activation='relu', input_shape=(self.lookback, 1)),
                keras.layers.Dense(25, activation='relu'),
                keras.layers.Dense(1)
            ])

            self.model.compile(optimizer='adam', loss='mse')
            self.model.fit(X, y, epochs=50, batch_size=32, verbose=0)

            self.is_trained = True
            self.last_values = scaled_values[-self.lookback:]
            self.last_date = df['ds'].max()

        except Exception as e:
            raise RuntimeError(f"LSTM training failed: {str(e)}")

    def _create_sequences(self, data):
        """Create sequences for LSTM"""
        X, y = [], []

        for i in range(self.lookback, len(data)):
            X.append(data[i - self.lookback:i])
            y.append(data[i])

        return np.array(X), np.array(y)

    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """Generate LSTM forecasts"""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        predictions = []
        current_sequence = self.last_values.copy()

        for _ in range(periods):
            X = current_sequence.reshape(1, self.lookback, 1)
            pred = self.model.predict(X, verbose=0)[0, 0]
            predictions.append(pred)

            # Update sequence
            current_sequence = np.append(current_sequence[1:], [[pred]], axis=0)

        # Inverse transform predictions
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

        # Confidence intervals (simplified)
        std = np.std(predictions)
        z_score = 1.96 if confidence_interval == 0.95 else 2.576

        future_dates = pd.date_range(start=self.last_date + pd.Timedelta(days=1), periods=periods, freq='D')

        result = pd.DataFrame({
            'ds': future_dates,
            'yhat': predictions,
            'lower': predictions - z_score * std,
            'upper': predictions + z_score * std
        })

        return result
