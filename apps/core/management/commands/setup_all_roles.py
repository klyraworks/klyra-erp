# apps/core/management/commands/setup_all_roles.py
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import logging
import time


class Command(BaseCommand):
    """
    Ejecuta todos los comandos de configuración de roles del ERP.

    Uso:
        python manage.py setup_all_roles
        python manage.py setup_all_roles --with-super-roles
        python manage.py setup_all_roles --with-super-roles --create-admin
    """

    help = 'Ejecuta todos los comandos de configuración de roles del ERP'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-super-roles',
            action='store_true',
            help='Incluye la configuración de roles superiores (Gerente General, etc.)'
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Crea un usuario Gerente General (solo con --with-super-roles)'
        )

    def handle(self, *args, **options):
        inicio = time.time()

        try:
            self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 70))
            self.stdout.write(self.style.HTTP_INFO('     CONFIGURACIÓN COMPLETA DE ROLES - SISTEMA ERP'))
            self.stdout.write(self.style.HTTP_INFO('=' * 70 + '\n'))

            comandos = [
                ('setup_rrhh_roles', 'RECURSOS HUMANOS'),
                ('setup_ventas_roles', 'VENTAS'),
                ('setup_compras_roles', 'COMPRAS'),
                ('setup_inventario_roles', 'INVENTARIO'),
                ('setup_finanzas_roles', 'FINANZAS'),
            ]

            errores = []
            exitosos = 0

            for comando, modulo in comandos:
                self.stdout.write(f'\n📦 Configurando módulo: {modulo}')
                self.stdout.write('-' * 70)

                try:
                    call_command(comando)
                    exitosos += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ {modulo} configurado correctamente\n'))
                    self.logger.info(f"Módulo {modulo} configurado exitosamente")
                except Exception as e:
                    errores.append((modulo, str(e)))
                    self.stdout.write(self.style.ERROR(f'✗ Error en {modulo}: {str(e)}\n'))
                    self.logger.error(f"Error en módulo {modulo}: {str(e)}", exc_info=True)

            if options['with_super_roles']:
                self.stdout.write(f'\n📦 Configurando roles de nivel superior')
                self.stdout.write('-' * 70)

                try:
                    if options['create_admin']:
                        call_command('setup_super_roles', create_admin=True)
                    else:
                        call_command('setup_super_roles')
                    exitosos += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Roles superiores configurados correctamente\n'))
                    self.logger.info("Roles superiores configurados exitosamente")
                except Exception as e:
                    errores.append(('Roles Superiores', str(e)))
                    self.stdout.write(self.style.ERROR(f'✗ Error en roles superiores: {str(e)}\n'))
                    self.logger.error(f"Error en roles superiores: {str(e)}", exc_info=True)

            self._mostrar_resumen(exitosos, errores, time.time() - inicio, options['with_super_roles'])

            if errores:
                raise CommandError('Algunos módulos presentaron errores')

        except Exception as e:
            self.logger.error(f"Error en setup_all_roles: {str(e)}", exc_info=True)
            raise CommandError(f'Error al configurar roles: {str(e)}')

    def _mostrar_resumen(self, exitosos, errores, tiempo_total, incluye_super_roles):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.HTTP_INFO('                    RESUMEN DE CONFIGURACIÓN'))
        self.stdout.write('=' * 70)

        self.stdout.write(f'\n📊 Estadísticas:')
        self.stdout.write(f'   • Módulos configurados exitosamente: {exitosos}')
        self.stdout.write(f'   • Módulos con errores: {len(errores)}')
        self.stdout.write(f'   • Tiempo total: {tiempo_total:.2f} segundos')

        if errores:
            self.stdout.write(f'\n⚠ Errores encontrados:')
            for modulo, error in errores:
                self.stdout.write(self.style.ERROR(f'   ✗ {modulo}: {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n¡Todos los roles se configuraron correctamente!'))

        self.stdout.write(f'\n💡 Próximos pasos:')
        self.stdout.write(f'   1. Crear empleados: python manage.py crear_empleado')
        self.stdout.write(f'   2. Asignar roles desde el admin de Django')
        if not incluye_super_roles:
            self.stdout.write(f'   3. O ejecutar: python manage.py setup_all_roles --with-super-roles --create-admin')

        self.stdout.write('\n' + '=' * 70 + '\n')

        self.stdout.write(self.style.WARNING(
            '\n💡 Ejecuta setup_roles_empresa para crear los Roles de negocio por empresa'
        ))