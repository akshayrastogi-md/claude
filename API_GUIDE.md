# API Guide - Quick Start Examples

## Authentication
Currently, the API is open (no authentication required). Add authentication middleware as needed.

## Base URL
```
http://localhost:8000/api/v1
```

## Quick Start Flow

### 1. Create a Product
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "UltraBook Pro 15",
    "category": "Electronics",
    "unit_price": 1299.99,
    "cost_price": 899.99,
    "reorder_point": 10,
    "reorder_quantity": 50
  }'
```

### 2. Add Sales Data
```bash
curl -X POST "http://localhost:8000/api/v1/sales/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity_sold": 5,
    "unit_price": 1299.99,
    "total_revenue": 6499.95,
    "sales_channel": "online",
    "sale_date": "2024-01-15T10:30:00"
  }'
```

### 3. Add Inventory
```bash
curl -X POST "http://localhost:8000/api/v1/inventory/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity_on_hand": 150,
    "quantity_reserved": 10,
    "quantity_available": 140,
    "warehouse_id": "WH-001"
  }'
```

### 4. Generate AI Forecast
```bash
curl -X POST "http://localhost:8000/api/v1/forecast/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "forecast_horizon_days": 30,
    "model_type": "prophet",
    "confidence_interval": 0.95,
    "include_historical": true
  }'
```

### 5. Get Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/comprehensive?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59"
```

## Python Examples

### Using requests library

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# 1. Get all products
response = requests.get(f"{BASE_URL}/products/")
products = response.json()

# 2. Generate forecast
forecast_request = {
    "product_id": 1,
    "forecast_horizon_days": 30,
    "confidence_interval": 0.95
}
response = requests.post(f"{BASE_URL}/forecast/", json=forecast_request)
forecast = response.json()

print(f"Model: {forecast['model_type']}")
print(f"Recommendations: {forecast['recommendations']}")

# 3. Get analytics
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

response = requests.get(
    f"{BASE_URL}/analytics/comprehensive",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
)
analytics = response.json()

print(f"Total Revenue: ${analytics['sales_metrics']['total_revenue']}")
print(f"Top Product: {analytics['top_products'][0]['name']}")
```

### Using httpx (async)

```python
import httpx
import asyncio

async def get_forecast(product_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/forecast/",
            json={
                "product_id": product_id,
                "forecast_horizon_days": 30
            }
        )
        return response.json()

# Run async
forecast = asyncio.run(get_forecast(1))
```

## JavaScript Examples

### Using fetch

```javascript
// Get products
const getProducts = async () => {
  const response = await fetch('http://localhost:8000/api/v1/products/');
  const products = await response.json();
  return products;
};

// Generate forecast
const generateForecast = async (productId) => {
  const response = await fetch('http://localhost:8000/api/v1/forecast/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      product_id: productId,
      forecast_horizon_days: 30,
      confidence_interval: 0.95
    })
  });

  const forecast = await response.json();
  console.log('Forecast:', forecast);
  return forecast;
};

// Get analytics
const getAnalytics = async () => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 30);

  const params = new URLSearchParams({
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString()
  });

  const response = await fetch(
    `http://localhost:8000/api/v1/analytics/comprehensive?${params}`
  );

  const analytics = await response.json();
  return analytics;
};
```

## Model Types

### Prophet
Best for data with strong seasonal patterns
```json
{
  "model_type": "prophet"
}
```

### ARIMA
Best for stationary time series
```json
{
  "model_type": "arima"
}
```

### LSTM
Best for complex patterns
```json
{
  "model_type": "lstm"
}
```

### XGBoost
Best for feature-rich forecasting
```json
{
  "model_type": "xgboost"
}
```

### Ensemble
Combines all models (recommended)
```json
{
  "model_type": "ensemble"
}
```

### Auto-Select (Default)
Automatically chooses best model
```json
{
  "model_type": null
}
```

## Response Examples

### Forecast Response
```json
{
  "product_id": 1,
  "product_sku": "LAPTOP-001",
  "product_name": "UltraBook Pro 15",
  "model_type": "prophet",
  "forecast_horizon_days": 30,
  "confidence_interval": 0.95,
  "forecasts": [
    {
      "date": "2024-02-01T00:00:00",
      "predicted_demand": 25.5,
      "lower_bound": 18.2,
      "upper_bound": 32.8
    }
  ],
  "model_metrics": {
    "mae": 3.2,
    "rmse": 4.5,
    "mape": 12.5
  },
  "recommendations": {
    "recommended_order_quantity": 850,
    "reorder_point": 85,
    "safety_stock": 25,
    "demand_trend": "increasing"
  }
}
```

### Analytics Response
```json
{
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59",
  "sales_metrics": {
    "total_revenue": 125000.50,
    "total_units_sold": 1250,
    "average_order_value": 150.25,
    "total_orders": 832,
    "return_rate": 2.5,
    "revenue_growth_rate": 15.3
  },
  "inventory_metrics": {
    "total_products": 50,
    "total_stock_value": 250000.00,
    "out_of_stock_count": 2,
    "low_stock_count": 5,
    "average_stock_level": 150.5,
    "inventory_turnover_ratio": 8.5
  },
  "top_products": [...],
  "category_performance": [...],
  "insights": [
    "Strong revenue growth of 15.3% compared to previous period",
    "2 products are out of stock - replenish immediately"
  ]
}
```

## Error Handling

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/forecast/",
        json={"product_id": 999}
    )
    response.raise_for_status()
    forecast = response.json()
except requests.exceptions.HTTPError as e:
    if response.status_code == 404:
        print("Product not found")
    elif response.status_code == 400:
        print(f"Bad request: {response.json()['detail']}")
    else:
        print(f"Error: {e}")
except requests.exceptions.ConnectionError:
    print("Could not connect to API")
```

## Rate Limiting

Current default: 60 requests per minute per IP

## Tips

1. **Seeding Data**: Use `python scripts/seed_data.py` to populate with sample data
2. **Testing**: Use `python scripts/test_api.py` to test all endpoints
3. **Documentation**: Visit `/docs` for interactive API documentation
4. **Bulk Operations**: Use bulk endpoints for better performance with multiple items
5. **Caching**: Forecast results are cached for better performance
