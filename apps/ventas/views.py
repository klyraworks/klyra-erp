from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# @login_required
def ventas_debug_dashboard(request):
    """Vista para el panel de pruebas de ventas"""
    return render(request, 'ventas/debug_dashboard.html')