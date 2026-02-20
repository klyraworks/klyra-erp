# apis/rrhh/views/activation_views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.rrhh.models import ActivationToken, OTPToken, Empleado
from utils.empleado_helpers import ActivationTokenGenerator, OTPGenerator
from functions.services import EmailService

import logging

logger = logging.getLogger('activation')


# ==================== ACTIVACIÓN POR TOKEN ====================

@require_http_methods(["GET", "POST"])
def activate_account(request, token):
    """
    Vista para activar cuenta con token.

    GET: Muestra formulario de establecer contraseña
    POST: Procesa nueva contraseña y activa cuenta

    URL: /activate/<token>/
    """

    # Verificar token
    activation = ActivationTokenGenerator.verify(token)

    if not activation:
        logger.warning(f"Intento de activación con token inválido")
        return render(request, 'emails/activation_error.html', {
            'error': 'invalid_token',
            'message': 'El link de activación es inválido o ha expirado.'
        })

    empleado = activation.empleado

    # GET: Mostrar formulario
    if request.method == 'GET':
        return render(request, 'emails/account_activated.html', {
            'empleado': empleado,
            'token': token,
            'tiempo_restante': activation.time_remaining()
        })

    # POST: Procesar contraseña
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')

    # Validaciones
    if not password or not confirm_password:
        messages.error(request, 'Todos los campos son requeridos')
        return render(request, 'emails/account_activated.html', {
            'empleado': empleado,
            'token': token
        })

    if password != confirm_password:
        messages.error(request, 'Las contraseñas no coinciden')
        return render(request, 'emails/account_activated.html', {
            'empleado': empleado,
            'token': token
        })

    if len(password) < 8:
        messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
        return render(request, 'emails/account_activated.html', {
            'empleado': empleado,
            'token': token
        })

    # Establecer contraseña y activar cuenta
    try:
        empleado.usuario.set_password(password)
        empleado.usuario.save()

        empleado.activar_cuenta()

        # Marcar token como usado
        ActivationTokenGenerator.mark_as_used(activation)

        # Registrar IP y navegador
        activation.ip_address = get_client_ip(request)
        activation.user_agent = request.META.get('HTTP_USER_AGENT', '')
        activation.save()

        logger.info(
            f"Cuenta activada exitosamente",
            extra={
                'empleado_id': empleado.id,
                'username': empleado.usuario.username
            }
        )

        # Loguar automáticamente
        login(request, empleado.usuario)

        messages.success(
            request,
            f'¡Bienvenido {empleado.persona.full_name()}! Tu cuenta ha sido activada exitosamente.'
        )

        return redirect('dashboard')

    except Exception as e:
        logger.exception(f"Error activando cuenta: {str(e)}")
        messages.error(request, 'Ocurrió un error al activar tu cuenta. Contacta a soporte.')
        return render(request, 'emails/account_activated.html', {
            'empleado': empleado,
            'token': token
        })


