# core/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Q, F, Count, Sum
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging

from .models import *
from .serializers import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class InventoryViewSet(viewsets.ModelViewSet):
    """Manage inventory items"""
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'product__brand', 'location']
    ordering_fields = ['quantity', 'expiry_date', 'created_at']
    
    def get_queryset(self):
        # In production, filter by user. For demo, show all
        return InventoryItem.objects.select_related('product', 'product__category').all()
    
    def perform_create(self, serializer):
        # Set default values if not provided
        data = serializer.validated_data
        if 'unit' not in data or not data['unit']:
            data['unit'] = data['product'].unit if data['product'].unit else 'each'
        
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock items"""
        queryset = self.get_queryset()
        
        # Calculate low stock manually
        low_items = []
        for item in queryset:
            if item.quantity <= item.min_threshold:
                low_items.append(item)
        
        # Paginate results
        page = self.paginate_queryset(low_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(low_items, many=True)
        return Response({
            'count': len(low_items),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def consume(self, request, pk=None):
        """Consume some quantity of an item"""
        item = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create consumption history
            ConsumptionHistory.objects.create(
                inventory_item=item,
                quantity_used=quantity,
                date=timezone.now().date(),
                source='MANUAL',
                notes=request.data.get('notes', '')
            )
            
            # Update inventory
            item.quantity -= quantity
            if item.quantity < 0:
                item.quantity = 0
            item.save()
            
            # Check if we need to create a prediction
            if item.quantity <= item.min_threshold:
                # Create or update prediction
                prediction, created = Prediction.objects.get_or_create(
                    product=item.product,
                    user=request.user,
                    defaults={
                        'predicted_quantity': float(item.min_threshold) * 2,
                        'predicted_runout_date': timezone.now().date() + timedelta(days=2),
                        'confidence': 0.8,
                        'is_active': True
                    }
                )
                if not created:
                    prediction.predicted_runout_date = timezone.now().date() + timedelta(days=2)
                    prediction.save()
            
            return Response({
                'message': 'Consumption recorded', 
                'new_quantity': item.quantity,
                'is_low': item.quantity <= item.min_threshold
            })
        except ValueError:
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        """Restock an item"""
        item = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.quantity += quantity
            item.save()
            
            # Deactivate any active predictions for this product
            Prediction.objects.filter(
                product=item.product,
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            return Response({
                'message': 'Restocked successfully',
                'new_quantity': item.quantity,
                'is_low': item.quantity <= item.min_threshold
            })
        except ValueError:
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get inventory statistics"""
        queryset = self.get_queryset()
        
        # Count low stock items
        low_stock_count = 0
        for item in queryset:
            if item.quantity <= item.min_threshold:
                low_stock_count += 1
        
        # Calculate totals
        total_items = queryset.count()
        total_value = sum(float(item.quantity) * 5 for item in queryset)  # Demo: $5 per unit
        
        # Get items expiring soon (within 7 days)
        soon = timezone.now().date() + timedelta(days=7)
        expiring_soon = queryset.filter(
            expiry_date__isnull=False,
            expiry_date__lte=soon
        ).count()
        
        # Get category breakdown
        categories = {}
        for item in queryset:
            category = item.product.category.name if item.product.category else 'Uncategorized'
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'low_stock': 0,
                    'total_quantity': 0
                }
            
            categories[category]['count'] += 1
            categories[category]['total_quantity'] += float(item.quantity)
            if item.quantity <= item.min_threshold:
                categories[category]['low_stock'] += 1
        
        return Response({
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'expiring_soon': expiring_soon,
            'total_value': total_value,
            'categories': categories
        })


