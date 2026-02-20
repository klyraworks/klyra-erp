# apps/seguridad/management/commands/setup_roles_empresa.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.db import transaction
from apps.core.models import Empresa
from apps.seguridad.models import Rol
import logging


class Command(BaseCommand):
    """
    Crea los Roles de negocio por empresa, enlazándolos a los grupos Django existentes.

    Uso:
        python manage.py setup_roles_empresa
        python manage.py setup_roles_empresa --empresa=UUID
        python manage.py setup_roles_empresa --force
    """

    help = 'Crea roles de negocio por empresa enlazados a grupos Django'

    ROLES_CONFIG = [
        # ==================== RRHH ====================
        {
            'nombre': 'Supervisor RRHH',
            'nivel_jerarquico': 3,
            'grupos_django': ['RRHH | Supervisor'],
            'puede_aprobar_vacaciones': True,
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Asistente RRHH',
            'nivel_jerarquico': 2,
            'grupos_django': ['RRHH | Asistente RRHH'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Gerente RRHH',
            'nivel_jerarquico': 7,
            'grupos_django': ['RRHH | Gerente RRHH'],
            'puede_aprobar_vacaciones': True,
            'puede_ver_salarios': True,
            'puede_anular_documentos': True,
            'monto_maximo_aprobacion': 10000,
            'monto_maximo_descuento': 0,
        },

        # ==================== VENTAS ====================
        {
            'nombre': 'Cajero',
            'nivel_jerarquico': 1,
            'grupos_django': ['Ventas | Cajero'],
            'monto_maximo_descuento': 0,
            'monto_maximo_aprobacion': 0,
        },
        {
            'nombre': 'Vendedor',
            'nivel_jerarquico': 2,
            'grupos_django': ['Ventas | Vendedor'],
            'monto_maximo_descuento': 5,
            'monto_maximo_aprobacion': 0,
            'limite_credito_clientes': 1000,
        },
        {
            'nombre': 'Supervisor de Ventas',
            'nivel_jerarquico': 5,
            'grupos_django': ['Ventas | Supervisor de Ventas'],
            'monto_maximo_descuento': 15,
            'monto_maximo_aprobacion': 5000,
            'limite_credito_clientes': 5000,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Gerente de Ventas',
            'nivel_jerarquico': 7,
            'grupos_django': ['Ventas | Gerente de Ventas'],
            'monto_maximo_descuento': 30,
            'monto_maximo_aprobacion': 50000,
            'limite_credito_clientes': 20000,
            'puede_modificar_precios': True,
            'puede_anular_documentos': True,
        },

        # ==================== COMPRAS ====================
        {
            'nombre': 'Solicitante',
            'nivel_jerarquico': 1,
            'grupos_django': ['Compras | Solicitante'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Comprador',
            'nivel_jerarquico': 3,
            'grupos_django': ['Compras | Comprador'],
            'monto_maximo_aprobacion': 5000,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Recepción',
            'nivel_jerarquico': 2,
            'grupos_django': ['Compras | Recepción'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Jefe de Compras',
            'nivel_jerarquico': 6,
            'grupos_django': ['Compras | Jefe de Compras'],
            'monto_maximo_aprobacion': 50000,
            'monto_maximo_descuento': 10,
            'puede_anular_documentos': True,
        },

        # ==================== INVENTARIO ====================
        {
            'nombre': 'Asistente de Inventario',
            'nivel_jerarquico': 2,
            'grupos_django': ['Inventario | Asistente de Inventario'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Supervisor de Inventario',
            'nivel_jerarquico': 5,
            'grupos_django': ['Inventario | Supervisor de Inventario'],
            'monto_maximo_aprobacion': 5000,
            'monto_maximo_descuento': 0,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Gerente de Inventario',
            'nivel_jerarquico': 7,
            'grupos_django': ['Inventario | Gerente de Inventario'],
            'monto_maximo_aprobacion': 20000,
            'monto_maximo_descuento': 0,
            'puede_modificar_precios': True,
            'puede_anular_documentos': True,
        },

        # ==================== FINANZAS ====================
        {
            'nombre': 'Asistente Contable',
            'nivel_jerarquico': 2,
            'grupos_django': ['Finanzas | Asistente Contable'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
        },
        {
            'nombre': 'Contador',
            'nivel_jerarquico': 5,
            'grupos_django': ['Finanzas | Contador'],
            'monto_maximo_aprobacion': 10000,
            'monto_maximo_descuento': 0,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Analista Financiero',
            'nivel_jerarquico': 4,
            'grupos_django': ['Finanzas | Analista Financiero'],
            'monto_maximo_aprobacion': 0,
            'monto_maximo_descuento': 0,
            'puede_ver_salarios': True,
        },
        {
            'nombre': 'Gerente de Cobranzas',
            'nivel_jerarquico': 6,
            'grupos_django': ['Finanzas | Gerente de Cobranzas'],
            'monto_maximo_aprobacion': 20000,
            'monto_maximo_descuento': 0,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Tesorero',
            'nivel_jerarquico': 6,
            'grupos_django': ['Finanzas | Tesorero'],
            'monto_maximo_aprobacion': 50000,
            'monto_maximo_descuento': 0,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Gerente Financiero',
            'nivel_jerarquico': 8,
            'grupos_django': ['Finanzas | Gerente Financiero'],
            'monto_maximo_aprobacion': 100000,
            'monto_maximo_descuento': 0,
            'puede_ver_salarios': True,
            'puede_anular_documentos': True,
        },

        # ==================== SUPERIORES ====================
        {
            'nombre': 'Director de Operaciones',
            'nivel_jerarquico': 8,
            'grupos_django': ['Director de Operaciones'],
            'monto_maximo_aprobacion': 100000,
            'monto_maximo_descuento': 20,
            'puede_aprobar_vacaciones': True,
            'puede_ver_salarios': True,
            'puede_modificar_precios': True,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Director Financiero',
            'nivel_jerarquico': 9,
            'grupos_django': ['Director Financiero'],
            'monto_maximo_aprobacion': 500000,
            'monto_maximo_descuento': 30,
            'puede_aprobar_vacaciones': True,
            'puede_ver_salarios': True,
            'puede_modificar_precios': True,
            'puede_anular_documentos': True,
        },
        {
            'nombre': 'Gerente General',
            'nivel_jerarquico': 10,
            'grupos_django': ['Gerente General'],
            'monto_maximo_aprobacion': 999999999,
            'monto_maximo_descuento': 100,
            'limite_credito_clientes': 999999999,
            'puede_aprobar_vacaciones': True,
            'puede_ver_salarios': True,
            'puede_modificar_precios': True,
            'puede_anular_documentos': True,
        },
    ]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.seguridad')

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            help='UUID de la empresa (opcional, usa la empresa activa si no se especifica)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES DE EMPRESA'))
            self.stdout.write(self.style.WARNING('=' * 60))

            empresa = self._obtener_empresa(options)

            with transaction.atomic():
                roles_resultado = self._crear_roles(empresa, options['force'])

            self._mostrar_resumen(roles_resultado)

        except Exception as e:
            self.logger.error(f"Error en setup_roles_empresa: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_empresa(self, options):
        if options.get('empresa'):
            try:
                return Empresa.objects.get(id=options['empresa'])
            except Empresa.DoesNotExist:
                raise CommandError(f'Empresa con ID {options["empresa"]} no encontrada')

        empresa = Empresa.objects.filter(is_active=True).first()
        if not empresa:
            raise CommandError('No se encontró empresa activa. Especifica --empresa=UUID')

        self.stdout.write(f'\nUsando empresa activa: {empresa.nombre_comercial}')
        return empresa

    def _crear_roles(self, empresa, force):
        self.stdout.write(f'\n📁 Empresa: {empresa.nombre_comercial}\n')

        creados = 0
        actualizados = 0
        omitidos = 0

        for config in self.ROLES_CONFIG:
            nombre = config['nombre']

            # Verificar grupos Django disponibles
            grupos = []
            for nombre_grupo in config.get('grupos_django', []):
                try:
                    grupos.append(Group.objects.get(name=nombre_grupo))
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠ Grupo "{nombre_grupo}" no encontrado, omitiendo rol "{nombre}"'
                    ))
                    omitidos += 1
                    continue

            rol, created = Rol.objects.get_or_create(
                nombre=nombre,
                empresa=empresa,
                defaults={
                    'nivel_jerarquico': config.get('nivel_jerarquico', 1),
                    'monto_maximo_descuento': config.get('monto_maximo_descuento', 0),
                    'monto_maximo_aprobacion': config.get('monto_maximo_aprobacion', 0),
                    'limite_credito_clientes': config.get('limite_credito_clientes', 0),
                    'puede_aprobar_vacaciones': config.get('puede_aprobar_vacaciones', False),
                    'puede_ver_salarios': config.get('puede_ver_salarios', False),
                    'puede_modificar_precios': config.get('puede_modificar_precios', False),
                    'puede_anular_documentos': config.get('puede_anular_documentos', False),
                }
            )

            if not created and force:
                rol.nivel_jerarquico = config.get('nivel_jerarquico', 1)
                rol.monto_maximo_descuento = config.get('monto_maximo_descuento', 0)
                rol.monto_maximo_aprobacion = config.get('monto_maximo_aprobacion', 0)
                rol.limite_credito_clientes = config.get('limite_credito_clientes', 0)
                rol.puede_aprobar_vacaciones = config.get('puede_aprobar_vacaciones', False)
                rol.puede_ver_salarios = config.get('puede_ver_salarios', False)
                rol.puede_modificar_precios = config.get('puede_modificar_precios', False)
                rol.puede_anular_documentos = config.get('puede_anular_documentos', False)
                rol.save()

            rol.grupos_django.set(grupos)

            if created:
                creados += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Creado: {nombre}'))
                self.logger.info(f"Rol creado: {nombre} | Empresa: {empresa.nombre_comercial}")
            elif force:
                actualizados += 1
                self.stdout.write(self.style.WARNING(f'  ⟳ Actualizado: {nombre}'))
                self.logger.info(f"Rol actualizado: {nombre} | Empresa: {empresa.nombre_comercial}")
            else:
                omitidos += 1
                self.stdout.write(f'  - Ya existe: {nombre}')

        return {'creados': creados, 'actualizados': actualizados, 'omitidos': omitidos}

    def _mostrar_resumen(self, resultado):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE CONFIGURACIÓN'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Creados: {resultado["creados"]}'))
        self.stdout.write(f'  ⟳ Actualizados: {resultado["actualizados"]}')
        self.stdout.write(f'  - Omitidos: {resultado["omitidos"]}')
        self.stdout.write('=' * 60)