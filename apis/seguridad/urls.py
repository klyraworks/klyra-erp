# urls.py - Módulo SEGURIDAD
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.seguridad.empleado.empleado_viewset import EmpleadoViewSet
from apis.seguridad.activacion.activacion_views import VerificarTokenView, ActivarCuentaView
from apis.seguridad.rol.rol_viewset import RolViewSet

router = DefaultRouter()
router.register('empleados', EmpleadoViewSet, basename='empleado')
router.register('roles', RolViewSet, basename='rol')

urlpatterns = [
    path('api/seguridad/', include(router.urls)),
    path('api/seguridad/verificar-token/', VerificarTokenView.as_view(), name='verificar-token'),
    path('api/seguridad/activar-cuenta/', ActivarCuentaView.as_view(), name='activar-cuenta'),
]