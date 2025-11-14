"""
Forecasting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


@router.post("/", response_model=ForecastResponse)
def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered demand forecast for a product

    This endpoint uses multiple AI models (Prophet, ARIMA, LSTM, XGBoost) to predict
    future demand and provides inventory recommendations.
    """
    try:
        service = ForecastService(db)

        result = service.generate_forecast(
            product_id=request.product_id,
            forecast_horizon_days=request.forecast_horizon_days,
            model_type=request.model_type,
            confidence_interval=request.confidence_interval,
            include_historical=request.include_historical
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}"
        )


@router.post("/bulk")
def generate_bulk_forecasts(
    product_ids: list[int],
    forecast_horizon_days: int = 30,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate forecasts for multiple products

    For large batches, this can be run as a background task.
    """
    service = ForecastService(db)
    results = []
    errors = []

    for product_id in product_ids:
        try:
            result = service.generate_forecast(
                product_id=product_id,
                forecast_horizon_days=forecast_horizon_days,
                include_historical=False
            )
            results.append({
                "product_id": product_id,
                "status": "success",
                "model_type": result.model_type
            })
        except Exception as e:
            errors.append({
                "product_id": product_id,
                "status": "failed",
                "error": str(e)
            })

    return {
        "total": len(product_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/accuracy/{product_id}")
def get_forecast_accuracy(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get forecast accuracy metrics for a product

    Compares historical forecasts to actual sales to measure model performance.
    """
    try:
        service = ForecastService(db)
        accuracy = service.get_forecast_accuracy(product_id, days)

        return accuracy

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate accuracy: {str(e)}"
        )
