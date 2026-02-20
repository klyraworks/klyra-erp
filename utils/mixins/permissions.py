# utils/mixins/permissions.py
"""
Mixin reutilizable para control de permisos basado en Django permissions.
Funciona con CUALQUIER módulo y rol, escalable a todo el sistema.
"""
from rest_framework.exceptions import PermissionDenied
import logging


class PermissionCheckMixin:
    """
    Mixin para verificar permisos de Django de forma flexible.

    Uso en ViewSets:
        class ProductoViewSet(PermissionCheckMixin, viewsets.ModelViewSet):
            def list(self, request):
                self.verificar_permiso('view_producto')
                # ... resto del código

    Ventajas:
    - Funciona con CUALQUIER rol que tenga el permiso
    - No necesita hardcodear nombres de roles
    - Escalable a múltiples módulos
    - Logging automático de intentos de acceso
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_logger = logging.getLogger('permissions')

    def verificar_permiso(self, codename, mensaje_error=None, app_label=None):
        """
        Verifica si el usuario tiene un permiso específico.

        Args:
            codename: Código del permiso (ej: 'add_empleado', 'view_producto')
            mensaje_error: Mensaje personalizado si no tiene permiso
            app_label: Label de la app (ej: 'rrhh', 'ventas').
                      Si no se especifica, se intenta detectar automáticamente.

        Raises:
            PermissionDenied: Si el usuario no tiene el permiso

        Example:
            self.verificar_permiso('add_producto', app_label='ventas')
            self.verificar_permiso('view_empleado')  # Auto-detecta app
        """
        usuario = self.request.user

        # Auto-detectar app_label del modelo si no se especifica
        if not app_label:
            app_label = self._detectar_app_label()

        permiso_completo = f'{app_label}.{codename}'

        if not usuario.has_perm(permiso_completo):
            roles_usuario = list(usuario.groups.values_list('name', flat=True))

            self.permission_logger.warning(
                f"Acceso denegado: {usuario.username} sin permiso '{permiso_completo}'",
                extra={
                    'username': usuario.username,
                    'roles': roles_usuario,
                    'permiso_requerido': permiso_completo,
                    'endpoint': getattr(self, 'action', 'unknown')
                }
            )

            if mensaje_error:
                raise PermissionDenied(mensaje_error)
            else:
                raise PermissionDenied(
                    f"No tienes permiso para realizar esta acción. "
                    f"Permiso requerido: {codename}"
                )

    def verificar_cualquier_permiso(self, permisos, mensaje_error=None, app_label=None):
        """
        Verifica si el usuario tiene AL MENOS UNO de los permisos.

        Args:
            permisos: Lista de códigos de permisos
            mensaje_error: Mensaje si no tiene ninguno
            app_label: Label de la app

        Example:
            # Usuario necesita poder ver O editar productos
            self.verificar_cualquier_permiso(
                ['view_producto', 'change_producto'],
                app_label='ventas'
            )
        """
        usuario = self.request.user

        if not app_label:
            app_label = self._detectar_app_label()

        permisos_completos = [f'{app_label}.{p}' for p in permisos]

        tiene_alguno = any(usuario.has_perm(p) for p in permisos_completos)

        if not tiene_alguno:
            roles_usuario = list(usuario.groups.values_list('name', flat=True))

            self.permission_logger.warning(
                f"Acceso denegado: {usuario.username} sin ningún permiso requerido",
                extra={
                    'username': usuario.username,
                    'roles': roles_usuario,
                    'permisos_requeridos': permisos_completos
                }
            )

            if mensaje_error:
                raise PermissionDenied(mensaje_error)
            else:
                raise PermissionDenied(
                    f"No tienes permiso para realizar esta acción. "
                    f"Requieres al menos uno de: {', '.join(permisos)}"
                )

    def verificar_todos_permisos(self, permisos, mensaje_error=None, app_label=None):
        """
        Verifica si el usuario tiene TODOS los permisos.

        Example:
            # Usuario necesita poder ver Y editar productos
            self.verificar_todos_permisos(
                ['view_producto', 'change_producto'],
                app_label='ventas'
            )
        """
        usuario = self.request.user

        if not app_label:
            app_label = self._detectar_app_label()

        permisos_completos = [f'{app_label}.{p}' for p in permisos]

        tiene_todos = all(usuario.has_perm(p) for p in permisos_completos)

        if not tiene_todos:
            roles_usuario = list(usuario.groups.values_list('name', flat=True))

            self.permission_logger.warning(
                f"Acceso denegado: {usuario.username} sin todos los permisos requeridos",
                extra={
                    'username': usuario.username,
                    'roles': roles_usuario,
                    'permisos_requeridos': permisos_completos
                }
            )

            if mensaje_error:
                raise PermissionDenied(mensaje_error)
            else:
                raise PermissionDenied(
                    f"No tienes todos los permisos necesarios. "
                    f"Requieres: {', '.join(permisos)}"
                )

    def tiene_permiso(self, codename, app_label=None):
        """
        Verifica permiso sin lanzar excepción.
        Útil para condicionales en la lógica.

        Returns:
            bool: True si tiene el permiso

        Example:
            if self.tiene_permiso('delete_producto'):
                # Mostrar botón de eliminar
        """
        if not app_label:
            app_label = self._detectar_app_label()

        permiso_completo = f'{app_label}.{codename}'
        return self.request.user.has_perm(permiso_completo)

    def _detectar_app_label(self):
        """
        Intenta detectar automáticamente el app_label del modelo del queryset.
        """
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model._meta.app_label

        if hasattr(self, 'serializer_class'):
            serializer = self.serializer_class()
            if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
                return serializer.Meta.model._meta.app_label

        # Fallback: intentar extraer del nombre de la clase
        # ProductoViewSet -> 'producto' -> buscar en settings
        self.permission_logger.warning(
            "No se pudo detectar app_label automáticamente"
        )
        return 'rrhh'  # Cambiar por tu app por defecto


class RoleMixin:
    """
    Mixin para verificar roles específicos (menos flexible, pero útil a veces).
    """

    def tiene_rol(self, nombre_rol):
        """Verifica si el usuario tiene un rol específico"""
        return self.request.user.groups.filter(name=nombre_rol).exists()

    def tiene_alguno_rol(self, roles):
        """Verifica si el usuario tiene alguno de los roles"""
        return self.request.user.groups.filter(name__in=roles).exists()

    def verificar_rol(self, nombre_rol, mensaje_error=None):
        """Verifica rol y lanza excepción si no lo tiene"""
        if not self.tiene_rol(nombre_rol):
            roles_usuario = list(self.request.user.groups.values_list('name', flat=True))

            if mensaje_error:
                raise PermissionDenied(mensaje_error)
            else:
                raise PermissionDenied(
                    f"Rol requerido: {nombre_rol}. Tus roles: {', '.join(roles_usuario)}"
                )


# ==================== USO COMBINADO ====================

class AdvancedPermissionMixin(PermissionCheckMixin, RoleMixin):
    """
    Combina verificación de permisos Y roles para máxima flexibilidad.

    Example:
        class VentaViewSet(AdvancedPermissionMixin, viewsets.ModelViewSet):
            def create(self, request):
                # Opción 1: Verificar permiso (recomendado)
                self.verificar_permiso('add_venta')

                # Opción 2: Verificar rol específico (menos flexible)
                self.verificar_rol('Ventas | Vendedor')

                # Opción 3: Lógica condicional
                if self.tiene_permiso('aprobar_venta'):
                    # Lógica especial para supervisores
                    pass
    """
    pass