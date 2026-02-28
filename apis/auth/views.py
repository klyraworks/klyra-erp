# apis/auth/views.py
import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.seguridad.models import Empleado
from apis.core.response_handler import StandardResponse
from rest_framework import status


logger = logging.getLogger('apps.seguridad')


class LoginView(APIView):
    """
    Vista de login con validación multi-tenant y JWT.

    Endpoints:
        POST /api/auth/login/ - Iniciar sesión

    Body:
        {
            "username": "string",
            "password": "string"
        }

    Returns:
        - 200: Login exitoso con tokens JWT
        - 400: Campos faltantes
        - 401: Credenciales inválidas
        - 403: Usuario inactivo o sin acceso a la empresa
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Validar campos requeridos
        if not username or not password:
            logger.warning(f"Intento de login sin credenciales completas | IP={request.META.get('REMOTE_ADDR')}")
            return StandardResponse.error(
                mensaje="Usuario y contraseña son requeridos",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if not user:
            logger.warning(f"Login fallido | Username={username} | IP={request.META.get('REMOTE_ADDR')}")
            return StandardResponse.error(
                mensaje="Credenciales inválidas",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar que el usuario esté activo
        if not user.is_active:
            logger.warning(f"Intento de login con usuario inactivo | User={user.id} | Username={username}")
            return StandardResponse.error(
                mensaje="Usuario inactivo",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # VALIDACIÓN MULTI-TENANT: Verificar que pertenezca a esta empresa
        try:
            empleado = Empleado.objects.select_related(
                'empresa',
                'persona',
                'departamento',
                'usuario'
            ).prefetch_related(
                'usuario__groups__permissions',
                'usuario__user_permissions'
            ).get(
                usuario=user,
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            )
        except Empleado.DoesNotExist:
            logger.warning(
                f"Acceso denegado | User={user.id} | Username={username} | "
                f"Empresa={request.empresa.subdominio} | IP={request.META.get('REMOTE_ADDR')}"
            )
            return StandardResponse.error(
                mensaje=f"Este usuario no pertenece a {request.empresa.nombre_comercial}",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Verificar estado del empleado
        if empleado.estado != 'activo':
            logger.warning(
                f"Empleado con estado no activo | Empleado={empleado.id} | "
                f"Estado={empleado.estado} | Username={username}"
            )
            return StandardResponse.error(
                mensaje=f"Empleado en estado: {empleado.get_estado_display()}",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Verificar si cuenta está activada
        if not empleado.cuenta_activada:
            logger.warning(f"Cuenta no activada | Empleado={empleado.id} | Username={username}")
            return StandardResponse.error(
                mensaje="Cuenta no activada. Revise su correo para activar su cuenta.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)

        # Obtener permisos del usuario
        permisos = list(user.user_permissions.values_list('codename', flat=True))
        permisos_grupos = list(user.groups.values_list('permissions__codename', flat=True))
        permisos_totales = list(set(permisos + permisos_grupos))

        # Login exitoso
        logger.info(
            f"Login exitoso | User={user.id} | Username={username} | "
            f"Empleado={empleado.codigo} | Empresa={request.empresa.subdominio}"
        )

        return StandardResponse.success(
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'empleado': {
                    'id': str(empleado.id),
                    'codigo': empleado.codigo,
                    'nombre_completo': empleado.get_full_name(),
                    'puesto': empleado.puesto.nombre if empleado.puesto else None,
                    'departamento': empleado.departamento.nombre if empleado.departamento else None,
                    'estado': empleado.estado,
                    'debe_cambiar_password': empleado.debe_cambiar_password
                },
                'empresa': {
                    'id': str(request.empresa.id),
                    'ruc': request.empresa.ruc,
                    'razon_social': request.empresa.razon_social,
                    'nombre_comercial': request.empresa.nombre_comercial,
                    'subdominio': request.empresa.subdominio,
                    'ambiente_sri': request.empresa.ambiente_sri,
                    # 'puede_facturar': request.empresa.puede_facturar_electronicamente(),
                    'logo': request.empresa.logo.url if request.empresa.logo else None
                },
                'permisos': permisos_totales
            },
            mensaje="Login exitoso"
        )


class LogoutView(APIView):
    """
    Vista de logout

    Endpoints:
        POST /api/auth/logout/ - Cerrar sesión
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"Logout | User={request.user.id} | Username={request.user.username}")

        return StandardResponse.success(
            mensaje="Sesión cerrada exitosamente"
        )


class CheckAuthView(APIView):
    """
    Verifica si el usuario está autenticado y si tiene acceso a la empresa actual.

    Endpoints:
        GET /api/auth/check/ - Verificar autenticación
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            empleado = Empleado.objects.select_related(
                'empresa',
                'persona',
                'departamento'
            ).get(
                usuario=request.user,
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            )

            if empleado.estado != 'activo':
                logger.warning(
                    f"CheckAuth: Empleado no activo | Empleado={empleado.id} | "
                    f"Estado={empleado.estado}"
                )
                return StandardResponse.error(
                    mensaje="Empleado no activo",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            return StandardResponse.success(
                data={
                    'authenticated': True,
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email
                    },
                    'empleado': {
                        'id': str(empleado.id),
                        'codigo': empleado.codigo,
                        'nombre_completo': empleado.get_full_name(),
                        'puesto': empleado.puesto.nombre if empleado.puesto else None,
                        'departamento': empleado.departamento.nombre if empleado.departamento else None,
                        'estado': empleado.estado
                    },
                    'empresa': {
                        'id': str(request.empresa.id),
                        'nombre_comercial': request.empresa.nombre_comercial,
                        'razon_social': request.empresa.razon_social,
                        'subdominio': request.empresa.subdominio,
                        'logo': request.empresa.logo.url if request.empresa.logo else None
                    }
                }
            )

        except Empleado.DoesNotExist:
            logger.warning(
                f"CheckAuth: Empleado no encontrado | User={request.user.id} | "
                f"Empresa={request.empresa.subdominio}"
            )
            return StandardResponse.error(
                mensaje=f"No tiene acceso a {request.empresa.nombre_comercial}",
                status_code=status.HTTP_403_FORBIDDEN
            )


class UserInfoView(APIView):
    """
    Obtiene información del usuario autenticado

    Endpoints:
        GET /api/auth/user/ - Información del usuario
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            empleado = Empleado.objects.select_related(
                'empresa',
                'persona',
                'departamento'
            ).get(
                usuario=request.user,
                empresa=request.empresa,
                is_active=True,
                deleted_at__isnull=True
            )

            return StandardResponse.success(
                data={
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email
                    },
                    'empleado': {
                        'id': str(empleado.id),
                        'codigo': empleado.codigo,
                        'nombre_completo': empleado.get_full_name(),
                        'puesto': empleado.puesto.nombre if empleado.puesto else None,
                        'departamento': empleado.departamento.nombre if empleado.departamento else None,
                        'fecha_contratacion': empleado.fecha_contratacion,
                        'estado': empleado.estado,
                        'debe_cambiar_password': empleado.debe_cambiar_password
                    },
                    'empresa': {
                        'id': str(request.empresa.id),
                        'ruc': request.empresa.ruc,
                        'razon_social': request.empresa.razon_social,
                        'nombre_comercial': request.empresa.nombre_comercial,
                        'subdominio': request.empresa.subdominio
                    }
                }
            )

        except Empleado.DoesNotExist:
            logger.error(
                f"UserInfo: Empleado no encontrado | User={request.user.id} | "
                f"Empresa={request.empresa.subdominio}"
            )
            return StandardResponse.error(
                mensaje="Empleado no encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )