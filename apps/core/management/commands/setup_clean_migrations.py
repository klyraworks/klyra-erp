# apps/core/management/commands/setup_clean_migrations.py
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import os


class Command(BaseCommand):
    """
    Elimina archivos de migración de apps Django específicas (solo apps del proyecto).

    Uso:
        python manage.py clean_migrations app1 app2
        python manage.py clean_migrations --all
        python manage.py clean_migrations usuarios productos --no-confirm
    """

    help = 'Elimina archivos de migración de apps Django específicas (solo apps del proyecto)'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            'apps',
            nargs='*',
            type=str,
            help='Nombres de las apps a limpiar'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpiar todas las apps del proyecto (excluye paquetes instalados)'
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Ejecutar sin confirmación'
        )
        parser.add_argument(
            '--delete-init',
            action='store_true',
            help='También eliminar archivos __init__.py (no recomendado)'
        )

    def handle(self, *args, **options):
        try:
            apps_seleccionadas = options['apps']
            limpiar_todas = options['all']
            sin_confirmacion = options['no_confirm']
            eliminar_init = options['delete_init']

            directorio_base = settings.BASE_DIR

            if self._esta_en_site_packages(directorio_base):
                raise CommandError('El directorio base parece estar en site-packages')

            if not apps_seleccionadas and not limpiar_todas:
                self._mostrar_apps_disponibles(directorio_base)
                return

            if limpiar_todas:
                apps_seleccionadas = self._obtener_apps_proyecto(directorio_base)
                if not apps_seleccionadas:
                    self.stdout.write(self.style.WARNING('No se encontraron apps del proyecto con carpetas migrations'))
                    return

            apps_validas = self._validar_apps(directorio_base, apps_seleccionadas)
            if not apps_validas:
                raise CommandError('No se encontraron apps válidas para procesar')

            self._mostrar_resumen_apps(apps_validas, eliminar_init)

            if not sin_confirmacion and not self._confirmar_accion():
                self.stdout.write(self.style.ERROR('Operación cancelada'))
                return

            self._limpiar_migrations(apps_validas, eliminar_init)

        except Exception as e:
            self.logger.error(f"Error en clean_migrations: {str(e)}", exc_info=True)
            raise CommandError(f'Error al limpiar migraciones: {str(e)}')

    def _esta_en_site_packages(self, directorio):
        return 'site-packages' in str(directorio) or '.venv' in str(directorio)

    def _obtener_apps_proyecto(self, directorio_base):
        apps = []
        directorios_busqueda = [directorio_base]

        carpeta_apps = os.path.join(directorio_base, 'apps')
        if os.path.exists(carpeta_apps):
            directorios_busqueda.append(carpeta_apps)

        for dir_busqueda in directorios_busqueda:
            if not os.path.exists(dir_busqueda):
                continue

            for item in os.listdir(dir_busqueda):
                ruta_completa = os.path.join(dir_busqueda, item)

                if not os.path.isdir(ruta_completa):
                    continue
                if item.startswith('.') or item == '__pycache__':
                    continue
                if 'site-packages' in str(ruta_completa) or '.venv' in str(ruta_completa):
                    continue

                ruta_migrations = os.path.join(ruta_completa, 'migrations')
                if os.path.exists(ruta_migrations):
                    apps.append(item)

        return apps

    def _validar_apps(self, directorio_base, apps):
        apps_validas = []

        for app in apps:
            ubicaciones_posibles = [
                os.path.join(directorio_base, app),
                os.path.join(directorio_base, 'apps', app),
            ]

            for ubicacion in ubicaciones_posibles:
                if os.path.exists(ubicacion):
                    if 'site-packages' not in str(ubicacion) and '.venv' not in str(ubicacion):
                        ruta_migrations = os.path.join(ubicacion, 'migrations')
                        if os.path.exists(ruta_migrations):
                            apps_validas.append({
                                'nombre': app,
                                'ruta': ubicacion,
                                'ruta_migrations': ruta_migrations
                            })
                            break

        return apps_validas

    def _mostrar_apps_disponibles(self, directorio_base):
        self.stdout.write(self.style.WARNING('\n⚠ No se especificaron apps para limpiar.\n'))
        self.stdout.write('Apps del proyecto con carpetas migrations:\n')

        apps_encontradas = self._obtener_apps_proyecto(directorio_base)

        if apps_encontradas:
            for app in apps_encontradas:
                ubicaciones = [
                    os.path.join(directorio_base, app),
                    os.path.join(directorio_base, 'apps', app),
                ]

                for ubicacion in ubicaciones:
                    if os.path.exists(ubicacion):
                        ruta_migrations = os.path.join(ubicacion, 'migrations')
                        if os.path.exists(ruta_migrations):
                            archivos = [f for f in os.listdir(ruta_migrations)
                                       if f.endswith('.py') and f != '__init__.py']
                            self.stdout.write(f'  • {app} ({len(archivos)} archivo(s) de migración)')
                            break
        else:
            self.stdout.write(self.style.WARNING('  No se encontraron apps del proyecto con migrations'))

        self.stdout.write('\n' + self.style.SUCCESS('Uso:'))
        self.stdout.write('  python manage.py clean_migrations app1 app2 app3')
        self.stdout.write('  python manage.py clean_migrations --all')
        self.stdout.write('  python manage.py clean_migrations usuarios productos --no-confirm\n')

    def _mostrar_resumen_apps(self, apps_validas, eliminar_init):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.WARNING('RESUMEN DE OPERACIÓN'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Apps a limpiar: {", ".join([a["nombre"] for a in apps_validas])}')
        self.stdout.write(f'Conservar __init__.py: {"NO" if eliminar_init else "SÍ"}')
        self.stdout.write('\nUbicaciones:')
        for app in apps_validas:
            self.stdout.write(f'  • {app["nombre"]}: {app["ruta_migrations"]}')
        self.stdout.write('=' * 60 + '\n')

    def _confirmar_accion(self):
        self.stdout.write(self.style.ERROR('⚠ ADVERTENCIA: Esta acción eliminará archivos de migración.'))
        self.stdout.write('   Asegúrate de tener un respaldo si es necesario.\n')

        respuesta = input('¿Deseas continuar? (si/no): ').lower().strip()
        return respuesta in ['si', 's', 'yes', 'y']

    def _limpiar_migrations(self, apps_validas, eliminar_init):
        archivos_eliminados = []
        errores = []

        for app_info in apps_validas:
            app_nombre = app_info['nombre']
            ruta_migrations = app_info['ruta_migrations']

            self.stdout.write(f'\n📁 Procesando: {app_nombre}/migrations')
            self.stdout.write(f'   Ubicación: {ruta_migrations}')

            archivos = os.listdir(ruta_migrations)

            for archivo in archivos:
                if not eliminar_init and archivo == '__init__.py':
                    self.stdout.write(f'  ⏭️  Conservando: {archivo}')
                    continue

                if archivo == '__pycache__':
                    continue

                ruta_archivo = os.path.join(ruta_migrations, archivo)

                if os.path.isfile(ruta_archivo) and archivo.endswith('.py'):
                    try:
                        os.remove(ruta_archivo)
                        archivos_eliminados.append(f'{app_nombre}/{archivo}')
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Eliminado: {archivo}'))
                        self.logger.info(f"Archivo eliminado: {app_nombre}/{archivo}")
                    except Exception as e:
                        errores.append((f'{app_nombre}/{archivo}', str(e)))
                        self.stdout.write(self.style.ERROR(f'  ✗ Error al eliminar {archivo}: {e}'))
                        self.logger.error(f"Error al eliminar {app_nombre}/{archivo}: {str(e)}")

        self._mostrar_resumen_final(archivos_eliminados, errores)

    def _mostrar_resumen_final(self, archivos_eliminados, errores):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN FINAL'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Archivos eliminados: {len(archivos_eliminados)}')

        if errores:
            self.stdout.write(self.style.ERROR(f'Errores: {len(errores)}'))
            self.stdout.write('\n⚠ Archivos con errores:')
            for archivo, error in errores:
                self.stdout.write(f'  - {archivo}: {error}')

        self.stdout.write('\n' + self.style.SUCCESS('✨ Proceso completado.'))

        if archivos_eliminados:
            self.stdout.write(self.style.WARNING('\n💡 Recuerda ejecutar: python manage.py makemigrations'))