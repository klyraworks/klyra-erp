# apps/inventario/management/commands/setup_inventario_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.inventario.models import (
    Producto, Categoria, Marca, Bodega, Stock,
    MovimientoInventario, AjusteInventario, KitComponente
)
import logging


class Command(BaseCommand):
    """
    Configura roles y permisos estándar del módulo Inventario.

    Uso:
        python manage.py setup_inventario_roles
        python manage.py setup_inventario_roles --force
    """

    help = 'Configura roles y permisos del módulo Inventario'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.inventario')

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES INVENTARIO'))
            self.stdout.write(self.style.WARNING('=' * 60))

            content_types = self._obtener_content_types()

            with transaction.atomic():
                roles_creados = [
                    self._crear_rol_asistente(content_types, options['force']),
                    self._crear_rol_supervisor(content_types, options['force']),
                    self._crear_rol_gerente(content_types, options['force'])
                ]

            self._mostrar_resumen(roles_creados)

        except Exception as e:
            self.logger.error(f"Error en setup_inventario_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_content_types(self):
        self.stdout.write('Obteniendo content types...')

        return {
            'producto': ContentType.objects.get_for_model(Producto),
            'categoria': ContentType.objects.get_for_model(Categoria),
            'marca': ContentType.objects.get_for_model(Marca),
            'bodega': ContentType.objects.get_for_model(Bodega),
            'stock': ContentType.objects.get_for_model(Stock),
            'movimiento': ContentType.objects.get_for_model(MovimientoInventario),
            'ajuste': ContentType.objects.get_for_model(AjusteInventario),
            'kit': ContentType.objects.get_for_model(KitComponente),
        }

    def _crear_rol_asistente(self, content_types, force):
        nombre_rol = 'Inventario | Asistente de Inventario'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['view_producto']
        ) | Permission.objects.filter(
            content_type=content_types['categoria'],
            codename__in=['view_categoria', 'ver_jerarquia_categorias']
        ) | Permission.objects.filter(
            content_type=content_types['marca'],
            codename__in=['view_marca']
        ) | Permission.objects.filter(
            content_type=content_types['bodega'],
            codename__in=['view_bodega']
        ) | Permission.objects.filter(
            content_type=content_types['stock'],
            codename__in=['view_stock']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento'],
            codename__in=['view_movimientoinventario']
        ) | Permission.objects.filter(
            content_type=content_types['kit'],
            codename__in=['view_kitcomponente', 'ver_composicion_kit']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_supervisor(self, content_types, force):
        nombre_rol = 'Inventario | Supervisor de Inventario'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['producto'],
            codename__in=['add_producto', 'view_producto', 'change_producto', 'delete_producto',
                         'ajustar_stock', 'ver_reportes_producto', 'gestionar_kits']
        ) | Permission.objects.filter(
            content_type=content_types['categoria'],
            codename__in=['add_categoria', 'view_categoria', 'change_categoria', 'delete_categoria',
                         'ver_jerarquia_categorias']
        ) | Permission.objects.filter(
            content_type=content_types['marca'],
            codename__in=['add_marca', 'view_marca', 'change_marca', 'delete_marca']
        ) | Permission.objects.filter(
            content_type=content_types['bodega'],
            codename__in=['add_bodega', 'view_bodega', 'change_bodega', 'ver_todas_bodegas',
                         'transferir_entre_bodegas']
        ) | Permission.objects.filter(
            content_type=content_types['stock'],
            codename__in=['view_stock', 'view_stock_todas_bodegas', 'exportar_stock']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento'],
            codename__in=['add_movimientoinventario', 'view_movimientoinventario',
                         'change_movimientoinventario', 'autorizar_movimiento',
                         'ver_todos_movimientos', 'ver_kardex']
        ) | Permission.objects.filter(
            content_type=content_types['ajuste'],
            codename__in=['add_ajusteinventario', 'view_ajusteinventario',
                         'change_ajusteinventario', 'realizar_conteo_fisico']
        ) | Permission.objects.filter(
            content_type=content_types['kit'],
            codename__in=['add_kitcomponente', 'view_kitcomponente', 'change_kitcomponente',
                         'delete_kitcomponente', 'ver_composicion_kit']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_gerente(self, content_types, force):
        nombre_rol = 'Inventario | Gerente de Inventario'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type__in=[
                content_types['producto'],
                content_types['categoria'],
                content_types['marca'],
                content_types['bodega'],
                content_types['stock'],
                content_types['movimiento'],
                content_types['ajuste'],
                content_types['kit']
            ]
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