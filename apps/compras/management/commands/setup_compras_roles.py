# apps/compras/management/commands/setup_compras_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.compras.models import (
    SolicitudCompra, OrdenCompra, RecepcionMercancia
)
from apps.personas.models import Proveedor
import logging


class Command(BaseCommand):
    """
    Configura roles y permisos estándar del módulo Compras.

    Uso:
        python manage.py setup_compras_roles
        python manage.py setup_compras_roles --force
    """

    help = 'Configura roles y permisos del módulo Compras'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.compras')

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES COMPRAS'))
            self.stdout.write(self.style.WARNING('=' * 60))

            content_types = self._obtener_content_types()

            with transaction.atomic():
                roles_creados = [
                    self._crear_rol_solicitante(content_types, options['force']),
                    self._crear_rol_comprador(content_types, options['force']),
                    self._crear_rol_jefe_compras(content_types, options['force']),
                    self._crear_rol_recepcion(content_types, options['force'])
                ]

            self._mostrar_resumen(roles_creados)

        except Exception as e:
            self.logger.error(f"Error en setup_compras_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_content_types(self):
        self.stdout.write('Obteniendo content types...')

        return {
            'proveedor': ContentType.objects.get_for_model(Proveedor),
            'solicitud': ContentType.objects.get_for_model(SolicitudCompra),
            'orden_compra': ContentType.objects.get_for_model(OrdenCompra),
            'recepcion': ContentType.objects.get_for_model(RecepcionMercancia),
        }

    def _crear_rol_solicitante(self, content_types, force):
        nombre_rol = 'Compras | Solicitante'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['solicitud'],
            codename__in=['add_solicitudcompra', 'view_solicitudcompra', 'change_solicitudcompra']
        ) | Permission.objects.filter(
            content_type=content_types['proveedor'],
            codename__in=['view_proveedor']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_comprador(self, content_types, force):
        nombre_rol = 'Compras | Comprador'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['proveedor'],
            codename__in=['add_proveedor', 'change_proveedor', 'view_proveedor', 'ver_historial_compras_proveedor']
        ) | Permission.objects.filter(
            content_type=content_types['orden_compra'],
            codename__in=['add_ordencompra', 'change_ordencompra', 'view_ordencompra', 'delete_ordencompra']
        ) | Permission.objects.filter(
            content_type=content_types['solicitud'],
            codename__in=['view_solicitudcompra', 'change_solicitudcompra', 'convertir_solicitud_orden']
        ) | Permission.objects.filter(
            content_type=content_types['recepcion'],
            codename__in=['view_recepcionmercancia']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_jefe_compras(self, content_types, force):
        nombre_rol = 'Compras | Jefe de Compras'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['proveedor'],
            codename__in=['add_proveedor', 'change_proveedor', 'view_proveedor', 'delete_proveedor',
                         'ver_historial_compras_proveedor', 'gestionar_calificacion']
        ) | Permission.objects.filter(
            content_type=content_types['orden_compra'],
            codename__in=['add_ordencompra', 'change_ordencompra', 'view_ordencompra', 'delete_ordencompra',
                         'aprobar_orden_compra', 'anular_orden_compra']
        ) | Permission.objects.filter(
            content_type=content_types['recepcion'],
            codename__in=['add_recepcionmercancia', 'change_recepcionmercancia', 'view_recepcionmercancia',
                         'delete_recepcionmercancia']
        ) | Permission.objects.filter(
            content_type=content_types['solicitud'],
            codename__in=['add_solicitudcompra', 'change_solicitudcompra', 'view_solicitudcompra',
                         'delete_solicitudcompra', 'aprobar_solicitud', 'convertir_solicitud_orden']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_recepcion(self, content_types, force):
        nombre_rol = 'Compras | Recepción'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['orden_compra'],
            codename__in=['view_ordencompra', 'recibir_orden_compra']
        ) | Permission.objects.filter(
            content_type=content_types['recepcion'],
            codename__in=['add_recepcionmercancia', 'change_recepcionmercancia', 'view_recepcionmercancia']
        ) | Permission.objects.filter(
            content_type=content_types['proveedor'],
            codename__in=['view_proveedor']
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