# ==================== REENVIAR LINK DE ACTIVACIÓN ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_activation_link(request):
    """
    API endpoint para reenviar link de activación.

    POST /api/rrhh/resend-activation/
    Body: {"email": "empleado@example.com"}
    """

    from apps.seguridad.models import Empleado

    email = request.data.get('email')

    if not email:
        return Response(
            {'error': 'Email es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        empleado = Empleado.objects.select_related('persona', 'usuario').get(
            persona__email=email,
            cuenta_activada=False
        )

        # Generar nuevo token
        token = ActivationTokenGenerator.generate(empleado)

        # Enviar email
        success, message = EmailService.send_activation_link(empleado, token)

        if success:
            logger.info(
                f"Link de activación reenviado",
                extra={'empleado_id': empleado.id}
            )

            return Response({
                'message': 'Link de activación enviado. Revisa tu email.'
            })
        else:
            return Response(
                {'error': 'Error enviando email. Intenta más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Empleado.DoesNotExist:
        # Por seguridad, no revelar si el email existe o no
        return Response({
            'message': 'Si el email existe, recibirás un link de activación.'
        })


# ==================== RESET DE CONTRASEÑA POR OTP ====================

@csrf_protect
@require_http_methods(["GET", "POST"])
def reset_password_otp(request):
    """
    Vista para reset de contraseña usando OTP (código numérico).
    Para casos donde el empleado no tiene acceso a email.

    GET: Muestra formulario para ingresar OTP
    POST: Valida OTP y permite cambiar contraseña

    URL: /reset-password-otp/
    """

    if request.method == 'GET':
        return render(request, 'emails/password_reset.html')

    # POST: Validar OTP y cambiar contraseña
    username = request.POST.get('username')
    otp = request.POST.get('otp')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')

    # Validaciones
    if not all([username, otp, new_password, confirm_password]):
        messages.error(request, 'Todos los campos son requeridos')
        return render(request, 'emails/password_reset.html')

    if new_password != confirm_password:
        messages.error(request, 'Las contraseñas no coinciden')
        return render(request, 'emails/password_reset.html')

    if len(new_password) < 8:
        messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
        return render(request, 'emails/password_reset.html')

    try:
        from django.contrib.auth.models import User
        from apps.seguridad.models import Empleado

        # Buscar usuario
        user = User.objects.get(username=username)
        empleado = Empleado.objects.get(usuario=user)

        # Verificar OTP
        if OTPGenerator.verify(empleado, otp):
            # Cambiar contraseña
            user.set_password(new_password)
            user.save()

            logger.info(
                f"Contraseña reseteada con OTP",
                extra={'empleado_id': empleado.id}
            )

            messages.success(
                request,
                'Contraseña cambiada exitosamente. Ya puedes iniciar sesión.'
            )

            return redirect('login')
        else:
            # OTP inválido - intentar incrementar contador
            try:
                otp_token = OTPToken.objects.get(
                    empleado=empleado,
                    otp=otp,
                    usado=False
                )
                otp_token.increment_failed_attempts()

                if otp_token.bloqueado:
                    messages.error(
                        request,
                        'Código bloqueado por múltiples intentos. Solicita uno nuevo.'
                    )
                else:
                    messages.error(
                        request,
                        f'Código inválido o expirado. Intentos restantes: {3 - otp_token.intentos_fallidos}'
                    )
            except OTPToken.DoesNotExist:
                messages.error(request, 'Código inválido o expirado')

            return render(request, 'emails/password_reset.html')

    except (User.DoesNotExist, Empleado.DoesNotExist):
        messages.error(request, 'Usuario no encontrado')
        return render(request, 'emails/password_reset.html')


# ==================== SOLICITAR OTP (Para soporte) ====================

@api_view(['POST'])
def request_otp(request):
    """
    API endpoint para que soporte genere OTP para un empleado.
    Requiere permisos de administrador.

    POST /api/rrhh/request-otp/
    Body: {"empleado_id": 123}
    """

    from apps.seguridad.models import Empleado

    if not request.user.is_staff:
        return Response(
            {'error': 'No autorizado'},
            status=status.HTTP_403_FORBIDDEN
        )

    empleado_id = request.data.get('empleado_id')

    if not empleado_id:
        return Response(
            {'error': 'empleado_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        empleado = Empleado.objects.get(id=empleado_id)

        # Generar OTP
        otp = OTPGenerator.generate_with_expiry(
            empleado=empleado,
            length=6,
            expiry_minutes=10
        )

        logger.info(
            f"OTP generado por soporte",
            extra={
                'empleado_id': empleado.id,
                'generado_por': request.user.id
            }
        )

        return Response({
            'otp': otp,
            'empleado': {
                'id': empleado.id,
                'nombre': empleado.persona.full_name(),
                'username': empleado.usuario.username
            },
            'expires_in': '10 minutos',
            'instrucciones': f'Dicta este código al empleado: {otp}'
        })

    except Empleado.DoesNotExist:
        return Response(
            {'error': 'Empleado no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== HELPERS ====================

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip