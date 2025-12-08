# core/admin.py
from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'size', 'created_at']
    list_filter = ['category', 'brand']
    search_fields = ['name', 'brand', 'upc']
    ordering = ['name']

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'unit', 'min_threshold', 'expiry_date', 'location', 'is_low']
    list_filter = ['location', 'product__category']
    search_fields = ['product__name', 'product__brand']
    readonly_fields = ['is_low']
    ordering = ['product__name']

@admin.register(ConsumptionHistory)
class ConsumptionHistoryAdmin(admin.ModelAdmin):
    list_display = ['inventory_item', 'quantity_used', 'date', 'source']
    list_filter = ['source', 'date']
    search_fields = ['inventory_item__product__name']
    ordering = ['-date']

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'predicted_runout_date', 'confidence', 'is_active']
    list_filter = ['is_active', 'predicted_runout_date', 'user']
    search_fields = ['product__name']
    ordering = ['predicted_runout_date']

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_name', 'is_active']
    list_filter = ['is_active']
    ordering = ['name']

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'user']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'status', 'requested_by', 'requested_at', 'approved_by']
    list_filter = ['status', 'requested_at']
    readonly_fields = ['requested_at', 'reviewed_at']
    ordering = ['-requested_at']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'user', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    readonly_fields = ['timestamp']
    search_fields = ['user__username', 'model_name']
    ordering = ['-timestamp']