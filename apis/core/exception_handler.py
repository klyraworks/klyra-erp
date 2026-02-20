# apis/core/exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from .response_handler import StandardResponse
import logging

logger = logging.getLogger('apps.api')


def custom_exception_handler(exc, context):
    """
    Exception handler personalizado que usa StandardResponse

    Maneja:
    - Errores de autenticación (JWT expirado, inválido)
    - Errores de validación
    - Errores de permisos
    - Errores genéricos
    """

    # ==================== ERRORES DE AUTENTICACIÓN JWT ====================

    if isinstance(exc, (InvalidToken, TokenError)):
        logger.warning(
            f"Token JWT inválido o expirado | "
            f"View={context.get('view').__class__.__name__ if context.get('view') else 'Unknown'} | "
            f"User={context.get('request').user if context.get('request') else 'Anonymous'}"
        )
        return StandardResponse.error(
            mensaje="Tu sesión ha expirado. Por favor, inicia sesión nuevamente.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        logger.warning(
            f"Autenticación fallida | "
            f"View={context.get('view').__class__.__name__ if context.get('view') else 'Unknown'}"
        )
        return StandardResponse.error(
            mensaje="Credenciales de autenticación no válidas o no proporcionadas.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # ==================== OTROS ERRORES ====================

    # Llamar al handler por defecto de DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Obtener mensaje de error
        error_message = str(exc)

        # Si es un diccionario de errores de validación
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_message = response.data['detail']
            elif 'non_field_errors' in response.data:
                error_message = response.data['non_field_errors'][0]

        # Logging técnico
        logger.error(
            f"Exception: {exc.__class__.__name__} | "
            f"Message: {str(exc)} | "
            f"View: {context.get('view').__class__.__name__ if context.get('view') else 'Unknown'}",
            exc_info=True
        )

        # Respuesta amigable al usuario
        return StandardResponse.error(
            mensaje=error_message if isinstance(error_message, str) else "Error en la solicitud",
            status_code=response.status_code
        )

    # Errores no manejados por DRF
    logger.critical(
        f"Error no manejado: {exc.__class__.__name__} | {str(exc)}",
        exc_info=True
    )

    return StandardResponse.error(
        mensaje="Error interno del servidor",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )