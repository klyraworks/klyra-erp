# apps/base/middleware/tenant_middleware.py
from threading import local
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

_thread_locals = local()


def get_current_empresa():
    """Obtiene la empresa del contexto actual del thread"""
    return getattr(_thread_locals, 'empresa', None)


def set_current_empresa(empresa):
    """Establece la empresa en el contexto actual del thread"""
    _thread_locals.empresa = empresa


def clear_current_empresa():
    """Limpia la empresa del contexto"""
    if hasattr(_thread_locals, 'empresa'):
        delattr(_thread_locals, 'empresa')


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware multi-tenant que:
    1. Detecta la empresa por subdominio
    2. Rechaza subdominios inexistentes
    3. No gestiona autenticación (eso va en las vistas)
    """

    def get_subdomain(self, request):
        """Extrae el subdominio del host"""
        host = request.get_host().split(':')[0]
        parts = host.split('.')

        # Validar estructura de dominio
        # Desarrollo: empresa1.local (2 partes)
        # Producción: empresa1.klyra.com (3 partes)
        if len(parts) >= 2:
            subdomain = parts[0]

            # Excluir subdominios reservados del sistema
            reserved = ['www', 'api', 'admin', 'static', 'media', 'localhost', '127']

            if subdomain not in reserved:
                return subdomain

        return None

    def process_request(self, request):
        """Establece la empresa al inicio del request"""
        from apps.core.models import Empresa

        subdomain = self.get_subdomain(request)

        # Bloquear acceso sin subdominio válido
        if not subdomain:
            return JsonResponse(
                {
                    'error': 'Acceso inválido',
                    'detail': 'Debe acceder mediante un subdominio válido (ej: empresa1.local:3000)'
                },
                status=400
            )

        # Buscar empresa por subdominio
        try:
            empresa = Empresa.objects.get(subdominio=subdomain, is_active=True)
        except Empresa.DoesNotExist:
            return JsonResponse(
                {
                    'error': 'Empresa no encontrada',
                    'detail': f'El subdominio "{subdomain}" no existe o está inactivo',
                    'subdomain': subdomain
                },
                status=404
            )

        # Asignar empresa al contexto
        set_current_empresa(empresa)
        request.empresa = empresa
        request.tenant = empresa

    def process_response(self, request, response):
        """Limpia el contexto al final del request"""
        clear_current_empresa()
        return response

    def process_exception(self, request, exception):
        """Limpia el contexto en caso de excepción"""
        clear_current_empresa()
        return None