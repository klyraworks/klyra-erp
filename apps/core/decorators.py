# apps/core/decorators.py
from functools import wraps
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger('security')


def requiere_permiso(permiso):
    """
    Decorador para validar permisos de usuario.

    Args:
        permiso: Código del permiso requerido (str)

    Usage:
        @requiere_permiso('crear_productos')
        def create(self, request):
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # DEBUG: Log inicial
            logger.info(f"=== DECORADOR requiere_permiso ===")
            logger.info(f"Permiso requerido: {permiso}")
            logger.info(f"Usuario autenticado: {request.user.is_authenticated}")
            logger.info(f"Usuario ID: {request.user.id}")
            logger.info(f"Username: {request.user.username}")
            logger.info(f"Has request.empleado: {hasattr(request, 'empleado')}")
            logger.info(f"Has request.empresa: {hasattr(request, 'empresa')}")

            if hasattr(request, 'empresa'):
                logger.info(f"Empresa ID: {request.empresa.id}")
                logger.info(f"Empresa subdominio: {request.empresa.subdominio}")

            # Validar que el usuario esté autenticado
            if not request.user.is_authenticated:
                logger.warning(f"Usuario no autenticado")
                raise PermissionDenied("Debe iniciar sesión")

            # Obtener empleado desde el request
            empleado = getattr(request, 'empleado', None)
            logger.info(f"Empleado desde request: {empleado}")

            if not empleado:
                logger.info("Empleado no en request, buscando en BD...")
                from apps.seguridad.models import Empleado

                empresa = getattr(request, 'empresa', None)

                if not empresa:
                    logger.error("No hay empresa en request")
                    raise PermissionDenied("Empresa no identificada")

                try:
                    logger.info(f"Buscando empleado con: usuario_id={request.user.id}, empresa_id={empresa.id}")

                    empleado = Empleado.objects.select_related('empresa', 'persona').get(
                        usuario=request.user,
                        empresa=empresa,
                        is_active=True,
                        deleted_at__isnull=True
                    )
                    logger.info(f"Empleado encontrado: ID={empleado.id}, Codigo={empleado.codigo}")
                    request.empleado = empleado

                except Empleado.DoesNotExist:
                    logger.error(
                        f"EMPLEADO NO ENCONTRADO en BD | "
                        f"Usuario ID={request.user.id} | "
                        f"Empresa ID={empresa.id} | "
                        f"Subdominio={empresa.subdominio}"
                    )

                    # Query de debug para ver qué hay en la BD
                    empleados_usuario = Empleado.objects.filter(usuario=request.user)
                    logger.error(
                        f"Empleados del usuario en BD: {list(empleados_usuario.values('id', 'empresa_id', 'is_active', 'deleted_at'))}")

                    raise PermissionDenied("Usuario sin empleado asociado")

                except Exception as e:
                    logger.error(f"Error inesperado al buscar empleado: {str(e)}", exc_info=True)
                    raise PermissionDenied("Error al validar empleado")

            # Validar permiso
            tiene_permiso = False
            formatos_permiso = [
                permiso,
                f'inventario.{permiso}',
                f'seguridad.{permiso}',
                f'ventas.{permiso}',
                f'compras.{permiso}',
            ]

            for formato in formatos_permiso:
                if request.user.has_perm(formato):
                    tiene_permiso = True
                    logger.info(f"Permiso encontrado: {formato}")
                    break

            if not tiene_permiso:
                logger.warning(f"PERMISO DENEGADO: {permiso}")
                raise PermissionDenied("No tiene permisos para realizar esta acción")

            logger.info(f"PERMISO CONCEDIDO | Acción={func.__name__}")
            logger.info(f"=== FIN DECORADOR ===")

            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator