from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
router.register(r'predictions', views.PredictionViewSet, basename='prediction')
router.register(r'carts', views.ShoppingCartViewSet, basename='cart')
router.register(r'approvals', views.ApprovalViewSet, basename='approval')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/check/', views.check_auth, name='check_auth'),
    path('ai_insights/', views.get_ai_insights, name='ai_insights'),
    path('vendors/comparison/', views.vendor_comparison, name='vendor_comparison'),
    path('carts/active/', views.ShoppingCartViewSet.as_view({'get': 'get_active_cart'}), name='active_cart'),
    path('carts/build_ai_cart/', views.ShoppingCartViewSet.as_view({'post': 'build_ai_cart'}), name='build_ai_cart'),
]