class ProductViewSet(viewsets.ModelViewSet):
    """Manage products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'brand', 'upc']
    
    def get_queryset(self):
        return Product.objects.select_related('category').all()

from .mcp_intergration import mcp_client

# Update the PredictionViewSet
class PredictionViewSet(viewsets.ModelViewSet):
    """View predictions with MCP integration"""
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        return Prediction.objects.filter(
            is_active=True
        ).select_related('product', 'product__category').order_by('predicted_runout_date')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate predictions using MCP"""
        # Get inventory items
        inventory_items = InventoryItem.objects.select_related('product').all()
        
        predictions = []
        for item in inventory_items:
            # Get consumption history
            history = ConsumptionHistory.objects.filter(
                inventory_item=item
            ).order_by('-date')[:30]  # Last 30 days
            
            historical_data = [
                {
                    'date': h.date.isoformat(),
                    'quantity': float(h.quantity_used),
                    'source': h.source
                }
                for h in history
            ]
            
            # Use MCP for prediction
            mcp_prediction = mcp_client.predict_consumption(
                product_id=str(item.product.id),
                historical_data=historical_data,
                user_context={
                    'household_size': 1,  # Would come from user profile
                    'location': 'home',   # Would come from settings
                    'preferences': {}     # Would come from user preferences
                }
            )
            
            # Create or update prediction
            existing = Prediction.objects.filter(
                product=item.product,
                is_active=True
            ).first()
            
            if existing:
                existing.predicted_quantity = mcp_prediction.get('recommended_quantity', 2)
                existing.predicted_runout_date = datetime.now().date() + timedelta(
                    days=mcp_prediction.get('days_until_runout', 7)
                )
                existing.confidence = mcp_prediction.get('confidence', 0.8)
                existing.save()
                predictions.append(existing)
            else:
                prediction = Prediction.objects.create(
                    product=item.product,
                    user=request.user,
                    predicted_quantity=mcp_prediction.get('recommended_quantity', 2),
                    predicted_runout_date=datetime.now().date() + timedelta(
                        days=mcp_prediction.get('days_until_runout', 7)
                    ),
                    confidence=mcp_prediction.get('confidence', 0.8),
                    is_active=True
                )
                predictions.append(prediction)
        
        serializer = self.get_serializer(predictions, many=True)
        return Response({
            'message': f'Generated {len(predictions)} predictions using {"MCP" if mcp_client.is_available else "fallback ML"}',
            'predictions': serializer.data,
            'count': len(predictions),
            'mcp_enabled': mcp_client.is_available
        })
    
    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get AI insights with MCP recommendations - FIXED VERSION"""
        try:
            # Get inventory for recommendations
            inventory_items = InventoryItem.objects.select_related('product').all()
            
            inventory_data = []
            for item in inventory_items:
                inventory_data.append({
                    'product_id': str(item.product.id),
                    'product_name': item.product.name,
                    'quantity': float(item.quantity),
                    'min_threshold': float(item.min_threshold),
                    'category': item.product.category.name if item.product.category else 'Uncategorized',
                    'last_updated': item.updated_at.isoformat()
                })
            
            # Get MCP recommendations
            mcp_recommendations = mcp_client.generate_recommendations(
                user_id=str(request.user.id),
                inventory=inventory_data,
                budget=request.GET.get('budget', None),
                preferences={}  # Would come from user preferences
            )
            
            # Get the most urgent recommendation
            if mcp_recommendations:
                most_urgent = mcp_recommendations[0]
                
                # Safely get days_until
                urgency_score = most_urgent.get('urgency_score', 0.5)
                days_until = int(urgency_score * 10)  # Convert urgency to days estimate
                
                return Response({
                    'recommendation': {
                        'title': f"{most_urgent.get('priority', 'MEDIUM').upper()} PRIORITY: {most_urgent.get('product_name', 'Item')}",
                        'message': most_urgent.get('reason', 'Needs restocking'),
                        'action': 'Add to Cart',
                        'product_id': most_urgent.get('product_id', ''),
                        'product_name': most_urgent.get('product_name', 'Product'),
                        'days_until': days_until,
                        'confidence': 0.85,
                        'mcp_generated': mcp_client.is_available
                    },
                    'all_recommendations': mcp_recommendations[:5],  # Top 5
                    'total_recommendations': len(mcp_recommendations)
                })
            
            # Fallback if no recommendations
            return Response({
                'recommendation': {
                    'title': 'Inventory Status Good',
                    'message': 'All items are well stocked. No urgent recommendations.',
                    'action': 'Run Analysis',
                    'mcp_generated': False
                },
                'total_recommendations': 0
            })
            
        except Exception as e:
            logger.error(f"Error in insights endpoint: {e}")
            return Response({
                'recommendation': {
                    'title': 'System Error',
                    'message': 'Unable to generate insights at this time.',
                    'action': 'Try Again',
                    'mcp_generated': False
                },
                'error': str(e)
            }, status=500)

class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Manage shopping carts"""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShoppingCart.objects.filter(
            user=self.request.user
        ).prefetch_related('items', 'items__product').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active cart (most recent DRAFT or READY cart)"""
        active_cart = self.get_queryset().filter(
            status__in=['DRAFT', 'READY']
        ).order_by('-created_at').first()
        
        if active_cart:
            serializer = self.get_serializer(active_cart)
            return Response(serializer.data)
        else:
            # Create a new cart
            cart = ShoppingCart.objects.create(
                user=request.user,
                status='DRAFT'
            )
            serializer = self.get_serializer(cart)
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to cart"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Check if item already exists in cart
            existing_item = cart.items.filter(product=product).first()
            
            if existing_item:
                existing_item.quantity += float(quantity)
                existing_item.save()
                cart_item = existing_item
            else:
                # Get vendor product price if available, otherwise use default
                vendor_product = VendorProduct.objects.filter(
                    product=product,
                    in_stock=True
                ).first()
                
                unit_price = vendor_product.current_price if vendor_product else 4.99
                
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )
            
            # Recalculate total
            cart.update_total()
            
            return Response(CartItemSerializer(cart_item).data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove item from cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()
            
            # Recalculate total
            cart.update_total()
            
            return Response({'message': 'Item removed from cart'})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """Update item quantity in cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.quantity = float(quantity)
            if cart_item.quantity <= 0:
                cart_item.delete()
                message = 'Item removed from cart'
            else:
                cart_item.save()
                message = 'Quantity updated'
            
            # Recalculate total
            cart.update_total()
            
            return Response({'message': message})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def request_approval(self, request, pk=None):
        """Request approval for this cart"""
        cart = self.get_object()
        
        # Check if cart has items
        if cart.items.count() == 0:
            return Response(
                {'error': 'Cannot request approval for empty cart'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if approval already exists
        if hasattr(cart, 'approval_request'):
            return Response(
                {'error': 'Approval already requested'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create approval request
        approval = ApprovalRequest.objects.create(
            cart=cart,
            requested_by=request.user,
            status='PENDING'
        )
        
        # Update cart status
        cart.status = 'PENDING_APPROVAL'
        cart.save()
        
        return Response(ApprovalRequestSerializer(approval).data)
    
    @action(detail=False, methods=['post'])
    def build_ai(self, request):
        """Build cart using MCP recommendations"""
        # Get MCP recommendations
        inventory_items = InventoryItem.objects.select_related('product').all()
        
        inventory_data = []
        for item in inventory_items:
            inventory_data.append({
                'product_id': str(item.product.id),
                'product_name': item.product.name,
                'quantity': float(item.quantity),
                'min_threshold': float(item.min_threshold),
                'category': item.product.category.name if item.product.category else 'Uncategorized'
            })
        
        mcp_recommendations = mcp_client.generate_recommendations(
            user_id=str(request.user.id),
            inventory=inventory_data,
            budget=request.data.get('budget'),
            preferences=request.data.get('preferences', {})
        )
        
        # Get or create active cart
        active_cart = self.get_queryset().filter(
            status__in=['DRAFT', 'READY']
        ).order_by('-created_at').first()
        
        if not active_cart:
            active_cart = ShoppingCart.objects.create(
                user=request.user,
                status='DRAFT'
            )
        
        added_items = []
        for recommendation in mcp_recommendations[:10]:  # Limit to 10 items
            try:
                product = Product.objects.get(id=recommendation['product_id'])
                
                # Check if already in cart
                if not active_cart.items.filter(product=product).exists():
                    cart_item = CartItem.objects.create(
                        cart=active_cart,
                        product=product,
                        quantity=recommendation['recommended_quantity'],
                        unit_price=recommendation.get('estimated_cost', 4.99)  # From MCP
                    )
                    added_items.append({
                        'name': product.name,
                        'quantity': cart_item.quantity,
                        'price': cart_item.unit_price
                    })
            except Product.DoesNotExist:
                continue
            except Exception as e:
                debugLog(f"Error adding {recommendation.get('product_name')}: {e}")
        
        # Update cart total
        active_cart.update_total()
        
        return Response({
            'message': f'Added {len(added_items)} items to cart using {"MCP" if mcp_client.is_available else "AI"}',
            'items': added_items,
            'cart_id': str(active_cart.id),
            'cart_total': active_cart.total_amount,
            'mcp_enabled': mcp_client.is_available
        })
    
    @action(detail=False, methods=['post'])
    def optimize(self, request):
        """Optimize cart using MCP"""
        cart_id = request.data.get('cart_id')
        
        try:
            cart = ShoppingCart.objects.get(id=cart_id, user=request.user)
            
            # Get cart items
            cart_items = []
            for item in cart.items.all():
                cart_items.append({
                    'product_id': str(item.product.id),
                    'product_name': item.product.name,
                    'quantity': float(item.quantity),
                    'unit_price': float(item.unit_price)
                })
            
            # Get vendor data
            vendors_response = self._get_vendor_data(cart_items)
            vendors = vendors_response.get('vendors', [])
            
            # Use MCP for optimization
            constraints = {
                'max_budget': request.data.get('max_budget'),
                'delivery_deadline': request.data.get('delivery_deadline')
            }
            
            optimization = mcp_client.optimize_cart(cart_items, vendors, constraints)
            
            return Response({
                'optimization': optimization,
                'mcp_enabled': mcp_client.is_available
            })
            
        except ShoppingCart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.items.all().delete()
        cart.update_total()
        
        return Response({'message': 'Cart cleared'})


class ApprovalViewSet(viewsets.ModelViewSet):
    """Manage approval requests"""
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        # Show approvals for carts owned by user or where user can approve
        return ApprovalRequest.objects.filter(
            Q(cart__user=self.request.user) | Q(requested_by=self.request.user)
        ).select_related('cart', 'requested_by', 'approved_by').order_by('-requested_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an approval request"""
        approval = self.get_object()
        
        if approval.status != 'PENDING':
            return Response(
                {'error': 'Request already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval.approve(request.user, request.data.get('notes', ''))
        return Response({'message': 'Approval granted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an approval request"""
        approval = self.get_object()
        
        if approval.status != 'PENDING':
            return Response(
                {'error': 'Request already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval.reject(request.user, request.data.get('notes', ''))
        return Response({'message': 'Approval rejected'})
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending approval requests"""
        pending = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending, many=True)
        return Response({
            'count': pending.count(),
            'results': serializer.data
        })


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """Manage vendors"""
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """Get vendor price comparison for current cart"""
        # Get active cart
        active_cart = ShoppingCart.objects.filter(
            user=request.user,
            status__in=['DRAFT', 'READY', 'PENDING_APPROVAL']
        ).order_by('-created_at').first()
        
        if not active_cart or active_cart.items.count() == 0:
            return Response({
                'message': 'No active cart with items',
                'vendors': []
            })
        
        # Mock vendor data - in production, this would query real APIs
        vendors = [
            {
                'id': 'amazon',
                'name': 'Amazon Fresh',
                'logo': 'amazon',
                'total_price': '87.45',
                'delivery_time': 'Tomorrow',
                'delivery_fee': 'Free',
                'service_fee': '0.00',
                'total_with_fees': '87.45',
                'items_available': active_cart.items.count(),
                'estimated_savings': '12%'
            },
            {
                'id': 'walmart',
                'name': 'Walmart',
                'logo': 'walmart',
                'total_price': '92.30',
                'delivery_time': 'Today',
                'delivery_fee': '7.95',
                'service_fee': '2.50',
                'total_with_fees': '102.75',
                'items_available': active_cart.items.count() - 1,
                'estimated_savings': '5%'
            },
            {
                'id': 'target',
                'name': 'Target',
                'logo': 'target',
                'total_price': '89.75',
                'delivery_time': '2 days',
                'delivery_fee': '9.99',
                'service_fee': '0.00',
                'total_with_fees': '99.74',
                'items_available': active_cart.items.count(),
                'estimated_savings': '8%'
            }
        ]
        
        return Response({
            'cart_id': str(active_cart.id),
            'cart_total': active_cart.total_amount,
            'vendors': vendors
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View audit logs"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        # Show logs for user's actions
        return AuditLog.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')


class DashboardView(APIView):
    """Dashboard overview data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get inventory stats
        inventory_items = InventoryItem.objects.select_related('product').all()
        low_stock_count = 0
        for item in inventory_items:
            if item.quantity <= item.min_threshold:
                low_stock_count += 1
        
        # Get predictions
        predictions = Prediction.objects.filter(is_active=True).count()
        
        # Get pending carts
        pending_carts = ShoppingCart.objects.filter(
            status='PENDING_APPROVAL'
        ).count()
        
        # Get pending approvals
        pending_approvals = ApprovalRequest.objects.filter(
            status='PENDING'
        ).count()
        
        # Calculate monthly spend (demo)
        monthly_spend = 247.50
        
        # Get recent consumption
        recent_consumption = ConsumptionHistory.objects.all()[:5]
        consumption_data = ConsumptionHistorySerializer(recent_consumption, many=True).data
        
        return Response({
            'stats': {
                'low_stock': low_stock_count,
                'predictions': predictions,
                'pending_carts': pending_carts,
                'pending_approvals': pending_approvals,
                'monthly_spend': monthly_spend
            },
            'recent_consumption': consumption_data,
            'ai_ready': True
        })


@api_view(['GET'])
def check_auth(request):
    """Check if user is authenticated"""
    return Response({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None
    })


class CategoryViewSet(viewsets.ModelViewSet):
    """Manage categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular categories based on inventory"""
        categories = Category.objects.annotate(
            product_count=Count('products'),
            inventory_count=Count('products__inventory_items')
        ).order_by('-inventory_count', '-product_count')[:10]
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import redirect

def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def dashboard_view(request):
    """Render the main dashboard"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'dashboard.html')

def custom_logout(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')