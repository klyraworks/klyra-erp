# apis/core/ViewSetBase.py
import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.seguridad.models import Empleado


logger = logging.getLogger('apps.base')


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet base con filtrado automático por tenant/empresa.
    Todos los ViewSets del sistema deben heredar de esta clase.

    Funcionalidades:
    - Filtrado automático por empresa
    - Validación de empleado activo
    - Soft delete automático
    - Asignación automática de created_by/updated_by
    """
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        """
        Validaciones iniciales antes de ejecutar cualquier acción.
        Verifica que el usuario tenga un empleado activo asociado.
        """
        super().initial(request, *args, **kwargs)

        # Validar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return

        # Validar que exista empresa en el request (seteada por middleware)
        if not hasattr(request, 'empresa'):
            logger.error(
                f"Request sin empresa | User={request.user.id} | "
                f"Path={request.path} | Method={request.method}"
            )
            raise PermissionDenied("Empresa no identificada en la solicitud")

        # Validar que el usuario tenga un empleado activo
        try:
            empleado = Empleado.objects.select_related('empresa', 'persona').get(
                usuario=request.user,
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            )

            # Validar estado del empleado
            if empleado.estado != 'activo':
                logger.warning(
                    f"Empleado no activo | Empleado={empleado.id} | "
                    f"Estado={empleado.estado} | User={request.user.id}"
                )
                raise PermissionDenied(
                    f"Empleado en estado: {empleado.get_estado_display()}"
                )

            # Setear empleado en request para uso posterior
            request.empleado = empleado

        except Empleado.DoesNotExist:
            logger.warning(
                f"Usuario sin empleado asociado | User={request.user.id} | "
                f"Username={request.user.username} | Empresa={request.empresa.subdominio}"
            )
            raise PermissionDenied("Usuario sin empleado asociado")

    def get_queryset(self):
        """
        Filtra automáticamente por empresa del usuario.

        IMPORTANTE: Los ViewSets hijos deben hacer super().get_queryset()
        y luego agregar select_related/prefetch_related.
        """
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset.none()

        # Seguridad multi-tenant: filtrar por empresa y soft delete
        return queryset.filter(
            empresa=self.request.empresa,
            deleted_at__isnull=True
        )

    def perform_create(self, serializer):
        """Agrega empresa y usuario en creación."""
        serializer.save(
            empresa=self.request.empresa,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        """Agrega usuario en actualización."""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete con deleted_at y deleted_by."""
        instance.soft_delete(user=self.request.user)