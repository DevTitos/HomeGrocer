# create_test_data.py
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeGrocer.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import *

def create_test_data():
    print("Creating test data...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_active': True,
            'is_staff': False
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created user: {user.username}")
    
    # Create categories
    categories = [
        ('Dairy', 'Milk, cheese, yogurt, eggs'),
        ('Produce', 'Fruits and vegetables'),
        ('Meat', 'Beef, chicken, pork, fish'),
        ('Bakery', 'Bread, pastries, baked goods'),
        ('Pantry', 'Dry goods, canned food, spices'),
        ('Beverages', 'Drinks, juices, soda'),
        ('Frozen', 'Frozen foods'),
    ]
    
    for name, desc in categories:
        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        if created:
            print(f"Created category: {name}")
    
    # Create products
    dairy = Category.objects.get(name='Dairy')
    produce = Category.objects.get(name='Produce')
    bakery = Category.objects.get(name='Bakery')
    pantry = Category.objects.get(name='Pantry')
    
    products = [
        {'name': 'Milk', 'brand': 'Organic Valley', 'category': dairy, 'size': '1L', 'unit': 'L'},
        {'name': 'Eggs', 'brand': 'Happy Hens', 'category': dairy, 'size': '12 count', 'unit': 'each'},
        {'name': 'Bread', 'brand': 'Local Bakery', 'category': bakery, 'size': '500g', 'unit': 'loaf'},
        {'name': 'Apples', 'brand': 'Fresh Farms', 'category': produce, 'size': '1kg', 'unit': 'kg'},
        {'name': 'Coffee', 'brand': 'Premium Roast', 'category': pantry, 'size': '500g', 'unit': 'g'},
        {'name': 'Rice', 'brand': 'Basmati', 'category': pantry, 'size': '2kg', 'unit': 'kg'},
        {'name': 'Cheese', 'brand': 'Cheddar', 'category': dairy, 'size': '200g', 'unit': 'g'},
        {'name': 'Yogurt', 'brand': 'Greek Style', 'category': dairy, 'size': '500g', 'unit': 'g'},
        {'name': 'Bananas', 'brand': None, 'category': produce, 'size': 'bunch', 'unit': 'each'},
        {'name': 'Pasta', 'brand': 'Italian', 'category': pantry, 'size': '500g', 'unit': 'g'},
    ]
    
    for prod_data in products:
        product, created = Product.objects.get_or_create(
            name=prod_data['name'],
            brand=prod_data['brand'] or '',
            defaults=prod_data
        )
        if created:
            print(f"Created product: {product.name}")
    
    # Create inventory items (some low stock)
    today = datetime.now().date()
    
    inventory_data = [
        ('Milk', 0.5, 'L', 1.0, 'Fridge', today + timedelta(days=5)),  # Low stock
        ('Eggs', 4, 'each', 6, 'Fridge', today + timedelta(days=14)),  # Low stock
        ('Bread', 2, 'loaf', 1, 'Pantry', today + timedelta(days=3)),  # Good
        ('Apples', 3, 'kg', 1, 'Fruit Bowl', today + timedelta(days=7)),  # Good
        ('Coffee', 0.2, 'g', 100, 'Pantry', today + timedelta(days=30)),  # Low stock
        ('Rice', 5, 'kg', 2, 'Pantry', None),  # Good
        ('Cheese', 0.3, 'g', 200, 'Fridge', today + timedelta(days=10)),  # Low stock
        ('Yogurt', 1, 'g', 500, 'Fridge', today + timedelta(days=2)),  # Good but expiring
        ('Bananas', 2, 'each', 1, 'Counter', today + timedelta(days=2)),  # Expiring
        ('Pasta', 0.8, 'g', 500, 'Pantry', today + timedelta(days=365)),  # Low stock
    ]
    
    for product_name, qty, unit, threshold, location, expiry in inventory_data:
        product = Product.objects.get(name=product_name)
        item, created = InventoryItem.objects.get_or_create(
            product=product,
            defaults={
                'quantity': qty,
                'unit': unit,
                'min_threshold': threshold,
                'location': location,
                'expiry_date': expiry
            }
        )
        if created:
            print(f"Created inventory: {product.name} ({qty} {unit})")
    
    # Create some predictions
    print("\nGenerating predictions...")
    for item in InventoryItem.objects.filter(quantity__lte=F('min_threshold')):
        runout_date = today + timedelta(days=2 if float(item.quantity) == 0 else 7)
        prediction, created = Prediction.objects.get_or_create(
            product=item.product,
            user=user,
            defaults={
                'predicted_quantity': float(item.min_threshold) * 2,
                'predicted_runout_date': runout_date,
                'confidence': 0.8,
                'is_active': True
            }
        )
        if created:
            print(f"Created prediction: {item.product.name} runs out in {runout_date}")
    
    # Create vendors
    vendors = [
        ('Amazon Fresh', 'amazon', 'https://amazon.com'),
        ('Walmart', 'walmart', 'https://walmart.com'),
        ('Target', 'target', 'https://target.com'),
    ]
    
    for name, api_name, url in vendors:
        vendor, created = Vendor.objects.get_or_create(
            name=name,
            defaults={'api_name': api_name, 'base_url': url}
        )
        if created:
            print(f"Created vendor: {name}")
    
    print("\nTest data created successfully!")
    print("\nLogin credentials:")
    print("  Username: testuser")
    print("  Password: testpass123")
    print("\nAdmin credentials (if created):")
    print("  Username: admin")
    print("  Password: (what you set during createsuperuser)")

if __name__ == '__main__':
    create_test_data()