# core/views.py - Add HTML views
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def dashboard(request):
    """Render the main dashboard"""
    return render(request, 'dashboard.html')

def custom_logout(request):
    """Custom logout view"""
    logout(request)
    return redirect('login')
