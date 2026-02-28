"""
URL configuration for Klyra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Importar las nuevas vistas de autenticación con sesiones
from apis.auth.views import LoginView, LogoutView, CheckAuthView, UserInfoView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Documentación API
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),

    # Autenticación con sesiones (reemplaza JWT)
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/check/', CheckAuthView.as_view(), name='check-auth'),
    path('api/auth/me/', UserInfoView.as_view(), name='user-info'),

    # APIS
    path('', include('apis.core.urls')),
    path('', include('apis.seguridad.urls')),
    path('', include('apis.ventas.urls')),
    path('', include('apis.inventario.urls')),
    path('', include('apis.rrhh.urls')),
    path('', include('apis.personas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
