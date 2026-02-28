# urls.py - Módulo RRHH
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.rrhh.departamento.departamento_viewset import DepartamentoViewSet
from apis.rrhh.puesto.puesto_viewset import PuestoViewSet


router = DefaultRouter()
router.register('departamentos', DepartamentoViewSet, basename='departamento')
router.register('puestos', PuestoViewSet, basename='puesto')

urlpatterns = [
    path('api/rrhh/', include(router.urls)),
]
