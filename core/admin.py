from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'size', 'created_at']
    list_filter = ['category', 'brand']
    search_fields = ['name', 'brand', 'upc']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'unit', 'min_threshold', 'location', 'expiry_date']
    list_filter = ['location', 'product__category']
    search_fields = ['product__name', 'product__brand']
    actions = ['mark_as_consumed']
    
    def mark_as_consumed(self, request, queryset):
        for item in queryset:
            item.quantity = 0
            item.save()
        self.message_user(request, f"Marked {queryset.count()} items as consumed")


@admin.register(ConsumptionPattern)
class ConsumptionPatternAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'avg_daily_consumption', 'lead_time_days', 'last_trained']
    list_filter = ['user']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'predicted_runout_date', 'confidence', 'created_at']
    list_filter = ['user', 'predicted_runout_date']


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_name', 'is_active', 'created_at']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vendor', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'vendor', 'user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'status', 'requested_by', 'requested_at', 'approved_by']
    list_filter = ['status', 'requested_at']
    readonly_fields = ['requested_at', 'reviewed_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'user', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    readonly_fields = ['timestamp']
    search_fields = ['user__username', 'model_name', 'object_id']