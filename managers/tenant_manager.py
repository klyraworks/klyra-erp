# managers/tenant_manager.py
from django.db import models
from apps.core.middleware.tenant_middleware import get_current_empresa


class TenantManager(models.Manager):
    """
    Manager que filtra automáticamente por empresa.
    SIEMPRE retorna solo los datos de la empresa actual.
    """

    def get_queryset(self):
        """Filtra automáticamente por empresa del contexto"""
        queryset = super().get_queryset()
        empresa = get_current_empresa()

        if empresa:
            return queryset.filter(empresa=empresa)

        # Si no hay empresa en contexto, retornar queryset vacío por seguridad
        return queryset.none()

    def all_companies(self):
        """
        Para casos donde necesites ver TODAS las empresas.
        Usar SOLO en admin o reportes de superusuario.
        """
        return super().get_queryset()


class TenantQuerySet(models.QuerySet):
    """QuerySet personalizado para operaciones bulk"""

    def delete(self):
        """Soft delete en lugar de hard delete"""
        return self.update(is_active=False)

    def hard_delete(self):
        """Hard delete real (usar con cuidado)"""
        return super().delete()