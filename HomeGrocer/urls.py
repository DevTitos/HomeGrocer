from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import login_view, logout_view
from django.contrib.auth import views as auth_views
from .views import dashboard, custom_logout
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('', dashboard, name='dashboard'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
]