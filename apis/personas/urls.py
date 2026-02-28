# urls.py - Módulo Inventario
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.personas.cliente_viewset import ClienteViewSet


router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
urlpatterns = [
    path('api/personas/', include(router.urls)),
]
