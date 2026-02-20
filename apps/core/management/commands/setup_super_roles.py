# apps/core/management/commands/setup_super_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission, User
from django.db import transaction
from apps.seguridad.models import Empleado, Rol
from apps.core.models import Persona, SubRegion, Empresa
from apps.rrhh.models import Departamento
from django.utils import timezone
from decimal import Decimal
import logging


class Command(BaseCommand):
    """
    Configura roles de nivel superior y opcionalmente crea un usuario Gerente General.

    Uso:
        python manage.py setup_super_roles
        python manage.py setup_super_roles --create-admin
        python manage.py setup_super_roles --create-admin --empresa=UUID
    """

    help = 'Configura roles de nivel superior (Gerente General, etc.) y opcionalmente crea un usuario administrador'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Crea un usuario Gerente General con todos los permisos'
        )
        parser.add_argument(
            '--empresa',
            type=str,
            help='UUID de la empresa (opcional, usa la empresa activa si no se especifica)'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('CONFIGURACIÓN DE ROLES SUPERIORES'))
            self.stdout.write(self.style.WARNING('=' * 60))

            with transaction.atomic():
                roles_creados = self._crear_roles_superiores()

            self._mostrar_resumen_roles(roles_creados)

            if options['create_admin']:
                empresa = self._obtener_empresa(options)
                if empresa:
                    self._crear_admin(empresa, roles_creados[0])

        except Exception as e:
            self.logger.error(f"Error en setup_super_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles superiores: {str(e)}')

    def _crear_roles_superiores(self):
        self.stdout.write('\nCreando roles de nivel superior...')

        # Gerente General
        gerente_general, created_gg = Group.objects.get_or_create(name='Gerente General')
        todos_permisos = Permission.objects.all()
        gerente_general.permissions.set(todos_permisos)

        # Director Financiero
        director_financiero, created_df = Group.objects.get_or_create(name='Director Financiero')
        permisos_financiero = Permission.objects.filter(
            content_type__app_label__in=['finanzas', 'ventas', 'compras']
        )
        director_financiero.permissions.set(permisos_financiero)

        # Director de Operaciones
        director_operaciones, created_do = Group.objects.get_or_create(name='Director de Operaciones')
        permisos_operaciones = Permission.objects.filter(
            content_type__app_label__in=['inventario', 'compras', 'rrhh']
        )
        director_operaciones.permissions.set(permisos_operaciones)

        # Administrador del Sistema
        admin_sistema, created_as = Group.objects.get_or_create(name='Administrador del Sistema')
        permisos_sistema = Permission.objects.filter(
            content_type__app_label__in=['auth', 'contenttypes', 'admin', 'sessions', 'core']
        )
        admin_sistema.permissions.set(permisos_sistema)

        roles = [
            {'nombre': 'Gerente General', 'grupo': gerente_general, 'permisos': todos_permisos.count(), 'creado': created_gg},
            {'nombre': 'Director Financiero', 'grupo': director_financiero, 'permisos': permisos_financiero.count(), 'creado': created_df},
            {'nombre': 'Director de Operaciones', 'grupo': director_operaciones, 'permisos': permisos_operaciones.count(), 'creado': created_do},
            {'nombre': 'Administrador del Sistema', 'grupo': admin_sistema, 'permisos': permisos_sistema.count(), 'creado': created_as}
        ]

        for rol in roles:
            estado = '✓ Creado' if rol['creado'] else '⟳ Actualizado'
            self.stdout.write(self.style.SUCCESS(f'{estado}: {rol["nombre"]} ({rol["permisos"]} permisos)'))
            self.logger.info(f"Rol {rol['nombre']}: {rol['permisos']} permisos")

        return roles

    def _obtener_empresa(self, options):
        if options.get('empresa'):
            empresa_id = options['empresa']
            self.stdout.write(f'\nUsando empresa: {empresa_id}')
            try:
                return Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                raise CommandError(f'Empresa con ID {empresa_id} no encontrada')

        empresa = Empresa.objects.filter(is_active=True).first()
        if empresa:
            self.stdout.write(f'\nUsando empresa activa: {empresa.nombre_comercial}')
            return empresa

        raise CommandError('No se encontró empresa activa. Especifica --empresa=UUID')

    def _crear_admin(self, empresa, rol_gerente_general):
        self.stdout.write(f'\n📋 Creando usuario Gerente General...')

        try:
            with transaction.atomic():
                # Asegurar Departamento
                depto_gerencia, _ = Departamento.objects.get_or_create(
                    nombre='Gerencia General',
                    empresa=empresa,
                    defaults={
                        'descripcion': 'Dirección y administración general de la empresa'
                    }
                )

                # Asegurar SubRegión
                direccion_base = SubRegion.objects.first()
                if not direccion_base:
                    raise CommandError('No existen SubRegiones. Ejecuta seeders de geografía primero')

                # Crear Persona
                cedula_admin = f"999999999{empresa.establecimiento[-1]}"
                persona, _ = Persona.objects.get_or_create(
                    cedula=cedula_admin,
                    empresa=empresa,
                    defaults={
                        'nombre1': 'Gerente',
                        'apellido1': 'General',
                        'email': f'admin@{empresa.subdominio}.com',
                        'telefono': '0999999999',
                        'direccion': direccion_base,
                        'fecha_nacimiento': '1980-01-01'
                    }
                )

                # Crear Usuario
                username = f"admin_{empresa.subdominio}"
                password = "admin123"

                usuario, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': persona.email,
                        'is_staff': True,
                        'is_superuser': True
                    }
                )

                if user_created:
                    usuario.set_password(password)
                    usuario.save()

                usuario.groups.add(rol_gerente_general['grupo'])

                # Crear Empleado
                empleado, emp_created = Empleado.objects.get_or_create(
                    usuario=usuario,
                    empresa=empresa,
                    defaults={
                        'persona': persona,
                        'puesto': 'Gerente General',
                        'departamento': depto_gerencia,
                        'fecha_contratacion': timezone.now().date(),
                        'salario': Decimal('5000.00'),
                        'estado': 'activo',
                        'cuenta_activada': True,
                        'fecha_activacion': timezone.now(),
                        'rol': Rol.objects.filter(
                            nombre='Gerente General',
                            empresa=empresa
                        ).first()
                    }
                )

                if empleado.rol:
                    empleado.sincronizar_grupos_django()

                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.SUCCESS('🚀 GERENTE GENERAL CREADO EXITOSAMENTE'))
                self.stdout.write('=' * 60)
                self.stdout.write(f'Empresa: {empresa.nombre_comercial}')
                self.stdout.write(f'Username: {username}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write(f'Email: {persona.email}')
                self.stdout.write(f'Rol: {rol_gerente_general["nombre"]}')
                self.stdout.write(f'Empleado: {empleado.get_full_name()}')
                self.stdout.write('=' * 60)

                self.logger.info(f"Admin creado: {username} | Empresa: {empresa.nombre_comercial}")

        except Exception as e:
            self.logger.error(f"Error al crear admin: {str(e)}", exc_info=True)
            raise CommandError(f'Error al crear usuario administrador: {str(e)}')

    def _mostrar_resumen_roles(self, roles):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE ROLES SUPERIORES'))
        self.stdout.write('=' * 60)

        total_creados = sum(1 for r in roles if r['creado'])
        total_actualizados = len(roles) - total_creados

        self.stdout.write(f'Roles procesados: {len(roles)}')
        self.stdout.write(self.style.SUCCESS(f'  - Creados: {total_creados}'))
        self.stdout.write(f'  - Actualizados: {total_actualizados}')
        self.stdout.write('=' * 60)