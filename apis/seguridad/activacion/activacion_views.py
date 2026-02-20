# ==================== IMPORTS ====================
# Standard library
import logging

# Third-party
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

# Local
from apis.core.response_handler import StandardResponse
from utils.empleado_helpers import ActivationTokenGenerator


logger = logging.getLogger('apps.seguridad')


class VerificarTokenView(APIView):
    """
    GET /api/seguridad/verificar-token/?token=<token>

    Verifica si un token de activación es válido antes de mostrar
    el formulario en el frontend. No consume el token.

    Respuestas:
        200 - Token válido, retorna datos del empleado para mostrar en el form
        400 - Token inválido o expirado
    """
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')

        if not token:
            return StandardResponse.error(
                mensaje="Token no proporcionado.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        activation = ActivationTokenGenerator.verify(token)

        if not activation:
            logger.warning(
                f"Token de activación inválido o expirado | "
                f"IP={request.META.get('REMOTE_ADDR')}"
            )
            return StandardResponse.error(
                mensaje="El enlace de activación es inválido o ha expirado. "
                        "Solicita un nuevo enlace a tu administrador.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        empleado = activation.empleado

        if empleado.cuenta_activada:
            return StandardResponse.error(
                mensaje="Esta cuenta ya fue activada. Puedes iniciar sesión.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            f"Token verificado | Empleado={empleado.id} | "
            f"IP={request.META.get('REMOTE_ADDR')}"
        )

        return StandardResponse.success(data={
            'valido': True,
            'empleado': {
                'nombre': empleado.persona.nombre1,
                'nombre_completo': empleado.get_full_name(),
                'username': empleado.usuario.username,
                'puesto': empleado.puesto,
            },
            'expira_en': activation.expires_at,
        })


class ActivarCuentaView(APIView):
    """
    POST /api/seguridad/activar-cuenta/

    Activa la cuenta del empleado y define su contraseña.

    Body:
        {
            "token": "<token>",
            "password": "NuevaPassword123!",
            "password_confirmacion": "NuevaPassword123!"
        }

    Flujo:
        1. Verifica token
        2. Valida contraseñas
        3. Activa User + setea password
        4. Marca empleado como activado
        5. Marca token como usado
        6. Retorna JWT para login automático
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token               = request.data.get('token')
        password            = request.data.get('password')
        password_confirmacion = request.data.get('password_confirmacion')

        # -- Validar campos presentes
        errores = {}
        if not token:
            errores['token'] = ['Este campo es requerido.']
        if not password:
            errores['password'] = ['Este campo es requerido.']
        if not password_confirmacion:
            errores['password_confirmacion'] = ['Este campo es requerido.']
        if errores:
            return StandardResponse.validation_error(errores)

        # -- Verificar token
        activation = ActivationTokenGenerator.verify(token)
        if not activation:
            logger.warning(
                f"Intento de activación con token inválido | "
                f"IP={request.META.get('REMOTE_ADDR')}"
            )
            return StandardResponse.error(
                mensaje="El enlace de activación es inválido o ha expirado. "
                        "Solicita un nuevo enlace a tu administrador.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        empleado = activation.empleado

        if empleado.cuenta_activada:
            return StandardResponse.error(
                mensaje="Esta cuenta ya fue activada. Puedes iniciar sesión.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # -- Validar contraseñas
        if password != password_confirmacion:
            return StandardResponse.validation_error({
                'password_confirmacion': ['Las contraseñas no coinciden.']
            })

        try:
            validate_password(password, user=empleado.usuario)
        except DjangoValidationError as e:
            return StandardResponse.validation_error({
                'password': list(e.messages)
            })

        # -- Activar cuenta
        try:
            with transaction.atomic():
                # Activar User y setear contraseña
                usuario = empleado.usuario
                usuario.set_password(password)
                usuario.is_active = True
                usuario.save(update_fields=['password', 'is_active'])

                # Marcar empleado como activado
                empleado.cuenta_activada = True
                empleado.fecha_activacion = timezone.now()
                empleado.debe_cambiar_password = False
                empleado.save(update_fields=[
                    'cuenta_activada',
                    'fecha_activacion',
                    'debe_cambiar_password',
                    'updated_at'
                ])

                # Consumir token — no puede usarse de nuevo
                ActivationTokenGenerator.mark_as_used(activation)

            # Generar JWT para login automático
            jwt_tokens = self._generar_jwt(usuario)

            logger.info(
                f"Cuenta activada | Empleado={empleado.id} | "
                f"Username={usuario.username} | "
                f"IP={request.META.get('REMOTE_ADDR')}"
            )

            return StandardResponse.success(
                data={
                    'access': jwt_tokens['access'],
                    'refresh': jwt_tokens['refresh'],
                    'empleado': {
                        'id': str(empleado.id),
                        'nombre_completo': empleado.get_full_name(),
                        'username': usuario.username,
                        'puesto': empleado.puesto,
                    }
                },
                mensaje=f"¡Bienvenido {empleado.persona.nombre1}! Tu cuenta ha sido activada exitosamente.",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Error al activar cuenta | Empleado={empleado.id} | Error={str(e)}",
                exc_info=True
            )
            return StandardResponse.error(
                mensaje="Error al activar la cuenta. Intenta nuevamente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generar_jwt(self, usuario):
        """
        Genera par de tokens JWT usando SimpleJWT.

        Returns:
            dict: {'access': str, 'refresh': str}
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(usuario)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }