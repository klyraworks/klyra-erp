# urls.py - Módulo RRHH
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.rrhh.departamento.departamento_viewset import DepartamentoViewSet


router = DefaultRouter()
router.register('departamentos', DepartamentoViewSet, basename='departamentos')

urlpatterns = [
    path('api/', include(router.urls)),
]
