# utils/pdf_generator.py

import logging
from io import BytesIO
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.utils import timezone
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger('pdf_generator')


class FacturaPDFGenerator:
    """
    Generador de PDF para facturas usando WeasyPrint.
    Mantiene compatibilidad con el código existente.
    """

    def __init__(self, venta, empresa):
        """
        Args:
            venta: Instancia del modelo Venta
            empresa: Instancia del modelo Empresa
        """
        self.venta = venta
        self.empresa = empresa
        self.font_config = FontConfiguration()

    def generar_html(self):
        """
        Genera el HTML de la factura usando el template.

        Returns:
            str: HTML renderizado
        """
        try:
            context = {
                'venta': self.venta,
                'empresa': self.empresa,
            }

            html_string = render_to_string(
                'facturas/factura_template.html',
                context
            )

            return html_string

        except Exception as e:
            logger.error(f"Error generando HTML de factura: {str(e)}")
            raise

    def generar_pdf(self):
        """
        Genera el PDF de la factura.

        Returns:
            BytesIO: Archivo PDF en memoria
        """
        try:
            # Generar HTML
            html_string = self.generar_html()

            # Crear PDF con WeasyPrint
            html = HTML(string=html_string)
            pdf_file = BytesIO()

            html.write_pdf(
                pdf_file,
                font_config=self.font_config
            )

            pdf_file.seek(0)

            logger.info(
                f"PDF generado para factura {self.venta.numero_factura}",
                extra={
                    'venta_id': str(self.venta.id),
                    'numero_factura': self.venta.numero_factura
                }
            )

            return pdf_file

        except Exception as e:
            logger.error(
                f"Error generando PDF de factura {self.venta.numero_factura}: {str(e)}"
            )
            raise

    def guardar_pdf(self):
        """
        Genera el PDF y lo guarda en el modelo Venta.

        Returns:
            str: Path del archivo guardado
        """
        try:
            # Generar PDF
            pdf_file = self.generar_pdf()

            # Guardar en el modelo
            filename = f"factura_{self.venta.numero_factura.replace('-', '_')}.pdf"

            self.venta.pdf_factura.save(
                filename,
                ContentFile(pdf_file.read()),
                save=True
            )

            logger.info(
                f"PDF guardado: {self.venta.pdf_factura.url}",
                extra={
                    'venta_id': str(self.venta.id),
                    'filename': filename
                }
            )

            return self.venta.pdf_factura.url

        except Exception as e:
            logger.error(f"Error guardando PDF: {str(e)}")
            raise

    @classmethod
    def generar_y_guardar(cls, venta, empresa):
        """
        Método de conveniencia para generar y guardar en un solo paso.

        Args:
            venta: Instancia del modelo Venta
            empresa: Instancia del modelo Empresa

        Returns:
            str: URL del PDF guardado
        """
        generator = cls(venta, empresa)
        return generator.guardar_pdf()





