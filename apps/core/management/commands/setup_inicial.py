# apps/core/management/commands/setup_inicial.py
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from apps.core.models import Empresa
import logging
import time


class Command(BaseCommand):
    """
    Ejecuta la configuración inicial completa del sistema ERP.

    Pasos que ejecuta:
    1. Migraciones de base de datos
    2. Carga de ciudades (cities_light)
    3. Creación de empresa
    4. Configuración de roles
    5. Creación de usuario administrador
    6. Unidades de medida
    7. Departamentos iniciales

    Uso:
        python manage.py setup_inicial
        python manage.py setup_inicial --skip-migrations
        python manage.py setup_inicial --skip-cities
        python manage.py setup_inicial --empresa-template=klyra
    """

    help = 'Ejecuta la configuración inicial completa del sistema ERP'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Omitir makemigrations y migrate'
        )
        parser.add_argument(
            '--skip-cities',
            action='store_true',
            help='Omitir carga de ciudades (cities_light)'
        )
        parser.add_argument(
            '--empresa-template',
            type=str,
            choices=['klyra', 'demo'],
            default='klyra',
            help='Template de empresa a crear (default: klyra)'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            help='Username para el administrador (default: admin_[subdominio])'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='Password para el administrador (default: admin123)'
        )

    def handle(self, *args, **options):
        inicio = time.time()

        try:
            self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 70))
            self.stdout.write(self.style.HTTP_INFO('          CONFIGURACIÓN INICIAL DEL SISTEMA ERP'))
            self.stdout.write(self.style.HTTP_INFO('=' * 70 + '\n'))

            pasos_completados = []
            pasos_omitidos = []
            errores = []

            # PASO 1: Migraciones
            if not options['skip_migrations']:
                if self._ejecutar_migraciones():
                    pasos_completados.append('Migraciones de base de datos')
                else:
                    errores.append('Migraciones de base de datos')
            else:
                pasos_omitidos.append('Migraciones de base de datos')

            # PASO 2: Cities Light
            if not options['skip_cities']:
                if self._cargar_ciudades():
                    pasos_completados.append('Carga de ciudades')
                else:
                    errores.append('Carga de ciudades')
            else:
                pasos_omitidos.append('Carga de ciudades')

            # PASO 3: Crear empresa
            empresa = self._crear_empresa(options['empresa_template'])
            if empresa:
                pasos_completados.append(f'Creación de empresa ({empresa.nombre_comercial})')
            else:
                errores.append('Creación de empresa')
                raise CommandError('No se pudo crear la empresa. Abortando configuración.')

            # PASO 4: Configurar roles y crear admin
            if self._configurar_roles_y_admin(empresa):
                pasos_completados.append('Configuración de roles y usuario administrador')
            else:
                errores.append('Configuración de roles')

            # PASO 5: Unidades de medida
            if self._configurar_unidades_medida():
                pasos_completados.append('Configuración de unidades de medida')
            else:
                errores.append('Unidades de medida')

            # PASO 6: Departamentos
            if self._configurar_departamentos(empresa):
                pasos_completados.append('Configuración de departamentos')
            else:
                errores.append('Departamentos')

            # Resumen final
            self._mostrar_resumen_final(
                pasos_completados,
                pasos_omitidos,
                errores,
                time.time() - inicio,
                empresa
            )

            if errores:
                raise CommandError('La configuración se completó con errores')

        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\n\n⚠ Configuración interrumpida por el usuario'))
            raise CommandError('Configuración cancelada')
        except Exception as e:
            self.logger.error(f"Error en setup_inicial: {str(e)}", exc_info=True)
            raise CommandError(f'Error en configuración inicial: {str(e)}')

    def _ejecutar_migraciones(self):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 1: MIGRACIONES DE BASE DE DATOS')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write('\n📦 Ejecutando makemigrations...')
            call_command('makemigrations')

            self.stdout.write('\n📦 Ejecutando migrate...')
            call_command('migrate')

            self.stdout.write(self.style.SUCCESS('\n✓ Migraciones completadas exitosamente'))
            self.logger.info("Migraciones ejecutadas exitosamente")
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error en migraciones: {str(e)}'))
            self.logger.error(f"Error en migraciones: {str(e)}", exc_info=True)
            return False

    def _cargar_ciudades(self):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 2: CARGA DE CIUDADES')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write('\n📍 Cargando ciudades con cities_light...')
            self.stdout.write(self.style.WARNING('   (Esto puede tomar varios minutos)'))

            call_command('cities_light')

            self.stdout.write(self.style.SUCCESS('\n✓ Ciudades cargadas exitosamente'))
            self.logger.info("Ciudades cargadas exitosamente")
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al cargar ciudades: {str(e)}'))
            self.logger.error(f"Error al cargar ciudades: {str(e)}", exc_info=True)
            return False

    def _crear_empresa(self, template):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 3: CREACIÓN DE EMPRESA')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write(f'\n🏢 Creando empresa con template: {template}')

            call_command('setup_crear_empresa', template=template, set_active=True, force=True)

            empresa = Empresa.objects.filter(is_active=True).first()
            if not empresa:
                raise Exception('No se encontró la empresa creada')

            self.stdout.write(self.style.SUCCESS(f'\n✓ Empresa creada: {empresa.nombre_comercial}'))
            self.logger.info(f"Empresa creada: {empresa.nombre_comercial}")
            return empresa
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al crear empresa: {str(e)}'))
            self.logger.error(f"Error al crear empresa: {str(e)}", exc_info=True)
            return None

    def _configurar_roles_y_admin(self, empresa):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 4: CONFIGURACIÓN DE ROLES Y ADMINISTRADOR')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write('\n👥 Configurando todos los roles...')

            call_command(
                'setup_all_roles',
                with_super_roles=True,
                create_admin=True
            )

            self.stdout.write(f'\n📋 Creando roles de negocio por empresa...')
            call_command(
                'setup_roles_empresa',
                empresa=str(empresa.id)
            )

            # Crear admin específico para la empresa
            self.stdout.write(f'\n👤 Creando administrador para empresa {empresa.nombre_comercial}...')
            call_command(
                'setup_super_roles',
                create_admin=True,
                empresa=str(empresa.id)
            )

            self.stdout.write(self.style.SUCCESS('\n✓ Roles y administrador configurados exitosamente'))
            self.logger.info("Roles y administrador configurados")
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al configurar roles: {str(e)}'))
            self.logger.error(f"Error al configurar roles: {str(e)}", exc_info=True)
            return False

    def _configurar_unidades_medida(self):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 5: CONFIGURACIÓN DE UNIDADES DE MEDIDA')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write('\n📏 Creando unidades de medida...')

            call_command('setup_unidades_medida', skip_existing=True)

            self.stdout.write(self.style.SUCCESS('\n✓ Unidades de medida configuradas'))
            self.logger.info("Unidades de medida configuradas")
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al configurar unidades: {str(e)}'))
            self.logger.error(f"Error al configurar unidades: {str(e)}", exc_info=True)
            return False

    def _configurar_departamentos(self, empresa):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('PASO 6: CONFIGURACIÓN DE DEPARTAMENTOS')
        self.stdout.write('=' * 70)

        try:
            self.stdout.write('\n🏛️ Creando departamentos iniciales...')

            call_command('setup_departamentos', empresa=str(empresa.id))

            self.stdout.write(self.style.SUCCESS('\n✓ Departamentos configurados'))
            self.logger.info("Departamentos configurados")
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error al configurar departamentos: {str(e)}'))
            self.logger.error(f"Error al configurar departamentos: {str(e)}", exc_info=True)
            return False

    def _mostrar_resumen_final(self, completados, omitidos, errores, tiempo_total, empresa):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.HTTP_INFO('                    RESUMEN DE CONFIGURACIÓN'))
        self.stdout.write('=' * 70)

        self.stdout.write(f'\n⏱️  Tiempo total: {tiempo_total:.2f} segundos')

        if completados:
            self.stdout.write(f'\n✓ Pasos completados ({len(completados)}):')
            for paso in completados:
                self.stdout.write(self.style.SUCCESS(f'  • {paso}'))

        if omitidos:
            self.stdout.write(f'\n⊘ Pasos omitidos ({len(omitidos)}):')
            for paso in omitidos:
                self.stdout.write(self.style.WARNING(f'  • {paso}'))

        if errores:
            self.stdout.write(f'\n✗ Pasos con errores ({len(errores)}):')
            for paso in errores:
                self.stdout.write(self.style.ERROR(f'  • {paso}'))

        if not errores:
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('🎉 ¡CONFIGURACIÓN INICIAL COMPLETADA EXITOSAMENTE!'))
            self.stdout.write('=' * 70)

            self.stdout.write(f'\n📋 CREDENCIALES DE ACCESO:')
            self.stdout.write(f'   • Empresa: {empresa.nombre_comercial}')
            self.stdout.write(f'   • Username: admin_{empresa.subdominio}')
            self.stdout.write(f'   • Password: admin123')
            self.stdout.write(f'   • Email: admin@{empresa.subdominio}.com')

            self.stdout.write(f'\n💡 PRÓXIMOS PASOS:')
            self.stdout.write(f'   1. Acceder al sistema con las credenciales proporcionadas')
            self.stdout.write(f'   2. Cambiar la contraseña del administrador')
            self.stdout.write(f'   3. Configurar el certificado digital para facturación (si es producción)')
            self.stdout.write(f'   4. Crear usuarios adicionales según sea necesario')
            self.stdout.write(f'   5. Configurar bodegas, categorías y productos')

        self.stdout.write('\n' + '=' * 70 + '\n')