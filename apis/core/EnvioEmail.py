# apis/base/EnvioEmail.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EnvioEmail(viewsets.ViewSet):
    """ViewSet para probar envío de emails"""

    # Esto evita el error de basename
    basename = 'enviaremail'

    @action(detail=False, methods=['post'], url_path='test')
    def send_test_email(self, request):
        """
        Endpoint de prueba para enviar email

        POST /api/enviaremail/test/

        Body (JSON):
        {
            "email": "destino@example.com",
            "nombre": "Usuario Prueba"
        }
        """
        try:
            # Obtener datos del request
            email_destino = request.data.get('email')
            nombre = request.data.get('nombre', 'Usuario')

            # Validación básica
            if not email_destino:
                return Response(
                    {'error': 'El campo "email" es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"📧 Preparando email de prueba para: {email_destino}")

            # Configurar email
            subject = "Email de Prueba - Klyra System"
            from_email = settings.DEFAULT_FROM_EMAIL

            # Contenido HTML
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email de Prueba</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .test-box {{ background-color: #fff; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 4px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; background-color: #f1f1f1; border-radius: 0 0 5px 5px; }}
        .emoji {{ font-size: 24px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✉️ Email de Prueba</h1>
        </div>

        <div class="content">
            <h2>¡Hola {nombre}!</h2>

            <p>Este es un <strong>email de prueba</strong> enviado desde el sistema Klyra.</p>

            <div class="test-box">
                <p class="emoji">✅</p>
                <h3>Configuración Exitosa</h3>
                <p>Si estás leyendo este mensaje, significa que:</p>
                <ul>
                    <li>El servidor SMTP está configurado correctamente</li>
                    <li>Django puede enviar emails</li>
                    <li>EmailMultiAlternatives funciona perfectamente</li>
                </ul>
            </div>

            <p><strong>Detalles del envío:</strong></p>
            <ul>
                <li><strong>Destinatario:</strong> {email_destino}</li>
                <li><strong>Sistema:</strong> Klyra - Test Environment</li>
                <li><strong>Método:</strong> EmailMultiAlternatives</li>
            </ul>

            <p>Este es un email automático de prueba. No es necesario responder.</p>

            <p style="margin-top: 30px;">¡Saludos! 👋</p>
        </div>

        <div class="footer">
            <p>Este es un email de prueba del sistema Klyra</p>
            <p>© 2024 - Sistema de Gestión</p>
        </div>
    </div>
</body>
</html>
"""

            # Versión texto plano (fallback)
            text_content = strip_tags(html_content)

            # Crear email con HTML y texto
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[email_destino]
            )
            msg.attach_alternative(html_content, "text/html")

            # Enviar
            logger.info(f"📤 Enviando email de prueba a {email_destino}...")
            result = msg.send(fail_silently=False)

            if result:
                logger.info(f"Email enviado exitosamente a {email_destino}")
                return Response({
                    'success': True,
                    'message': 'Email enviado exitosamente',
                    'destinatario': email_destino,
                    'subject': subject
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Error: msg.send() retornó 0")
                return Response({
                    'success': False,
                    'error': 'El servidor no confirmó el envío'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error enviando email de prueba: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='info')
    def email_info(self, request):
        """
        Endpoint para ver información de configuración de email

        GET /api/enviaremail/info/
        """
        try:
            config = {
                'email_backend': settings.EMAIL_BACKEND,
                'email_host': settings.EMAIL_HOST,
                'email_port': settings.EMAIL_PORT,
                'email_use_tls': settings.EMAIL_USE_TLS,
                'default_from_email': settings.DEFAULT_FROM_EMAIL,
            }

            return Response({
                'success': True,
                'configuration': config,
                'message': 'Configuración de email cargada'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)