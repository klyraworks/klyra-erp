# apps/core/management/commands/reset_database.py
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.apps import apps
import logging


class Command(BaseCommand):
    """
    Elimina todas las tablas de la base de datos EXCEPTO cities_light.

    ADVERTENCIA: Esta operación es IRREVERSIBLE.

    Uso:
        python manage.py reset_database
        python manage.py reset_database --no-confirm
    """

    help = 'Elimina todas las tablas excepto cities_light (IRREVERSIBLE)'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.core')

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Ejecutar sin confirmación (PELIGROSO)'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.ERROR('\n' + '=' * 70))
            self.stdout.write(self.style.ERROR('          ⚠️  RESETEO DE BASE DE DATOS  ⚠️'))
            self.stdout.write(self.style.ERROR('=' * 70))

            # Obtener todas las tablas
            tablas_sistema = self._obtener_tablas_sistema()
            tablas_cities = self._obtener_tablas_cities()
            tablas_a_eliminar = [t for t in tablas_sistema if t not in tablas_cities]

            if not tablas_a_eliminar:
                self.stdout.write(self.style.WARNING('\nNo hay tablas para eliminar.'))
                return

            # Mostrar resumen
            self._mostrar_resumen(tablas_a_eliminar, tablas_cities)

            # Confirmar acción
            if not options['no_confirm'] and not self._confirmar_accion():
                self.stdout.write(self.style.ERROR('\n❌ Operación cancelada por el usuario'))
                return

            # Eliminar tablas
            self._eliminar_tablas(tablas_a_eliminar)

            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('✅ BASE DE DATOS RESETEADA EXITOSAMENTE'))
            self.stdout.write('=' * 70)
            self.stdout.write(f'\n📊 Tablas eliminadas: {len(tablas_a_eliminar)}')
            self.stdout.write(f'📍 Tablas cities_light preservadas: {len(tablas_cities)}')

            self.stdout.write('\n💡 PRÓXIMOS PASOS:')
            self.stdout.write('   1. python manage.py migrate')
            self.stdout.write('   2. python manage.py setup_inicial --skip-cities')
            self.stdout.write('\n' + '=' * 70 + '\n')

            self.logger.info(f"Base de datos reseteada: {len(tablas_a_eliminar)} tablas eliminadas")

        except Exception as e:
            self.logger.error(f"Error en reset_database: {str(e)}", exc_info=True)
            raise CommandError(f'Error al resetear base de datos: {str(e)}')

    def _obtener_tablas_sistema(self):
        """Obtiene todas las tablas del sistema"""
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT tablename
                           FROM pg_tables
                           WHERE schemaname = 'public'
                           ORDER BY tablename
                           """)
            return [row[0] for row in cursor.fetchall()]

    def _obtener_tablas_cities(self):
        """Obtiene las tablas de cities_light que deben preservarse"""
        return [
            'cities_light_country',
            'cities_light_region',
            'cities_light_subregion',
            'cities_light_city',
            'cities_light_alternativename'
        ]

    def _mostrar_resumen(self, tablas_a_eliminar, tablas_cities):
        """Muestra resumen de lo que se va a hacer"""
        self.stdout.write('\n' + self.style.WARNING('📋 RESUMEN DE OPERACIÓN:'))
        self.stdout.write(f'\n🗑️  Tablas a ELIMINAR: {len(tablas_a_eliminar)}')

        # Agrupar por app
        tablas_por_app = {}
        for tabla in tablas_a_eliminar:
            if tabla.startswith('django_'):
                app = 'django'
            elif '_' in tabla:
                app = tabla.split('_')[0]
            else:
                app = 'other'

            if app not in tablas_por_app:
                tablas_por_app[app] = []
            tablas_por_app[app].append(tabla)

        for app, tablas in sorted(tablas_por_app.items()):
            self.stdout.write(f'\n   {app}:')
            for tabla in sorted(tablas)[:5]:  # Mostrar solo primeras 5
                self.stdout.write(f'      • {tabla}')
            if len(tablas) > 5:
                self.stdout.write(f'      ... y {len(tablas) - 5} más')

        self.stdout.write(f'\n\n✅ Tablas a PRESERVAR (cities_light): {len(tablas_cities)}')
        for tabla in tablas_cities:
            self.stdout.write(f'   • {tabla}')

        self.stdout.write('\n' + '=' * 70)

    def _confirmar_accion(self):
        """Solicita confirmación al usuario"""
        self.stdout.write(self.style.ERROR('\n⚠️  ADVERTENCIA CRÍTICA:'))
        self.stdout.write(self.style.ERROR('   Esta operación eliminará TODAS las tablas excepto cities_light'))
        self.stdout.write(self.style.ERROR('   PERDERÁS TODOS LOS DATOS: empresas, usuarios, productos, ventas, etc.'))
        self.stdout.write(self.style.ERROR('   Esta acción es IRREVERSIBLE'))

        self.stdout.write('\n¿Estás COMPLETAMENTE SEGURO de que deseas continuar?')
        respuesta1 = input('Escribe "ELIMINAR TODO" para confirmar: ').strip()

        if respuesta1 != "ELIMINAR TODO":
            return False

        self.stdout.write('\n¿Estás absolutamente seguro? Esta es tu última oportunidad.')
        respuesta2 = input('Escribe "SI" para continuar: ').strip().upper()

        return respuesta2 == "SI"

    def _eliminar_tablas(self, tablas):
        """Elimina las tablas especificadas"""
        self.stdout.write('\n🗑️  Eliminando tablas...\n')

        with connection.cursor() as cursor:
            # Desactivar restricciones de foreign key temporalmente
            cursor.execute('SET session_replication_role = replica;')

            eliminadas = 0
            errores = 0

            for tabla in tablas:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{tabla}" CASCADE')
                    eliminadas += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {tabla}'))
                    self.logger.info(f"Tabla eliminada: {tabla}")
                except Exception as e:
                    errores += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ {tabla}: {str(e)}'))
                    self.logger.error(f"Error al eliminar tabla {tabla}: {str(e)}")

            # Reactivar restricciones
            cursor.execute('SET session_replication_role = DEFAULT;')

            if errores > 0:
                self.stdout.write(self.style.WARNING(f'\n⚠️  {errores} tabla(s) no pudieron eliminarse'))