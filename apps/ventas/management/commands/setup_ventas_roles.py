# apps/ventas/management/commands/setup_ventas_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.ventas.models import Venta, Cotizacion, Pago
from apps.personas.models import Cliente
from apps.inventario.models import Producto
import logging


class Command(BaseCommand):
    """
    Configura roles y permisos estándar del módulo Ventas.

    Uso:
        python manage.py setup_ventas_roles
        python manage.py setup_ventas_roles --force
    """

    help = 'Configura roles y permisos del módulo Ventas'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.ventas')

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES VENTAS'))
            self.stdout.write(self.style.WARNING('=' * 60))

            content_types = self._obtener_content_types()

            with transaction.atomic():
                roles_creados = [
                    self._crear_rol_vendedor(content_types, options['force']),
                    self._crear_rol_supervisor(content_types, options['force']),
                    self._crear_rol_gerente(content_types, options['force']),
                    self._crear_rol_cajero(content_types, options['force'])
                ]

            self._mostrar_resumen(roles_creados)

        except Exception as e:
            self.logger.error(f"Error en setup_ventas_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_content_types(self):
        self.stdout.write('Obteniendo content types...')

        return {
            'cliente': ContentType.objects.get_for_model(Cliente),
            'venta': ContentType.objects.get_for_model(Venta),
            'cotizacion': ContentType.objects.get_for_model(Cotizacion),
            'pago': ContentType.objects.get_for_model(Pago),
            'producto': ContentType.objects.get_for_model(Producto),
        }

    def _crear_rol_vendedor(self, content_types, force):
        nombre_rol = 'Ventas | Vendedor'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['cliente'],
            codename__in=['add_cliente', 'view_cliente', 'change_cliente']
        ) | Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['view_producto']
        ) | Permission.objects.filter(
            content_type=content_types['venta'],
            codename__in=['add_venta', 'view_venta', 'change_venta']
        ) | Permission.objects.filter(
            content_type=content_types['cotizacion'],
            codename__in=['add_cotizacion', 'view_cotizacion', 'change_cotizacion']
        ) | Permission.objects.filter(
            content_type=content_types['pago'],
            codename__in=['add_pago', 'view_pago']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_supervisor(self, content_types, force):
        nombre_rol = 'Ventas | Supervisor de Ventas'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['cliente'],
            codename__in=['add_cliente', 'view_cliente', 'change_cliente', 'delete_cliente',
                         'ver_historial_compras', 'gestionar_credito']
        ) | Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['view_producto']
        ) | Permission.objects.filter(
            content_type=content_types['venta'],
            codename__in=['add_venta', 'view_venta', 'change_venta', 'confirmar_venta',
                         'anular_venta', 'ver_todas_ventas']
        ) | Permission.objects.filter(
            content_type=content_types['cotizacion'],
            codename__in=['add_cotizacion', 'view_cotizacion', 'change_cotizacion',
                         'delete_cotizacion', 'convertir_cotizacion']
        ) | Permission.objects.filter(
            content_type=content_types['pago'],
            codename__in=['add_pago', 'view_pago', 'change_pago', 'delete_pago']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_gerente(self, content_types, force):
        nombre_rol = 'Ventas | Gerente de Ventas'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type__in=[
                content_types['cliente'],
                content_types['venta'],
                content_types['cotizacion'],
                content_types['pago']
            ]
        ) | Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['view_producto', 'ajustar_precios', 'ver_costo_compra']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_cajero(self, content_types, force):
        nombre_rol = 'Ventas | Cajero'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['cliente'],
            codename__in=['view_cliente']
        ) | Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['view_producto']
        ) | Permission.objects.filter(
            content_type=content_types['venta'],
            codename__in=['view_venta']
        ) | Permission.objects.filter(
            content_type=content_types['pago'],
            codename__in=['add_pago', 'view_pago']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _mostrar_resumen(self, roles):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE CONFIGURACIÓN'))
        self.stdout.write('=' * 60)

        total_creados = sum(1 for r in roles if r['creado'])
        total_actualizados = len(roles) - total_creados

        self.stdout.write(f'Roles procesados: {len(roles)}')
        self.stdout.write(self.style.SUCCESS(f'  - Creados: {total_creados}'))
        self.stdout.write(f'  - Actualizados: {total_actualizados}')

        self.stdout.write('\nDetalle de roles:')
        for rol in roles:
            estado = '✓ Creado' if rol['creado'] else '⟳ Actualizado'
            self.stdout.write(f"  {estado}: {rol['nombre']} ({rol['permisos']} permisos)")

        self.stdout.write(self.style.SUCCESS('=' * 60))