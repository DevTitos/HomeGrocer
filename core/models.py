# core/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Category(models.Model):
    """Product categories (e.g., Dairy, Produce, Meat)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Master product catalog"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    upc = models.CharField(max_length=20, blank=True, verbose_name="UPC/Barcode")
    size = models.CharField(max_length=50, blank=True)  # e.g., "500g", "1L"
    unit = models.CharField(max_length=20, blank=True)  # e.g., "g", "ml", "each"
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'brand', 'size']
    
    def __str__(self):
        return f"{self.name} ({self.brand}) - {self.size}"


class InventoryItem(models.Model):
    """Current household inventory items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # Override product unit if needed
    purchase_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    min_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    location = models.CharField(max_length=100, blank=True)  # e.g., "Fridge", "Pantry"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.unit}"
    
    @property
    def is_low(self):
        return self.quantity <= self.min_threshold


class ConsumptionHistory(models.Model):
    """Track product consumption over time"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='consumption_history')
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    source = models.CharField(max_length=50, choices=[
        ('MANUAL', 'Manual Entry'),
        ('RECEIPT', 'Receipt OCR'),
        ('API', 'Smart Appliance API'),
        ('PREDICTION', 'ML Prediction'),
    ])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class ConsumptionPattern(models.Model):
    """Store ML consumption patterns for products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='patterns')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Pattern data (simplified ML features)
    avg_daily_consumption = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    weekly_pattern = models.JSONField(default=dict)  # e.g., {"monday": 1.2, "tuesday": 0.8}
    seasonality_factor = models.JSONField(default=dict)  # e.g., {"summer": 1.1, "winter": 0.9}
    lead_time_days = models.IntegerField(default=2)  # Days to reorder before running out
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    
    last_trained = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'user']


class Prediction(models.Model):
    """Store ML predictions for reordering"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    predicted_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_runout_date = models.DateField()
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Prediction: {self.product.name} - Runout: {self.predicted_runout_date}"
    

class Vendor(models.Model):
    """Supported vendors (Amazon, Walmart, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    api_name = models.CharField(max_length=50)  # e.g., "amazon", "walmart"
    base_url = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)  # Encrypted in real implementation
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class VendorProduct(models.Model):
    """Link our products to vendor-specific products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='vendor_products')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    vendor_product_id = models.CharField(max_length=100)  # Vendor's product ID
    vendor_product_name = models.CharField(max_length=200)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField()
    in_stock = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'vendor']
    
    def __str__(self):
        return f"{self.product.name} on {self.vendor.name}"


class ShoppingCart(models.Model):
    """Shopping cart for automatic orders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft - Building'),
        ('READY', 'Ready for Review'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Order Placed'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery = models.DateField(null=True, blank=True)
    spend_cap = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart #{self.id.hex[:8]} - {self.get_status_display()}"


class CartItem(models.Model):
    """Items in a shopping cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    vendor_product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    is_substitution = models.BooleanField(default=False)
    original_product = models.ForeignKey(Product, on_delete=models.SET_NULL, 
                                         null=True, blank=True, 
                                         related_name='substituted_items')
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    

class ApprovalRule(models.Model):
    """Rules for automatic approval"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_rules')
    
    RULE_TYPE_CHOICES = [
        ('AMOUNT', 'Maximum Amount'),
        ('CATEGORY', 'Category Allowlist'),
        ('VENDOR', 'Vendor Allowlist'),
        ('ITEM', 'Item Allowlist'),
    ]
    
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    
    # Condition fields (store based on rule_type)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    # Action
    auto_approve = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    
    priority = models.IntegerField(default=0)  # Lower number = higher priority
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ApprovalRequest(models.Model):
    """Approval requests for shopping carts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.OneToOneField(ShoppingCart, on_delete=models.CASCADE, related_name='approval_request')
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('MODIFIED', 'Modified and Approved'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approvals_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approvals_granted')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Approval for Cart #{self.cart.id.hex[:8]}"
    

class AuditLog(models.Model):
    """Comprehensive audit trail for all actions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('ORDER', 'Place Order'),
        ('PREDICT', 'Make Prediction'),
        ('SYNC', 'Sync with Vendor'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)  # Which model was affected
    object_id = models.UUIDField()  # ID of affected object
    old_value = models.JSONField(null=True, blank=True)  # Store previous state
    new_value = models.JSONField(null=True, blank=True)  # Store new state
    changes = models.JSONField(null=True, blank=True)  # Diff between old and new
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.model_name} by {self.user}"