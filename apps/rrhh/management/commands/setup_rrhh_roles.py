# apps/rrhh/management/commands/setup_roles_rrhh.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.rrhh.models import Nomina, Asistencia, Ausencia, Evaluacion, Departamento
from apps.seguridad.models import Empleado
import logging


class Command(BaseCommand):
    """
    Configura roles y permisos estándar del módulo RRHH.

    Uso:
        python manage.py setup_roles_rrhh
        python manage.py setup_roles_rrhh --force
    """

    help = 'Configura roles y permisos del módulo RRHH'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.rrhh')

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir roles existentes'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES RRHH'))
            self.stdout.write(self.style.WARNING('=' * 60))

            # Obtener content types
            content_types = self._obtener_content_types()

            # Crear roles
            with transaction.atomic():
                roles_creados = []

                roles_creados.append(
                    self._crear_rol_supervisor(content_types, options['force'])
                )
                roles_creados.append(
                    self._crear_rol_gerente_rrhh(content_types, options['force'])
                )
                roles_creados.append(
                    self._crear_rol_asistente_rrhh(content_types, options['force'])
                )

            # Resumen
            self._mostrar_resumen(roles_creados)

        except Exception as e:
            self.logger.error(f"Error en setup_roles_rrhh: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _obtener_content_types(self):
        """Obtiene content types necesarios"""
        self.stdout.write('Obteniendo content types...')

        return {
            'empleado': ContentType.objects.get_for_model(Empleado),
            'nomina': ContentType.objects.get_for_model(Nomina),
            'asistencia': ContentType.objects.get_for_model(Asistencia),
            'ausencia': ContentType.objects.get_for_model(Ausencia),
            'evaluacion': ContentType.objects.get_for_model(Evaluacion),
            'departamento': ContentType.objects.get_for_model(Departamento),
        }

    def _crear_rol_supervisor(self, content_types, force):
        """Crea rol de Supervisor"""
        nombre_rol = 'RRHH | Supervisor'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['empleado'],
            codename__in=['view_empleado']
        ) | Permission.objects.filter(
            content_type=content_types['asistencia'],
            codename__in=['view_asistencia', 'ver_todas_asistencias']
        ) | Permission.objects.filter(
            content_type=content_types['ausencia'],
            codename__in=['view_ausencia', 'change_ausencia', 'aprobar_ausencias']
        ) | Permission.objects.filter(
            content_type=content_types['evaluacion'],
            codename__in=['add_evaluacion', 'change_evaluacion', 'view_evaluacion', 'realizar_evaluaciones']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_gerente_rrhh(self, content_types, force):
        """Crea rol de Gerente RRHH"""
        nombre_rol = 'RRHH | Gerente RRHH'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['empleado'],
            codename__in=['add_empleado', 'change_empleado', 'view_empleado', 'delete_empleado',
                         'ver_salarios', 'ver_reportes_rrhh']
        ) | Permission.objects.filter(
            content_type=content_types['nomina'],
            codename__in=['add_nomina', 'change_nomina', 'view_nomina', 'delete_nomina',
                         'aprobar_nomina', 'ver_todas_nominas']
        ) | Permission.objects.filter(
            content_type=content_types['asistencia'],
            codename__in=['add_asistencia', 'change_asistencia', 'view_asistencia',
                         'delete_asistencia', 'ver_todas_asistencias', 'marcar_asistencia_otros']
        ) | Permission.objects.filter(
            content_type=content_types['ausencia'],
            codename__in=['add_ausencia', 'change_ausencia', 'view_ausencia',
                         'delete_ausencia', 'aprobar_ausencias']
        ) | Permission.objects.filter(
            content_type=content_types['evaluacion'],
            codename__in=['add_evaluacion', 'change_evaluacion', 'view_evaluacion',
                         'delete_evaluacion', 'realizar_evaluaciones', 'ver_todas_evaluaciones']
        ) | Permission.objects.filter(
            content_type=content_types['departamento'],
            codename__in=['add_departamento', 'change_departamento', 'view_departamento',
                         'delete_departamento', 'ver_organigrama', 'gestionar_departamentos']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _crear_rol_asistente_rrhh(self, content_types, force):
        """Crea rol de Asistente RRHH"""
        nombre_rol = 'RRHH | Asistente RRHH'
        self.stdout.write(f'\n📋 Configurando: {nombre_rol}')

        grupo, created = Group.objects.get_or_create(name=nombre_rol)

        if not created and not force:
            self.stdout.write(f'  - Rol ya existe (use --force para sobrescribir)')
            return {'nombre': nombre_rol, 'permisos': grupo.permissions.count(), 'creado': False}

        permisos = Permission.objects.filter(
            content_type=content_types['empleado'],
            codename__in=['add_empleado', 'view_empleado', 'change_empleado']
        ) | Permission.objects.filter(
            content_type=content_types['nomina'],
            codename__in=['add_nomina', 'view_nomina']
        ) | Permission.objects.filter(
            content_type=content_types['asistencia'],
            codename__in=['view_asistencia', 'ver_todas_asistencias']
        ) | Permission.objects.filter(
            content_type=content_types['ausencia'],
            codename__in=['view_ausencia', 'change_ausencia']
        ) | Permission.objects.filter(
            content_type=content_types['departamento'],
            codename__in=['view_departamento']
        )

        grupo.permissions.set(permisos)
        total_permisos = permisos.count()

        self.stdout.write(self.style.SUCCESS(f'  ✓ {total_permisos} permisos asignados'))
        self.logger.info(f"Rol creado: {nombre_rol} | Permisos: {total_permisos}")

        return {'nombre': nombre_rol, 'permisos': total_permisos, 'creado': created}

    def _mostrar_resumen(self, roles):
        """Muestra resumen de roles creados"""
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