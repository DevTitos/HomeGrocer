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
    is_low = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = '__all__'


class ConsumptionPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumptionPattern
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Prediction
        fields = '__all__'


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'


class ShoppingCartSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShoppingCart
        fields = '__all__'
    
    def get_items_count(self, obj):
        return obj.items.count()


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = '__all__'


class ApprovalRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRule
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    cart_details = ShoppingCartSerializer(source='cart', read_only=True)
    
    class Meta:
        model = ApprovalRequest
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = '__all__'
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else 'System'