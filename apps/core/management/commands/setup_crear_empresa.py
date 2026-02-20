# apps/core/management/commands/setup_crear_empresa.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decouple import config
from apps.core.models import Empresa, ConfiguracionCorreo
import logging


class Command(BaseCommand):
    """
    Crea una empresa con configuración inicial.

    Uso:
        python manage.py setup_crear_empresa
        python manage.py setup_crear_empresa --ruc=0999999999001 --razon-social="MI EMPRESA S.A."
        python manage.py setup_crear_empresa --template=klyra
        python manage.py setup_crear_empresa --set-active
    """

    help = 'Crea una empresa con configuración inicial'

    TEMPLATES = {
        'klyra': {
            'ruc': '0999999999001',
            'razon_social': 'KLYRA SISTEMAS Y SOLUCIONES S.A.',
            'nombre_comercial': 'Klyra',
            'subdominio': 'klyra',
            'ciudad': 'Guayaquil',
            'provincia': 'Guayas',
            'color_primario': '#1E40AF',
            'slogan': 'Soluciones tecnológicas a tu medida'
        },
        'demo': {
            'ruc': '0988888888001',
            'razon_social': 'EMPRESA DEMO S.A.',
            'nombre_comercial': 'Demo',
            'subdominio': 'demo',
            'ciudad': 'Quito',
            'provincia': 'Pichincha',
            'color_primario': '#059669',
            'slogan': 'Tu aliado comercial'
        }
    }

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            '--template',
            type=str,
            choices=['klyra', 'demo'],
            help='Usar template predefinido (klyra o demo)'
        )
        parser.add_argument(
            '--ruc',
            type=str,
            help='RUC de la empresa (13 dígitos)'
        )
        parser.add_argument(
            '--razon-social',
            type=str,
            help='Razón social de la empresa'
        )
        parser.add_argument(
            '--nombre-comercial',
            type=str,
            help='Nombre comercial de la empresa'
        )
        parser.add_argument(
            '--subdominio',
            type=str,
            help='Subdominio de la empresa'
        )
        parser.add_argument(
            '--set-active',
            action='store_true',
            help='Marcar como empresa activa (desactiva las demás)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Actualizar si ya existe'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CREACIÓN DE EMPRESA'))
            self.stdout.write(self.style.WARNING('=' * 60))

            datos_empresa = self._preparar_datos_empresa(options)

            if not datos_empresa:
                raise CommandError('Debe especificar --template o proporcionar --ruc y --razon-social')

            with transaction.atomic():
                if options['set_active']:
                    self._desactivar_empresas_activas()

                empresa, created = self._crear_empresa(datos_empresa, options['force'])
                config_correo, config_created = self._crear_configuracion_correo(empresa)

            self._mostrar_resumen(empresa, created, config_created)

        except Exception as e:
            self.logger.error(f"Error en setup_crear_empresa: {str(e)}", exc_info=True)
            raise CommandError(f'Error al crear empresa: {str(e)}')

    def _preparar_datos_empresa(self, options):
        if options.get('template'):
            template = self.TEMPLATES[options['template']]
            self.stdout.write(f'\nUsando template: {options["template"]}')
            return template

        if options.get('ruc') and options.get('razon_social'):
            return {
                'ruc': options['ruc'],
                'razon_social': options['razon_social'],
                'nombre_comercial': options.get('nombre_comercial') or options['razon_social'],
                'subdominio': options.get('subdominio') or 'empresa',
                'ciudad': 'Guayaquil',
                'provincia': 'Guayas',
                'color_primario': '#1E40AF',
                'slogan': 'Excelencia empresarial'
            }

        return None

    def _desactivar_empresas_activas(self):
        count = Empresa.objects.filter(is_active=True).update(is_active=False)
        if count > 0:
            self.stdout.write(self.style.WARNING(f'✓ {count} empresa(s) desactivada(s)'))
            self.logger.info(f"{count} empresas desactivadas")

    def _crear_empresa(self, datos, force):
        ruc = datos['ruc']

        if Empresa.objects.filter(ruc=ruc).exists() and not force:
            raise CommandError(f'Ya existe una empresa con RUC {ruc}. Use --force para actualizar')

        empresa, created = Empresa.objects.update_or_create(
            ruc=ruc,
            defaults={
                'razon_social': datos['razon_social'],
                'nombre_comercial': datos['nombre_comercial'],
                'subdominio': datos['subdominio'],

                # Ubicación
                'direccion_matriz': 'Dirección de la empresa',
                'ciudad': datos['ciudad'],
                'provincia': datos['provincia'],
                'pais': 'Ecuador',
                'codigo_postal': '090101',

                # Contacto
                'telefono': '04-0000000',
                'celular': '0900000000',
                'email': config('EMAIL_HOST_USER', default='info@empresa.com'),
                'sitio_web': config('SITE_URL', default='https://empresa.com'),

                # Tributario
                'obligado_contabilidad': True,
                'contribuyente_especial': None,
                'agente_retencion': False,

                # SRI - Ambiente de PRUEBAS
                'ambiente_sri': '1',
                'tipo_emision': '1',

                # Establecimiento
                'establecimiento': '001',
                'punto_emision': '001',

                # Secuenciales
                'secuencial_factura': 1,
                'secuencial_nota_credito': 1,
                'secuencial_nota_debito': 1,
                'secuencial_guia_remision': 1,
                'secuencial_retencion': 1,

                # Branding
                'color_primario': datos['color_primario'],
                'slogan': datos['slogan'],

                # Configuración
                'dias_validez_factura': 30,
                'leyenda_factura': (
                    'Este documento es una representación impresa de una factura electrónica.\n'
                    'Para consultar la validez de esta factura, ingrese a:\n'
                    'https://srienlinea.sri.gob.ec/facturacion-internet/consultas/publico/comprobantes.jspa'
                ),
                'informacion_adicional': f'Gracias por su compra. {datos["nombre_comercial"]}',

                # Estado
                'is_active': True
            }
        )

        return empresa, created

    def _crear_configuracion_correo(self, empresa):
        config_correo, created = ConfiguracionCorreo.objects.update_or_create(
            empresa=empresa,
            defaults={
                'servidor_smtp': config('EMAIL_HOST', default='smtp.gmail.com'),
                'puerto_smtp': config('EMAIL_PORT', default=587),
                'usar_tls': config('EMAIL_USE_TLS', default=True, cast=bool),
                'email_remitente': config('EMAIL_HOST_USER', default='noreply@empresa.com'),
                'nombre_remitente': f'Facturación - {empresa.nombre_comercial}',
                'password_email': config('EMAIL_HOST_PASSWORD', default=''),

                'asunto_factura': f'Factura Electrónica #{{numero}} - {empresa.nombre_comercial}',
                'mensaje_factura': f'''Estimado/a {{cliente}},

                Adjunto encontrará su factura electrónica #{{numero}} por un valor de ${{total}}.
                
                Detalles de la compra:
                - Número de factura: {{numero}}
                - Fecha: {{fecha}}
                - Total: ${{total}}
                
                Puede consultar la validez de esta factura en:
                https://srienlinea.sri.gob.ec/facturacion-internet/consultas/publico/comprobantes.jspa
                
                Gracias por su preferencia.
                
                Saludos cordiales,
                {empresa.nombre_comercial}
                {empresa.sitio_web}
                ''',
            }
        )

        return config_correo, created

    def _mostrar_resumen(self, empresa, created, config_created):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('EMPRESA CREADA EXITOSAMENTE' if created else 'EMPRESA ACTUALIZADA'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'RUC: {empresa.ruc}')
        self.stdout.write(f'Razón Social: {empresa.razon_social}')
        self.stdout.write(f'Nombre Comercial: {empresa.nombre_comercial}')
        self.stdout.write(f'Subdominio: {empresa.subdominio}')
        self.stdout.write(f'Email: {empresa.email}')
        self.stdout.write(f'Ambiente SRI: {"PRUEBAS" if empresa.ambiente_sri == "1" else "PRODUCCIÓN"}')
        self.stdout.write(f'Establecimiento: {empresa.establecimiento}')
        self.stdout.write(f'Punto de Emisión: {empresa.punto_emision}')
        self.stdout.write(f'Estado: {"ACTIVA" if empresa.is_active else "INACTIVA"}')
        self.stdout.write(f'Configuración de correo: {"Creada" if config_created else "Actualizada"}')
        self.stdout.write('=' * 60)

        self.stdout.write(self.style.WARNING(
            '\n💡 NOTA: Esta empresa está configurada en MODO PRUEBAS del SRI.\n'
            '   Para producción, cambia ambiente_sri a "2" y configura el certificado digital.'
        ))

        self.logger.info(f"Empresa {'creada' if created else 'actualizada'}: {empresa.nombre_comercial}")
