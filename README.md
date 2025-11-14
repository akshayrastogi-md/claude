# 🤖 AI-Powered Inventory Forecasting & Ecommerce Analytics API

A complete FastAPI-based backend service for AI-powered inventory forecasting and advanced ecommerce analytics. This service uses multiple machine learning models to predict demand and provide actionable insights for inventory management.

## 🌟 Features

### AI-Powered Forecasting
- **Multiple AI Models**: Prophet, ARIMA, LSTM, XGBoost
- **Auto-Model Selection**: Automatically selects the best model based on historical performance
- **Ensemble Forecasting**: Combines predictions from multiple models
- **Confidence Intervals**: Provides upper and lower bounds for predictions
- **Inventory Recommendations**: Calculates reorder points, safety stock, and order quantities

### Advanced Analytics
- **Sales Metrics**: Revenue, orders, AOV, growth rate, return rate
- **Inventory Metrics**: Stock levels, turnover ratio, out-of-stock alerts
- **Product Performance**: Top products, category analysis
- **Time Series Analysis**: Daily sales trends and patterns
- **AI-Generated Insights**: Automated business insights

### API Features
- **RESTful Design**: Clean, intuitive API endpoints
- **Automatic Documentation**: Interactive Swagger UI and ReDoc
- **Data Validation**: Pydantic schemas for all requests/responses
- **CORS Support**: Cross-origin resource sharing enabled
- **Error Handling**: Comprehensive error responses
- **Performance Monitoring**: Request timing headers

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd claude
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
python app/main.py
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the API**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Products
- `POST /api/v1/products/` - Create a new product
- `GET /api/v1/products/` - List all products
- `GET /api/v1/products/{id}` - Get product by ID
- `GET /api/v1/products/sku/{sku}` - Get product by SKU
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Inventory
- `POST /api/v1/inventory/` - Create inventory record
- `GET /api/v1/inventory/` - List inventory records
- `GET /api/v1/inventory/current` - Get current inventory levels
- `GET /api/v1/inventory/product/{id}` - Get product inventory history

### Sales
- `POST /api/v1/sales/` - Create sales record
- `POST /api/v1/sales/bulk` - Create multiple sales records
- `GET /api/v1/sales/` - List sales records
- `GET /api/v1/sales/product/{id}` - Get product sales history

### Forecasting 🤖
- `POST /api/v1/forecast/` - Generate AI forecast for a product
- `POST /api/v1/forecast/bulk` - Generate forecasts for multiple products
- `GET /api/v1/forecast/accuracy/{id}` - Get forecast accuracy metrics

### Analytics 📊
- `GET /api/v1/analytics/comprehensive` - Get comprehensive analytics
- `GET /api/v1/analytics/sales-metrics` - Get sales metrics
- `GET /api/v1/analytics/inventory-metrics` - Get inventory metrics
- `GET /api/v1/analytics/top-products` - Get top performing products
- `GET /api/v1/analytics/category-performance` - Get category performance
- `GET /api/v1/analytics/dashboard` - Get dashboard summary

## 🔮 Forecasting Example

```python
import requests

# Generate forecast for a product
response = requests.post(
    "http://localhost:8000/api/v1/forecast/",
    json={
        "product_id": 1,
        "forecast_horizon_days": 30,
        "model_type": "prophet",  # or "arima", "lstm", "xgboost", "ensemble"
        "confidence_interval": 0.95,
        "include_historical": True
    }
)

forecast = response.json()
print(f"Model used: {forecast['model_type']}")
print(f"Recommended order quantity: {forecast['recommendations']['recommended_order_quantity']}")
```

## 📊 Analytics Example

```python
import requests
from datetime import datetime, timedelta

# Get comprehensive analytics
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

response = requests.get(
    "http://localhost:8000/api/v1/analytics/comprehensive",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
)

analytics = response.json()
print(f"Total revenue: ${analytics['sales_metrics']['total_revenue']:.2f}")
print(f"Top product: {analytics['top_products'][0]['name']}")
print(f"AI Insights: {analytics['insights']}")
```

## 🧠 AI Models

### Prophet (Facebook)
- Best for: Time series with strong seasonal patterns
- Strengths: Handles missing data, outliers, and holidays well
- Use case: Products with weekly/yearly seasonality

### ARIMA
- Best for: Stationary time series data
- Strengths: Classical statistical approach, interpretable
- Use case: Products with stable demand patterns

### LSTM (Neural Network)
- Best for: Complex patterns and long-term dependencies
- Strengths: Learns from non-linear patterns
- Use case: Products with complex demand patterns

### XGBoost
- Best for: Feature-rich forecasting
- Strengths: Fast, accurate, handles various patterns
- Use case: Products with multiple influencing factors

### Ensemble
- Combines all models using weighted averaging
- Automatically selects weights based on historical accuracy
- Use case: Maximum accuracy, production deployments

## 🗄️ Database Models

### Product
- SKU, name, description, category
- Pricing information
- Inventory thresholds
- Physical attributes

### Inventory Record
- Stock levels (on-hand, reserved, available)
- Warehouse and location
- Historical tracking

### Sales Record
- Quantity sold, revenue, discounts
- Order and customer information
- Sales channel and location
- Return tracking

### Forecast Result
- Predictions with confidence intervals
- Model metadata and accuracy
- Historical forecast tracking

## 🐳 Docker Deployment

```bash
# Build image
docker build -t inventory-forecast-api .

# Run container
docker run -p 8000:8000 inventory-forecast-api
```

## 📝 Configuration

Edit `.env` file to configure:

- **Database**: SQLite (default) or PostgreSQL
- **AI Models**: Enable/disable specific models
- **Forecast Settings**: Horizon, confidence intervals
- **CORS**: Allowed origins
- **Cache**: Enable caching for better performance

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📈 Performance

- **Response Time**: < 100ms for most endpoints
- **Forecast Generation**: 2-10 seconds depending on model
- **Batch Processing**: Supports background tasks
- **Caching**: Built-in caching for improved performance

## 🔒 Security

- Input validation with Pydantic
- SQL injection protection via SQLAlchemy
- CORS configuration
- Rate limiting (configurable)
- Environment-based secrets

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.109+
- **ML/AI**: Prophet, Statsmodels, XGBoost, TensorFlow
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Server**: Uvicorn

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Support

For issues and questions, please open a GitHub issue.

## 🚦 Status

- ✅ Core API: Production Ready
- ✅ AI Forecasting: Production Ready
- ✅ Analytics: Production Ready
- ✅ Documentation: Complete
- 🔄 Additional Features: In Development

---

Built with ❤️ using FastAPI and AI
