"""
Base forecasting model interface
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Tuple
import numpy as np


class BaseForecastModel(ABC):
    """Abstract base class for all forecasting models"""

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_name = "base"

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None:
        """
        Train the forecasting model

        Args:
            df: DataFrame with 'ds' (date) and 'y' (value) columns
        """
        pass

    @abstractmethod
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Generate forecasts

        Args:
            periods: Number of periods to forecast
            confidence_interval: Confidence interval (default: 0.95)

        Returns:
            DataFrame with predictions and confidence bounds
        """
        pass

    def evaluate(self, df: pd.DataFrame, test_size: int = 30) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            df: DataFrame with historical data
            test_size: Number of periods to use for testing

        Returns:
            Dictionary of evaluation metrics
        """
        if len(df) < test_size + 30:
            return {"error": "Insufficient data for evaluation"}

        train_df = df[:-test_size].copy()
        test_df = df[-test_size:].copy()

        # Train on training data
        self.train(train_df)

        # Predict test period
        predictions = self.predict(test_size)

        # Calculate metrics
        actual = test_df['y'].values
        predicted = predictions['yhat'].values[:len(actual)]

        mae = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-10))) * 100

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "test_size": test_size
        }

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for forecasting

        Args:
            df: Raw DataFrame

        Returns:
            Prepared DataFrame with required columns
        """
        if 'ds' not in df.columns or 'y' not in df.columns:
            raise ValueError("DataFrame must have 'ds' and 'y' columns")

        df = df.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.sort_values('ds')
        df = df.dropna(subset=['y'])

        return df
