# apps/finanzas/management/commands/setup_finanzas_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.finanzas.models import (
    PlanCuentas, AsientoContable, CuentaBancaria, MovimientoBancario,
    ConciliacionBancaria, CuentaPorCobrar, CuentaPorPagar, Presupuesto, CentroCosto
)
import logging


class Command(BaseCommand):
    """
    Configura roles y permisos estándar del módulo Finanzas.

    Uso:
        python manage.py setup_finanzas_roles
        python manage.py setup_finanzas_roles --force
    """

    help = 'Configura roles y permisos del módulo Finanzas'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.finanzas')

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES FINANZAS'))
            self.stdout.write(self.style.WARNING('=' * 60))

            content_types = self._obtener_content_types()

            with transaction.atomic():
                roles_creados = [
                    self._crear_rol_asistente_contable(content_types, options['force']),
                    self._crear_rol_contador(content_types, options['force']),
                    self._crear_rol_analista_financiero(content_types, options['force']),
                    self._crear_rol_gerente_cobranzas(content_types, options['force']),
                    self._crear_rol_tesorero(content_types, options['force']),
                    self._crear_rol_gerente_financiero(content_types, options['force'])
                ]

            self._mostrar_resumen(roles_creados)

        except Exception as e:
            self.logger.error(f"Error en setup_finanzas_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_content_types(self):
        self.stdout.write('Obteniendo content types...')

        return {
            'plan_cuentas': ContentType.objects.get_for_model(PlanCuentas),
            'asiento': ContentType.objects.get_for_model(AsientoContable),
            'cuenta_bancaria': ContentType.objects.get_for_model(CuentaBancaria),
            'movimiento_bancario': ContentType.objects.get_for_model(MovimientoBancario),
            'conciliacion': ContentType.objects.get_for_model(ConciliacionBancaria),
            'cxc': ContentType.objects.get_for_model(CuentaPorCobrar),
            'cxp': ContentType.objects.get_for_model(CuentaPorPagar),
            'presupuesto': ContentType.objects.get_for_model(Presupuesto),
            'centro_costo': ContentType.objects.get_for_model(CentroCosto),
        }

    def _crear_rol_asistente_contable(self, content_types, force):
        nombre_rol = 'Finanzas | Asistente Contable'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['plan_cuentas'],
            codename__in=['view_plancuentas']
        ) | Permission.objects.filter(
            content_type=content_types['asiento'],
            codename__in=['add_asientocontable', 'view_asientocontable', 'change_asientocontable']
        ) | Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['view_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['view_movimientobancario']
        ) | Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['view_cuentaporcobrar']
        ) | Permission.objects.filter(
            content_type=content_types['cxp'],
            codename__in=['view_cuentaporpagar']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_contador(self, content_types, force):
        nombre_rol = 'Finanzas | Contador'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['plan_cuentas'],
            codename__in=['add_plancuentas', 'change_plancuentas', 'view_plancuentas', 'gestionar_plan_cuentas']
        ) | Permission.objects.filter(
            content_type=content_types['asiento'],
            codename__in=['add_asientocontable', 'change_asientocontable', 'view_asientocontable',
                         'delete_asientocontable', 'contabilizar_asiento']
        ) | Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['add_cuentabancaria', 'change_cuentabancaria', 'view_cuentabancaria',
                         'delete_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['add_movimientobancario', 'change_movimientobancario', 'view_movimientobancario',
                         'delete_movimientobancario']
        ) | Permission.objects.filter(
            content_type=content_types['conciliacion'],
            codename__in=['add_conciliacionbancaria', 'change_conciliacionbancaria', 'view_conciliacionbancaria',
                         'delete_conciliacionbancaria']
        ) | Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['add_cuentaporcobrar', 'change_cuentaporcobrar', 'view_cuentaporcobrar',
                         'delete_cuentaporcobrar']
        ) | Permission.objects.filter(
            content_type=content_types['cxp'],
            codename__in=['add_cuentaporpagar', 'change_cuentaporpagar', 'view_cuentaporpagar',
                         'delete_cuentaporpagar']
        ) | Permission.objects.filter(
            content_type=content_types['centro_costo'],
            codename__in=['view_centrocosto']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_analista_financiero(self, content_types, force):
        nombre_rol = 'Finanzas | Analista Financiero'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['plan_cuentas'],
            codename__in=['view_plancuentas', 'ver_reportes_contables']
        ) | Permission.objects.filter(
            content_type=content_types['asiento'],
            codename__in=['view_asientocontable']
        ) | Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['view_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['view_movimientobancario']
        ) | Permission.objects.filter(
            content_type=content_types['conciliacion'],
            codename__in=['view_conciliacionbancaria']
        ) | Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['view_cuentaporcobrar']
        ) | Permission.objects.filter(
            content_type=content_types['cxp'],
            codename__in=['view_cuentaporpagar']
        ) | Permission.objects.filter(
            content_type=content_types['presupuesto'],
            codename__in=['view_presupuesto']
        ) | Permission.objects.filter(
            content_type=content_types['centro_costo'],
            codename__in=['view_centrocosto']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_gerente_cobranzas(self, content_types, force):
        nombre_rol = 'Finanzas | Gerente de Cobranzas'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['add_cuentaporcobrar', 'change_cuentaporcobrar', 'view_cuentaporcobrar',
                         'delete_cuentaporcobrar', 'gestionar_cobranza', 'declarar_incobrable']
        ) | Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['view_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['add_movimientobancario', 'view_movimientobancario']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_tesorero(self, content_types, force):
        nombre_rol = 'Finanzas | Tesorero'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['add_cuentabancaria', 'change_cuentabancaria', 'view_cuentabancaria',
                         'delete_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['add_movimientobancario', 'change_movimientobancario', 'view_movimientobancario',
                         'delete_movimientobancario']
        ) | Permission.objects.filter(
            content_type=content_types['conciliacion'],
            codename__in=['add_conciliacionbancaria', 'change_conciliacionbancaria', 'view_conciliacionbancaria',
                         'delete_conciliacionbancaria']
        ) | Permission.objects.filter(
            content_type=content_types['cxp'],
            codename__in=['add_cuentaporpagar', 'change_cuentaporpagar', 'view_cuentaporpagar']
        ) | Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['view_cuentaporcobrar']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_gerente_financiero(self, content_types, force):
        nombre_rol = 'Finanzas | Gerente Financiero'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['plan_cuentas'],
            codename__in=['add_plancuentas', 'change_plancuentas', 'view_plancuentas', 'delete_plancuentas',
                         'gestionar_plan_cuentas', 'ver_reportes_contables']
        ) | Permission.objects.filter(
            content_type=content_types['asiento'],
            codename__in=['add_asientocontable', 'change_asientocontable', 'view_asientocontable',
                         'delete_asientocontable', 'contabilizar_asiento', 'anular_asiento']
        ) | Permission.objects.filter(
            content_type=content_types['cuenta_bancaria'],
            codename__in=['add_cuentabancaria', 'change_cuentabancaria', 'view_cuentabancaria',
                         'delete_cuentabancaria']
        ) | Permission.objects.filter(
            content_type=content_types['movimiento_bancario'],
            codename__in=['add_movimientobancario', 'change_movimientobancario', 'view_movimientobancario',
                         'delete_movimientobancario']
        ) | Permission.objects.filter(
            content_type=content_types['conciliacion'],
            codename__in=['add_conciliacionbancaria', 'change_conciliacionbancaria', 'view_conciliacionbancaria',
                         'delete_conciliacionbancaria']
        ) | Permission.objects.filter(
            content_type=content_types['cxc'],
            codename__in=['add_cuentaporcobrar', 'change_cuentaporcobrar', 'view_cuentaporcobrar',
                         'delete_cuentaporcobrar', 'gestionar_cobranza', 'declarar_incobrable']
        ) | Permission.objects.filter(
            content_type=content_types['cxp'],
            codename__in=['add_cuentaporpagar', 'change_cuentaporpagar', 'view_cuentaporpagar',
                         'delete_cuentaporpagar']
        ) | Permission.objects.filter(
            content_type=content_types['presupuesto'],
            codename__in=['add_presupuesto', 'change_presupuesto', 'view_presupuesto', 'delete_presupuesto']
        ) | Permission.objects.filter(
            content_type=content_types['centro_costo'],
            codename__in=['add_centrocosto', 'change_centrocosto', 'view_centrocosto', 'delete_centrocosto']
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