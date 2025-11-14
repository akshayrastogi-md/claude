"""
Seed database with example data for testing and demonstration
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from app.core.database import SessionLocal, init_db
from app.models import Product, SalesRecord, InventoryRecord


def seed_products(db):
    """Seed sample products"""
    print("📦 Seeding products...")

    products = [
        {
            "sku": "LAPTOP-001",
            "name": "UltraBook Pro 15",
            "description": "High-performance laptop for professionals",
            "category": "Electronics",
            "sub_category": "Laptops",
            "brand": "TechCorp",
            "unit_price": 1299.99,
            "cost_price": 899.99,
            "reorder_point": 10,
            "reorder_quantity": 50,
            "safety_stock": 5
        },
        {
            "sku": "PHONE-001",
            "name": "SmartPhone X1",
            "description": "Latest flagship smartphone",
            "category": "Electronics",
            "sub_category": "Phones",
            "brand": "MobileTech",
            "unit_price": 899.99,
            "cost_price": 599.99,
            "reorder_point": 20,
            "reorder_quantity": 100,
            "safety_stock": 10
        },
        {
            "sku": "TABLET-001",
            "name": "TabPro 12",
            "description": "Professional tablet with stylus",
            "category": "Electronics",
            "sub_category": "Tablets",
            "brand": "TechCorp",
            "unit_price": 699.99,
            "cost_price": 449.99,
            "reorder_point": 15,
            "reorder_quantity": 75,
            "safety_stock": 8
        },
        {
            "sku": "HEADPHONE-001",
            "name": "Wireless Pro Headphones",
            "description": "Premium noise-cancelling headphones",
            "category": "Electronics",
            "sub_category": "Audio",
            "brand": "AudioMax",
            "unit_price": 299.99,
            "cost_price": 149.99,
            "reorder_point": 25,
            "reorder_quantity": 150,
            "safety_stock": 15,
            "is_seasonal": True
        },
        {
            "sku": "MOUSE-001",
            "name": "Ergonomic Wireless Mouse",
            "description": "Comfortable wireless mouse",
            "category": "Electronics",
            "sub_category": "Accessories",
            "brand": "PeripheralCo",
            "unit_price": 49.99,
            "cost_price": 24.99,
            "reorder_point": 50,
            "reorder_quantity": 300,
            "safety_stock": 25
        },
        {
            "sku": "KEYBOARD-001",
            "name": "Mechanical Gaming Keyboard",
            "description": "RGB mechanical keyboard",
            "category": "Electronics",
            "sub_category": "Accessories",
            "brand": "GamerGear",
            "unit_price": 149.99,
            "cost_price": 79.99,
            "reorder_point": 30,
            "reorder_quantity": 200,
            "safety_stock": 20
        },
        {
            "sku": "MONITOR-001",
            "name": "4K Ultra HD Monitor 27\"",
            "description": "Professional 4K monitor",
            "category": "Electronics",
            "sub_category": "Displays",
            "brand": "DisplayPro",
            "unit_price": 499.99,
            "cost_price": 299.99,
            "reorder_point": 12,
            "reorder_quantity": 60,
            "safety_stock": 6
        },
        {
            "sku": "CAMERA-001",
            "name": "Digital Camera Pro",
            "description": "Professional DSLR camera",
            "category": "Electronics",
            "sub_category": "Photography",
            "brand": "PhotoTech",
            "unit_price": 1499.99,
            "cost_price": 999.99,
            "reorder_point": 8,
            "reorder_quantity": 40,
            "safety_stock": 4
        },
        {
            "sku": "SPEAKER-001",
            "name": "Smart Speaker Pro",
            "description": "AI-powered smart speaker",
            "category": "Electronics",
            "sub_category": "Audio",
            "brand": "SmartHome",
            "unit_price": 199.99,
            "cost_price": 99.99,
            "reorder_point": 35,
            "reorder_quantity": 180,
            "safety_stock": 18
        },
        {
            "sku": "WATCH-001",
            "name": "SmartWatch Elite",
            "description": "Premium fitness smartwatch",
            "category": "Electronics",
            "sub_category": "Wearables",
            "brand": "WearTech",
            "unit_price": 399.99,
            "cost_price": 249.99,
            "reorder_point": 18,
            "reorder_quantity": 90,
            "safety_stock": 9,
            "is_seasonal": True
        }
    ]

    db_products = []
    for product_data in products:
        product = Product(**product_data)
        db.add(product)
        db_products.append(product)

    db.commit()
    print(f"✅ Created {len(db_products)} products")
    return db_products


def seed_sales(db, products):
    """Seed sample sales data for the past 90 days"""
    print("💰 Seeding sales data...")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)

    sales_channels = ["online", "retail", "wholesale"]
    regions = ["North", "South", "East", "West"]
    countries = ["USA", "Canada", "UK", "Germany", "France"]

    sales_count = 0

    for product in products:
        # Generate sales for each day
        current_date = start_date

        # Base daily demand with some randomness
        base_demand = random.randint(5, 30)

        while current_date <= end_date:
            # Add some seasonality and trend
            day_of_week = current_date.weekday()
            week_multiplier = 1.3 if day_of_week in [4, 5, 6] else 1.0  # Weekend boost

            # Trend (slight increase over time)
            trend_multiplier = 1 + ((current_date - start_date).days / 180)

            # Random variation
            random_multiplier = random.uniform(0.7, 1.3)

            daily_sales = int(base_demand * week_multiplier * trend_multiplier * random_multiplier)

            # Create 1-3 sales records per day
            num_orders = random.randint(1, min(3, max(1, daily_sales)))

            for _ in range(num_orders):
                quantity = max(1, daily_sales // num_orders + random.randint(-2, 2))

                if quantity > 0:
                    # Calculate pricing
                    unit_price = product.unit_price
                    discount = random.choice([0, 0, 0, 0.05, 0.10, 0.15])  # 60% no discount
                    discount_amount = unit_price * quantity * discount
                    total_revenue = unit_price * quantity

                    sale = SalesRecord(
                        product_id=product.id,
                        quantity_sold=quantity,
                        unit_price=unit_price,
                        total_revenue=total_revenue,
                        discount_amount=discount_amount,
                        order_id=f"ORD-{random.randint(10000, 99999)}",
                        customer_id=f"CUST-{random.randint(1000, 9999)}",
                        sales_channel=random.choice(sales_channels),
                        region=random.choice(regions),
                        country=random.choice(countries),
                        is_returned=random.random() < 0.03,  # 3% return rate
                        sale_date=current_date + timedelta(
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                    )

                    db.add(sale)
                    sales_count += 1

            current_date += timedelta(days=1)

    db.commit()
    print(f"✅ Created {sales_count} sales records")


def seed_inventory(db, products):
    """Seed current inventory levels"""
    print("📊 Seeding inventory data...")

    warehouses = ["WH-001", "WH-002", "WH-003"]
    inventory_count = 0

    for product in products:
        for warehouse in warehouses:
            # Random stock level
            quantity = random.randint(50, 500)
            reserved = random.randint(0, min(50, quantity))
            available = quantity - reserved

            inventory = InventoryRecord(
                product_id=product.id,
                quantity_on_hand=quantity,
                quantity_reserved=reserved,
                quantity_available=available,
                warehouse_id=warehouse,
                location=f"AISLE-{random.randint(1, 20)}-SHELF-{random.randint(1, 10)}",
                recorded_at=datetime.utcnow()
            )

            db.add(inventory)
            inventory_count += 1

    db.commit()
    print(f"✅ Created {inventory_count} inventory records")


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...\n")

    # Initialize database
    init_db()

    # Create session
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_products = db.query(Product).count()
        if existing_products > 0:
            print(f"⚠️  Database already contains {existing_products} products")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return

            # Clear existing data
            print("🗑️  Clearing existing data...")
            db.query(SalesRecord).delete()
            db.query(InventoryRecord).delete()
            db.query(Product).delete()
            db.commit()
            print("✅ Cleared existing data\n")

        # Seed data
        products = seed_products(db)
        seed_sales(db, products)
        seed_inventory(db, products)

        print("\n✨ Database seeding completed successfully!")
        print("\n📈 You can now:")
        print("   1. Start the API: python app/main.py")
        print("   2. Visit http://localhost:8000/docs")
        print("   3. Try the /api/v1/forecast/ endpoint")
        print("   4. Try the /api/v1/analytics/comprehensive endpoint")

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
