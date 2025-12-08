# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'predictions', views.PredictionViewSet, basename='prediction')
router.register(r'carts', views.ShoppingCartViewSet, basename='cart')
router.register(r'approvals', views.ApprovalViewSet, basename='approval')
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')
router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    # API Routes
    path('', include(router.urls)),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    
    # Inventory endpoints
    path('inventory/low_stock/', views.InventoryViewSet.as_view({'get': 'low_stock'}), name='inventory-low-stock'),
    path('inventory/stats/', views.InventoryViewSet.as_view({'get': 'stats'}), name='inventory-stats'),
    path('inventory/<uuid:pk>/consume/', views.InventoryViewSet.as_view({'post': 'consume'}), name='inventory-consume'),
    path('inventory/<uuid:pk>/restock/', views.InventoryViewSet.as_view({'post': 'restock'}), name='inventory-restock'),
    
    # Prediction endpoints
    path('predictions/generate/', views.PredictionViewSet.as_view({'post': 'generate'}), name='predictions-generate'),
    path('predictions/urgent/', views.PredictionViewSet.as_view({'get': 'urgent'}), name='predictions-urgent'),
    path('predictions/insights/', views.PredictionViewSet.as_view({'get': 'insights'}), name='predictions-insights'),
    path('predictions/<uuid:pk>/snooze/', views.PredictionViewSet.as_view({'post': 'snooze'}), name='prediction-snooze'),
    
    # Cart endpoints
    path('carts/active/', views.ShoppingCartViewSet.as_view({'get': 'active'}), name='cart-active'),
    path('carts/build_ai/', views.ShoppingCartViewSet.as_view({'post': 'build_ai'}), name='cart-build-ai'),
    path('carts/<uuid:pk>/add_item/', views.ShoppingCartViewSet.as_view({'post': 'add_item'}), name='cart-add-item'),
    path('carts/<uuid:pk>/remove_item/', views.ShoppingCartViewSet.as_view({'post': 'remove_item'}), name='cart-remove-item'),
    path('carts/<uuid:pk>/update_quantity/', views.ShoppingCartViewSet.as_view({'post': 'update_quantity'}), name='cart-update-quantity'),
    path('carts/<uuid:pk>/request_approval/', views.ShoppingCartViewSet.as_view({'post': 'request_approval'}), name='cart-request-approval'),
    path('carts/<uuid:pk>/clear/', views.ShoppingCartViewSet.as_view({'post': 'clear'}), name='cart-clear'),
    path('categories/popular/', views.CategoryViewSet.as_view({'get': 'popular'}), name='category-popular'),

    # Approval endpoints
    path('approvals/pending/', views.ApprovalViewSet.as_view({'get': 'pending'}), name='approvals-pending'),
    path('approvals/<uuid:pk>/approve/', views.ApprovalViewSet.as_view({'post': 'approve'}), name='approval-approve'),
    path('approvals/<uuid:pk>/reject/', views.ApprovalViewSet.as_view({'post': 'reject'}), name='approval-reject'),
    
    # Vendor endpoints
    path('vendors/comparison/', views.VendorViewSet.as_view({'get': 'comparison'}), name='vendor-comparison'),
    
    # Auth check
    path('auth/check/', views.check_auth, name='check-auth'),
]
