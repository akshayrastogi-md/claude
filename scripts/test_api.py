"""
Test script for API endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health():
    """Test health endpoint"""
    print_section("Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def test_products():
    """Test product endpoints"""
    print_section("Products")

    # List products
    response = requests.get(f"{BASE_URL}/api/v1/products/")
    products = response.json()
    print(f"Total products: {len(products)}")

    if products:
        product = products[0]
        print(f"\nFirst product:")
        print(f"  SKU: {product['sku']}")
        print(f"  Name: {product['name']}")
        print(f"  Price: ${product['unit_price']}")
        return product['id']

    return None


def test_forecast(product_id):
    """Test forecasting endpoint"""
    print_section("AI Forecasting")

    if not product_id:
        print("No product ID available for forecasting")
        return

    payload = {
        "product_id": product_id,
        "forecast_horizon_days": 30,
        "confidence_interval": 0.95,
        "include_historical": False
    }

    print(f"Generating forecast for product ID: {product_id}...")
    response = requests.post(f"{BASE_URL}/api/v1/forecast/", json=payload)

    if response.status_code == 200:
        forecast = response.json()
        print(f"\n✅ Forecast generated successfully!")
        print(f"  Model: {forecast['model_type']}")
        print(f"  Forecasts: {len(forecast['forecasts'])} days")

        if 'model_metrics' in forecast and forecast['model_metrics']:
            print(f"  Model Metrics: {json.dumps(forecast['model_metrics'], indent=4)}")

        if 'recommendations' in forecast:
            rec = forecast['recommendations']
            print(f"\n  📦 Inventory Recommendations:")
            print(f"    Recommended Order: {rec.get('recommended_order_quantity', 'N/A')} units")
            print(f"    Reorder Point: {rec.get('reorder_point', 'N/A')} units")
            print(f"    Safety Stock: {rec.get('safety_stock', 'N/A')} units")
            print(f"    Demand Trend: {rec.get('demand_trend', 'N/A')}")

        # Show first few forecasts
        print(f"\n  First 5 forecasts:")
        for f in forecast['forecasts'][:5]:
            date = f['date'][:10]
            demand = f['predicted_demand']
            print(f"    {date}: {demand:.1f} units")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_analytics():
    """Test analytics endpoint"""
    print_section("Advanced Analytics")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

    response = requests.get(f"{BASE_URL}/api/v1/analytics/comprehensive", params=params)

    if response.status_code == 200:
        analytics = response.json()
        print("✅ Analytics generated successfully!\n")

        # Sales metrics
        sales = analytics['sales_metrics']
        print("💰 Sales Metrics:")
        print(f"  Total Revenue: ${sales['total_revenue']:,.2f}")
        print(f"  Total Orders: {sales['total_orders']}")
        print(f"  Average Order Value: ${sales['average_order_value']:,.2f}")
        print(f"  Return Rate: {sales['return_rate']:.2f}%")
        if sales.get('revenue_growth_rate'):
            print(f"  Growth Rate: {sales['revenue_growth_rate']:.2f}%")

        # Inventory metrics
        inv = analytics['inventory_metrics']
        print(f"\n📊 Inventory Metrics:")
        print(f"  Total Products: {inv['total_products']}")
        print(f"  Stock Value: ${inv['total_stock_value']:,.2f}")
        print(f"  Out of Stock: {inv['out_of_stock_count']}")
        print(f"  Low Stock: {inv['low_stock_count']}")

        # Top products
        print(f"\n🏆 Top 3 Products:")
        for i, product in enumerate(analytics['top_products'][:3], 1):
            print(f"  {i}. {product['name']} (SKU: {product['sku']})")
            print(f"     Revenue: ${product['total_revenue']:,.2f}")
            print(f"     Units Sold: {product['total_sales']}")

        # Insights
        if analytics.get('insights'):
            print(f"\n💡 AI-Generated Insights:")
            for insight in analytics['insights']:
                print(f"  • {insight}")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_dashboard():
    """Test dashboard endpoint"""
    print_section("Dashboard Summary")

    response = requests.get(f"{BASE_URL}/api/v1/analytics/dashboard")

    if response.status_code == 200:
        dashboard = response.json()
        print(json.dumps(dashboard, indent=2))
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    """Run all tests"""
    print("\n🧪 Testing AI Inventory Forecasting API")
    print("=" * 60)

    try:
        # Test health
        test_health()

        # Test products and get a product ID
        product_id = test_products()

        # Test forecasting
        test_forecast(product_id)

        # Test analytics
        test_analytics()

        # Test dashboard
        test_dashboard()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("Make sure the API is running at http://localhost:8000")
        print("Start it with: python app/main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
