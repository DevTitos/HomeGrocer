from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

class InventoryViewSet(viewsets.ModelViewSet):
    """Manage inventory items"""
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(
            product__in=Product.objects.filter(
                # Filter by user's products (in real app, you'd have user field on Product)
                # For now, return all
            )
        )
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock items"""
        low_items = self.get_queryset().filter(is_low=True)
        serializer = self.get_serializer(low_items, many=True)
        return Response(serializer.data)
    
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
                source='MANUAL'
            )
            
            # Update inventory
            item.quantity -= quantity
            if item.quantity < 0:
                item.quantity = 0
            item.save()
            
            return Response({'message': 'Consumption recorded', 'new_quantity': item.quantity})
        except ValueError:
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """View predictions and generate new ones"""
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_predictions(self, request):
        """Generate predictions for low stock items"""
        # Simple prediction logic (to be replaced with actual ML)
        low_items = InventoryItem.objects.filter(is_low=True)
        
        predictions = []
        for item in low_items:
            # Simple rule: predict 7 days from now if quantity is below threshold
            prediction, created = Prediction.objects.get_or_create(
                product=item.product,
                user=request.user,
                defaults={
                    'predicted_quantity': item.min_threshold * 2,
                    'predicted_runout_date': timezone.now().date() + timedelta(days=7),
                    'confidence': 0.8,
                }
            )
            
            if created:
                predictions.append(prediction)
        
        serializer = self.get_serializer(predictions, many=True)
        return Response({
            'message': f'Generated {len(predictions)} predictions',
            'predictions': serializer.data
        })


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Manage shopping carts"""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to cart"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
            # For now, create a simple cart item without vendor product
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
                unit_price=0.00  # Would get from vendor in real implementation
            )
            
            # Recalculate total
            cart.total_amount = sum(item.total_price for item in cart.items.all())
            cart.save()
            
            return Response(CartItemSerializer(cart_item).data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def request_approval(self, request, pk=None):
        """Request approval for this cart"""
        cart = self.get_object()
        
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


class ApprovalViewSet(viewsets.ModelViewSet):
    """Manage approval requests"""
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an approval request"""
        approval = self.get_object()
        
        if approval.status != 'PENDING':
            return Response(
                {'error': 'Request already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval.status = 'APPROVED'
        approval.approved_by = request.user
        approval.reviewed_at = timezone.now()
        approval.save()
        
        # Update cart status
        approval.cart.status = 'APPROVED'
        approval.cart.save()
        
        return Response({'message': 'Approval granted'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View audit logs"""
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # In real app, filter by user permissions
        return self.queryset
    

@login_required
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html')

def login_view(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'login.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')

# Additional API endpoints for frontend
@api_view(['GET'])
def check_auth(request):
    """Check if user is authenticated"""
    return Response({'authenticated': request.user.is_authenticated})

@api_view(['GET'])
def get_ai_insights(request):
    """Get AI insights for dashboard"""
    if not request.user.is_authenticated:
        return Response({'error': 'Not authenticated'}, status=401)
    
    # Get low stock items
    low_items = InventoryItem.objects.filter(
        quantity__lte=models.F('min_threshold'),
        product__user=request.user
    )
    
    # Get most urgent prediction
    urgent_prediction = Prediction.objects.filter(
        user=request.user,
        predicted_runout_date__lte=timezone.now() + timedelta(days=3)
    ).first()
    
    insight = {
        'recommendation': {
            'title': 'Smart Recommendation',
            'message': 'All systems operational',
            'action': 'View Details'
        }
    }
    
    if urgent_prediction:
        insight['recommendation'] = {
            'title': 'Urgent Reorder Needed',
            'message': f'{urgent_prediction.product.name} will run out soon',
            'action': 'Reorder Now',
            'product_id': str(urgent_prediction.product.id),
            'prediction_id': str(urgent_prediction.id)
        }
    
    return Response(insight)

@api_view(['GET'])
def vendor_comparison(request):
    """Get vendor price comparison"""
    # This would integrate with Amazon/Walmart APIs
    vendors = [
        {
            'name': 'Amazon Fresh',
            'total_price': '87.45',
            'delivery_time': 'Tomorrow'
        },
        {
            'name': 'Walmart',
            'total_price': '92.30',
            'delivery_time': 'Today'
        }
    ]
    return Response(vendors)