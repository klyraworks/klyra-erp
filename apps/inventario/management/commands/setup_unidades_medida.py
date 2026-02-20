# apps/inventario/management/commands/setup_unidades_medida.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.inventario.models import UnidadMedida
import logging


class Command(BaseCommand):
    """
    Crea las unidades de medida predeterminadas del sistema.

    Uso:
        python manage.py setup_unidades_medida
        python manage.py setup_unidades_medida --clear
        python manage.py setup_unidades_medida --skip-existing
    """

    help = 'Crea las unidades de medida predeterminadas del sistema'

    UNIDADES_MEDIDA = [
        # UNIDAD
        {'nombre': 'Unidad', 'abreviatura': 'UND', 'tipo': 'unidad'},
        {'nombre': 'Docena', 'abreviatura': 'DOC', 'tipo': 'unidad'},
        {'nombre': 'Ciento', 'abreviatura': 'CTO', 'tipo': 'unidad'},
        {'nombre': 'Millar', 'abreviatura': 'MLL', 'tipo': 'unidad'},
        {'nombre': 'Par', 'abreviatura': 'PAR', 'tipo': 'unidad'},
        {'nombre': 'Caja', 'abreviatura': 'CJA', 'tipo': 'unidad'},
        {'nombre': 'Paquete', 'abreviatura': 'PAQ', 'tipo': 'unidad'},
        {'nombre': 'Set', 'abreviatura': 'SET', 'tipo': 'unidad'},

        # PESO
        {'nombre': 'Kilogramo', 'abreviatura': 'KG', 'tipo': 'peso'},
        {'nombre': 'Gramo', 'abreviatura': 'G', 'tipo': 'peso'},
        {'nombre': 'Miligramo', 'abreviatura': 'MG', 'tipo': 'peso'},
        {'nombre': 'Tonelada', 'abreviatura': 'TON', 'tipo': 'peso'},
        {'nombre': 'Libra', 'abreviatura': 'LB', 'tipo': 'peso'},
        {'nombre': 'Onza', 'abreviatura': 'OZ', 'tipo': 'peso'},
        {'nombre': 'Quintal', 'abreviatura': 'QTL', 'tipo': 'peso'},

        # VOLUMEN
        {'nombre': 'Litro', 'abreviatura': 'L', 'tipo': 'volumen'},
        {'nombre': 'Mililitro', 'abreviatura': 'ML', 'tipo': 'volumen'},
        {'nombre': 'Galón', 'abreviatura': 'GAL', 'tipo': 'volumen'},
        {'nombre': 'Metro cúbico', 'abreviatura': 'M³', 'tipo': 'volumen'},
        {'nombre': 'Centímetro cúbico', 'abreviatura': 'CM³', 'tipo': 'volumen'},
        {'nombre': 'Barril', 'abreviatura': 'BRL', 'tipo': 'volumen'},

        # LONGITUD
        {'nombre': 'Metro', 'abreviatura': 'M', 'tipo': 'longitud'},
        {'nombre': 'Centímetro', 'abreviatura': 'CM', 'tipo': 'longitud'},
        {'nombre': 'Milímetro', 'abreviatura': 'MM', 'tipo': 'longitud'},
        {'nombre': 'Kilómetro', 'abreviatura': 'KM', 'tipo': 'longitud'},
        {'nombre': 'Pulgada', 'abreviatura': 'IN', 'tipo': 'longitud'},
        {'nombre': 'Pie', 'abreviatura': 'FT', 'tipo': 'longitud'},
        {'nombre': 'Yarda', 'abreviatura': 'YD', 'tipo': 'longitud'},

        # ÁREA
        {'nombre': 'Metro cuadrado', 'abreviatura': 'M²', 'tipo': 'area'},
        {'nombre': 'Centímetro cuadrado', 'abreviatura': 'CM²', 'tipo': 'area'},
        {'nombre': 'Hectárea', 'abreviatura': 'HA', 'tipo': 'area'},
        {'nombre': 'Acre', 'abreviatura': 'AC', 'tipo': 'area'},

        # TIEMPO
        {'nombre': 'Hora', 'abreviatura': 'HR', 'tipo': 'tiempo'},
        {'nombre': 'Día', 'abreviatura': 'DÍA', 'tipo': 'tiempo'},
        {'nombre': 'Semana', 'abreviatura': 'SEM', 'tipo': 'tiempo'},
        {'nombre': 'Mes', 'abreviatura': 'MES', 'tipo': 'tiempo'},
        {'nombre': 'Año', 'abreviatura': 'AÑO', 'tipo': 'tiempo'},
    ]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('apps.inventario')

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todas las unidades existentes antes de crear las nuevas'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Omite las unidades que ya existen'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.WARNING('=' * 60))
            self.stdout.write(self.style.WARNING('SETUP DE UNIDADES DE MEDIDA'))
            self.stdout.write(self.style.WARNING('=' * 60))

            clear = options['clear']
            skip_existing = options['skip_existing']

            if clear:
                self._limpiar_unidades_existentes()

            created_count, skipped_count, error_count = self._crear_unidades(skip_existing)

            self._mostrar_resumen(created_count, skipped_count, error_count)

        except Exception as e:
            self.logger.error(f"Error en setup_unidades_medida: {str(e)}", exc_info=True)
            raise CommandError(f'Error al inicializar unidades: {str(e)}')

    def _limpiar_unidades_existentes(self):
        self.stdout.write('Eliminando unidades existentes...')
        count = UnidadMedida.objects.count()
        UnidadMedida.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ {count} unidades eliminadas\n'))
        self.logger.info(f"{count} unidades eliminadas")

    def _crear_unidades(self, skip_existing):
        self.stdout.write('Creando unidades de medida...\n')

        created_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for unidad_data in self.UNIDADES_MEDIDA:
                nombre = unidad_data['nombre']

                try:
                    if UnidadMedida.objects.filter(nombre__iexact=nombre).exists():
                        if skip_existing:
                            self.stdout.write(f'  ⊘ {nombre} (ya existe)')
                            skipped_count += 1
                            continue
                        else:
                            self.stdout.write(self.style.WARNING(f'  ⚠ {nombre} ya existe'))
                            skipped_count += 1
                            continue

                    unidad = UnidadMedida.objects.create(**unidad_data)

                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ {unidad.nombre} ({unidad.abreviatura}) - Código: {unidad.codigo}'
                    ))
                    created_count += 1
                    self.logger.info(f"Unidad creada: {unidad.nombre} | Código: {unidad.codigo}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Error creando {nombre}: {str(e)}'))
                    error_count += 1
                    self.logger.error(f"Error creando {nombre}: {str(e)}")

        return created_count, skipped_count, error_count

    def _mostrar_resumen(self, created_count, skipped_count, error_count):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMEN FINAL'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✓ Unidades creadas: {created_count}'))

        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⊘ Unidades omitidas: {skipped_count}'))

        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errores: {error_count}'))

        total = UnidadMedida.objects.count()
        self.stdout.write(f'\n📊 Total en base de datos: {total}')

        self.stdout.write('\n📋 Unidades por tipo:')
        for tipo_code, tipo_name in UnidadMedida._meta.get_field('tipo').choices:
            count = UnidadMedida.objects.filter(tipo=tipo_code).count()
            if count > 0:
                self.stdout.write(f'  • {tipo_name}: {count} unidades')

        self.stdout.write(self.style.SUCCESS('\n✨ Setup completado exitosamente'))
        self.stdout.write('=' * 60)