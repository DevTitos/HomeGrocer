# core/urls.py
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
    path('api/', include(router.urls)),
]