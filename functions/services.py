from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from decouple import config

import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de emails con sistema de templates HTML"""

    @staticmethod
    def send_email_from_template(to_email, subject, template_name, context):
        """
        Método genérico para enviar emails usando templates HTML

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            template_name: Nombre del template (sin extensión)
            context: Diccionario con datos para el template

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            from_email = config('DEFAULT_FROM_EMAIL')

            # Agregar datos comunes a todos los templates
            context.update({
                'company_name': config('COMPANY_NAME'),
            })

            # Renderizar template HTML
            html_content = render_to_string(
                f'emails/{template_name}.html',
                context
            )
            text_content = strip_tags(html_content)

            # Crear y enviar email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email]
            )
            msg.attach_alternative(html_content, "text/html")

            result = msg.send(fail_silently=False)

            if result:
                logger.info(f"Email enviado exitosamente a {to_email}")
                return True, "Email enviado exitosamente"
            else:
                logger.error(f"Error enviando email a {to_email}")
                return False, "Error al enviar email"

        except Exception as e:
            logger.error(f"Excepción enviando email: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def send_employee_credentials(employee, password):
        """Enviar credenciales de empleado por email"""
        try:
            subject = f"Bienvenido a {config('COMPANY_NAME')} - Credenciales de Acceso"
            to_email = employee.persona.email

            context = {
                'employee_name': employee.persona.nombre1,
                'full_name': f"{employee.persona.nombre1} {employee.persona.apellido1}",
                'username': employee.usuario.username,
                'password': password,
                'title': f"Bienvenido a {config('COMPANY_NAME')}",
                'subtitle': 'Tu cuenta ha sido creada exitosamente',
            }

            return EmailService.send_email_from_template(
                to_email=to_email,
                subject=subject,
                template_name='credenciales',
                context=context
            )

        except Exception as e:
            logger.error(f"Error enviando credenciales: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def send_password_reset(employee, new_password):
        """Enviar email de reset de contraseña"""
        try:
            subject = "Contraseña Reseteada - Acción Requerida"
            to_email = employee.persona.email

            context = {
                'employee_name': employee.persona.nombre1,
                'password': new_password,
                'title': 'Contraseña Reseteada',
                'subtitle': 'Tu contraseña ha sido actualizada por motivos de seguridad',
            }

            return EmailService.send_email_from_template(
                to_email=to_email,
                subject=subject,
                template_name='resetear_contraseña',
                context=context
            )

        except Exception as e:
            logger.error(f"Error enviando email de reset: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def send_notification(employee, subject_text, title, subtitle, message, cta_text=None, cta_url=None):
        """
        Enviar notificación genérica

        Args:
            employee: Objeto empleado
            subject_text: Asunto del email
            title: Título principal
            subtitle: Subtítulo
            message: Contenido del mensaje
            cta_text: Texto del botón (opcional)
            cta_url: URL del botón (opcional)
        """
        try:
            to_email = employee.persona.email

            context = {
                'employee_name': employee.persona.nombre1,
                'title': title,
                'subtitle': subtitle,
                'message': message,
                'cta_text': cta_text,
                'cta_url': cta_url,
            }

            return EmailService.send_email_from_template(
                to_email=to_email,
                subject=subject_text,
                template_name='notificaciones',
                context=context
            )

        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return False, f"Error: {str(e)}"