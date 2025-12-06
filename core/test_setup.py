import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeGrocer.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import *

# Create test data
def create_test_data():
    # Create user
    user, _ = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Create category
    category, _ = Category.objects.get_or_create(
        name='Dairy',
        defaults={'description': 'Dairy products'}
    )
    
    # Create product
    product, _ = Product.objects.get_or_create(
        name='Milk',
        brand='Generic',
        category=category,
        defaults={'size': '1L', 'unit': 'L'}
    )
    
    # Create inventory item
    inventory, _ = InventoryItem.objects.get_or_create(
        product=product,
        defaults={
            'quantity': 0.5,
            'unit': 'L',
            'min_threshold': 1.0,
            'location': 'Fridge'
        }
    )
    
    print(f"Created test data:")
    print(f"  User: {user.username}")
    print(f"  Category: {category.name}")
    print(f"  Product: {product.name}")
    print(f"  Inventory: {inventory.quantity} {inventory.unit} (Low: {inventory.is_low})")
    
    return user, product, inventory

if __name__ == '__main__':
    create_test_data()