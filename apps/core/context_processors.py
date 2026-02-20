# apps/base/context_processors.py (crear si no existe)

def tenant_context(request):
    """Hace disponible la empresa actual en todos los templates"""
    return {
        'tenant': getattr(request, 'tenant', None),
        'empresa_actual': getattr(request, 'empresa', None),
    }