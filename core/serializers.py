# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'


class InventoryItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    is_low = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        model = InventoryItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ConsumptionHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory_item.product.name', read_only=True)
    
    class Meta:
        model = ConsumptionHistory
        fields = '__all__'


class ConsumptionPatternSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ConsumptionPattern
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    days_until_runout = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Prediction
        fields = '__all__'


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'


class VendorProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = VendorProduct
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = '__all__'


class ShoppingCartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShoppingCart
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ApprovalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRule
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    cart_details = ShoppingCartSerializer(source='cart', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = ApprovalRequest
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'