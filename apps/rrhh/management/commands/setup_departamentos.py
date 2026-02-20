# apps/rrhh/management/commands/setup_departamentos.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.empresa.models import Empresa
from apps.rrhh.models import Departamento
import logging


class Command(BaseCommand):
    """
    Inicializa departamentos estándar en el sistema.

    Uso:
        python manage.py setup_departamentos
        python manage.py setup_departamentos --empresa=UUID
        python manage.py setup_departamentos --all
    """

    help = 'Inicializa departamentos estándar en el sistema'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.rrhh')

    def add_arguments(self, parser):
        """Define argumentos del comando"""
        parser.add_argument(
            '--empresa',
            type=str,
            help='UUID de la empresa (opcional, usa la empresa por defecto si no se especifica)'
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Crear departamentos en todas las empresas activas'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir departamentos existentes'
        )

    def handle(self, *args, **options):
        """Lógica principal del comando"""
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('INICIALIZANDO DEPARTAMENTOS'))
            self.stdout.write(self.style.WARNING('=' * 60))

            # Determinar empresas objetivo
            empresas = self._obtener_empresas(options)

            if not empresas:
                raise CommandError('No se encontraron empresas para procesar')

            # Procesar cada empresa
            total_creados = 0
            total_existentes = 0

            for empresa in empresas:
                creados, existentes = self._crear_departamentos_empresa(
                    empresa,
                    force=options.get('force', False)
                )
                total_creados += creados
                total_existentes += existentes

            # Resumen final
            self._mostrar_resumen(total_creados, total_existentes, len(empresas))

        except Exception as e:
            self.logger.error(f"Error en setup_departamentos: {str(e)}", exc_info=True)
            raise CommandError(f'Error al inicializar departamentos: {str(e)}')

    def _obtener_empresas(self, options):
        """Obtiene las empresas según las opciones del comando"""
        if options.get('all'):
            self.stdout.write('Procesando todas las empresas activas...')
            return Empresa.objects.filter(is_active=True)

        if options.get('empresa'):
            empresa_id = options['empresa']
            self.stdout.write(f'Procesando empresa: {empresa_id}')
            try:
                return [Empresa.objects.get(id=empresa_id)]
            except Empresa.DoesNotExist:
                raise CommandError(f'Empresa con ID {empresa_id} no encontrada')

        # Usar empresa por defecto (primera activa)
        empresa = Empresa.objects.filter(is_active=True).first()
        if empresa:
            self.stdout.write(f'Usando empresa por defecto: {empresa.nombre}')
            return [empresa]

        return []

    def _crear_departamentos_empresa(self, empresa, force=False):
        """Crea departamentos para una empresa específica"""
        self.stdout.write(f'\n📁 Empresa: {empresa.nombre}')

        departamentos_estandar = [
            'Recursos Humanos',
            'Finanzas',
            'Ventas',
            'Compras',
            'Inventario',
            'Tecnología de la Información',
            'Marketing',
            'Atención al Cliente',
            'Producción',
            'Logística'
        ]

        creados = 0
        existentes = 0

        with transaction.atomic():
            for nombre in departamentos_estandar:
                departamento, created = Departamento.objects.get_or_create(
                    nombre=nombre,
                    empresa=empresa,
                    defaults={
                        'codigo': self._generar_codigo(nombre),
                        'is_active': True
                    }
                )

                if created:
                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Creado: {nombre}')
                    )
                    self.logger.info(f"Departamento creado: {nombre} | Empresa: {empresa.nombre}")
                else:
                    existentes += 1
                    if force:
                        # Actualizar si se usa --force
                        departamento.is_active = True
                        departamento.save()
                        self.stdout.write(
                            self.style.WARNING(f'  ⟳ Actualizado: {nombre}')
                        )
                    else:
                        self.stdout.write(f'  - Ya existe: {nombre}')

        return creados, existentes

    def _generar_codigo(self, nombre):
        """Genera código de departamento a partir del nombre"""
        from unidecode import unidecode
        import re

        nombre_limpio = unidecode(nombre).upper()
        palabras = nombre_limpio.split()

        if len(palabras) > 1:
            # Acrónimo de palabras
            codigo = ''.join([p[0] for p in palabras[:3]])
        else:
            # Primeras 3 letras
            codigo = palabras[0][:3]

        codigo = re.sub(r'[^A-Z0-9]', '', codigo)
        return codigo[:3].ljust(3, 'X')

    def _mostrar_resumen(self, creados, existentes, total_empresas):
        """Muestra resumen de la ejecución"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE EJECUCIÓN'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Empresas procesadas: {total_empresas}')
        self.stdout.write(self.style.SUCCESS(f'Departamentos creados: {creados}'))
        self.stdout.write(f'Departamentos existentes: {existentes}')
        self.stdout.write(self.style.SUCCESS('=' * 60))