# # utils/pdf_generator.py
#
# import logging
# from io import BytesIO
# from django.template.loader import render_to_string
# from django.core.files.base import ContentFile
# from weasyprint import HTML, CSS
# from weasyprint.text.fonts import FontConfiguration
#
# logger = logging.getLogger('pdf_generator')
#
#
# class FacturaPDFGenerator:
#     """
#     Generador de PDF para facturas usando WeasyPrint.
#     """
#
#     def __init__(self, venta, empresa):
#         """
#         Args:
#             venta: Instancia del modelo Venta
#             empresa: Instancia del modelo Empresa
#         """
#         self.venta = venta
#         self.empresa = empresa
#         self.font_config = FontConfiguration()
#
#     def generar_html(self):
#         """
#         Genera el HTML de la factura usando el template.
#
#         Returns:
#             str: HTML renderizado
#         """
#         try:
#             context = {
#                 'venta': self.venta,
#                 'empresa': self.empresa,
#             }
#
#             html_string = render_to_string(
#                 'facturas/factura_template.html',
#                 context
#             )
#
#             return html_string
#
#         except Exception as e:
#             logger.error(f"Error generando HTML de factura: {str(e)}")
#             raise
#
#     def generar_pdf(self):
#         """
#         Genera el PDF de la factura.
#
#         Returns:
#             BytesIO: Archivo PDF en memoria
#         """
#         try:
#             # Generar HTML
#             html_string = self.generar_html()
#
#             # Crear PDF con WeasyPrint
#             html = HTML(string=html_string)
#             pdf_file = BytesIO()
#
#             html.write_pdf(
#                 pdf_file,
#                 font_config=self.font_config
#             )
#
#             pdf_file.seek(0)
#
#             logger.info(
#                 f"PDF generado para factura {self.venta.numero_factura}",
#                 extra={
#                     'venta_id': str(self.venta.id),
#                     'numero_factura': self.venta.numero_factura
#                 }
#             )
#
#             return pdf_file
#
#         except Exception as e:
#             logger.error(
#                 f"Error generando PDF de factura {self.venta.numero_factura}: {str(e)}"
#             )
#             raise
#
#     def guardar_pdf(self):
#         """
#         Genera el PDF y lo guarda en el modelo Venta.
#
#         Returns:
#             str: Path del archivo guardado
#         """
#         try:
#             # Generar PDF
#             pdf_file = self.generar_pdf()
#
#             # Guardar en el modelo
#             filename = f"factura_{self.venta.numero_factura.replace('-', '_')}.pdf"
#
#             self.venta.pdf_factura.save(
#                 filename,
#                 ContentFile(pdf_file.read()),
#                 save=True
#             )
#
#             logger.info(
#                 f"PDF guardado: {self.venta.pdf_factura.url}",
#                 extra={
#                     'venta_id': str(self.venta.id),
#                     'filename': filename
#                 }
#             )
#
#             return self.venta.pdf_factura.url
#
#         except Exception as e:
#             logger.error(f"Error guardando PDF: {str(e)}")
#             raise
#
#     @classmethod
#     def generar_y_guardar(cls, venta, empresa):
#         """
#         Método de conveniencia para generar y guardar en un solo paso.
#
#         Args:
#             venta: Instancia del modelo Venta
#             empresa: Instancia del modelo Empresa
#
#         Returns:
#             str: URL del PDF guardado
#         """
#         generator = cls(venta, empresa)
#         return generator.guardar_pdf()
#
#
# # ==================== FUNCIÓN DE ENVÍO DE EMAIL ====================
#
# from django.core.mail import EmailMessage
# from django.conf import settings
#
#
# def enviar_factura_por_email(venta, empresa, config_correo):
#     """
#     Envía la factura por correo electrónico al cliente.
#
#     Args:
#         venta: Instancia del modelo Venta
#         empresa: Instancia del modelo Empresa
#         config_correo: Instancia de ConfiguracionCorreo
#
#     Returns:
#         bool: True si se envió correctamente
#     """
#     try:
#         # Preparar datos para el mensaje
#         cliente_nombre = (
#                 venta.cliente.razon_social or
#                 venta.cliente.persona.full_name()
#         )
#
#         # Formatear asunto
#         asunto = config_correo.asunto_factura.format(
#             numero=venta.numero_factura
#         )
#
#         # Formatear mensaje
#         mensaje = config_correo.mensaje_factura.format(
#             cliente=cliente_nombre,
#             numero=venta.numero_factura,
#             total=venta.total,
#             empresa=empresa.nombre_comercial,
#             fecha=venta.fecha_factura.strftime('%d/%m/%Y')
#         )
#
#         # Email del destinatario
#         email_destinatario = (
#                 venta.cliente.email_facturacion or
#                 venta.cliente.persona.email
#         )
#
#         # Crear email
#         email = EmailMessage(
#             subject=asunto,
#             body=mensaje,
#             from_email=f"{config_correo.nombre_remitente} <{config_correo.email_remitente}>",
#             to=[email_destinatario],
#             reply_to=[empresa.email]
#         )
#
#         # Adjuntar PDF
#         if venta.pdf_factura:
#             pdf_filename = f"factura_{venta.numero_factura}.pdf"
#
#             # Leer el archivo PDF
#             venta.pdf_factura.open('rb')
#             pdf_content = venta.pdf_factura.read()
#             venta.pdf_factura.close()
#
#             email.attach(
#                 pdf_filename,
#                 pdf_content,
#                 'application/pdf'
#             )
#
#         # Enviar
#         email.send(fail_silently=False)
#
#         # Actualizar venta
#         from django.utils import timezone
#         venta.correo_enviado = True
#         venta.fecha_envio_correo = timezone.now()
#         venta.save(update_fields=['correo_enviado', 'fecha_envio_correo'])
#
#         logger.info(
#             f"Factura enviada por email: {venta.numero_factura} -> {email_destinatario}",
#             extra={
#                 'venta_id': str(venta.id),
#                 'email_destinatario': email_destinatario
#             }
#         )
#
#         return True
#
#     except Exception as e:
#         logger.error(
#             f"Error enviando factura por email: {str(e)}",
#             extra={
#                 'venta_id': str(venta.id),
#                 'error': str(e)
#             }
#         )
#         raise
#
#
# def generar_factura_completa(venta):
#     """
#     Proceso completo: Genera PDF y envía por email.
#
#     Args:
#         venta: Instancia del modelo Venta
#
#     Returns:
#         dict: Resultado del proceso
#     """
#     from apps.core.models import Empresa, ConfiguracionCorreo
#     from django.utils import timezone
#
#     try:
#         # Obtener empresa activa
#         empresa = Empresa.get_empresa_activa()
#
#         # Asignar número de factura si no tiene
#         if not venta.numero_factura:
#             venta.numero_factura = empresa.generar_numero_factura()
#             venta.fecha_factura = empresa.obtener_fecha_empresa()
#             venta.estado = 'facturada'
#             venta.save()
#
#         # Generar PDF
#         pdf_url = FacturaPDFGenerator.generar_y_guardar(venta, empresa)
#
#         # Enviar por email
#         try:
#             config_correo = ConfiguracionCorreo.objects.get(empresa=empresa)
#             enviar_factura_por_email(venta, empresa, config_correo)
#             email_enviado = True
#         except ConfiguracionCorreo.DoesNotExist:
#             logger.warning("No hay configuración de correo. PDF generado pero no enviado.")
#             email_enviado = False
#         except Exception as e:
#             logger.error(f"Error enviando email: {str(e)}")
#             email_enviado = False
#
#         return {
#             'success': True,
#             'numero_factura': venta.numero_factura,
#             'pdf_url': pdf_url,
#             'email_enviado': email_enviado
#         }
#
#     except Exception as e:
#         logger.error(f"Error en proceso completo de facturación: {str(e)}")
#         return {
#             'success': False,
#             'error': str(e)
#         }