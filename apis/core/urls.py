# urls.py - Módulo Base
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apis.core.EnvioEmail import EnvioEmail
from apis.core.ciudad.ciudad_viewset import CiudadViewSet
from apis.core.UserViewset import get_current_user

router = DefaultRouter()
router.register('enviaremail', EnvioEmail, basename='enviaremail')  # Agregado basename
router.register('ciudades', CiudadViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/user/me/', get_current_user, name='current_user'),
]