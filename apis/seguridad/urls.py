# urls.py - Módulo SEGURIDAD
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.seguridad.empleado.empleado_viewset import EmpleadoViewSet
from apis.seguridad.activacion.activacion_views import VerificarTokenView, ActivarCuentaView

router = DefaultRouter()
router.register('empleados', EmpleadoViewSet, basename='empleado')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/verificar-token/', VerificarTokenView.as_view(), name='verificar-token'),
    path('api/activar-cuenta/', ActivarCuentaView.as_view(), name='activar-cuenta'),
]