# apis/inventario/bodega/bodega_serializer.py
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, F
from cities_light.models import SubRegion

from apps.inventario.models import Bodega, Stock
from apps.seguridad.models import Empleado
from apis.core.SerializerBase import TenantSerializer
from apis.seguridad.empleado.empleado_serializer import EmpleadoListSerializer

import logging
import re
from unidecode import unidecode


class BodegaSerializer(TenantSerializer):
    """
    Serializer completo para Bodega con generación automática de código
    """

    # ==================== CAMPOS DE LECTURA ====================
    responsable_detalle = EmpleadoListSerializer(source='responsable', read_only=True)
    ciudad_detalle = serializers.SerializerMethodField(read_only=True)
    total_productos = serializers.SerializerMethodField(read_only=True)
    valor_total_inventario = serializers.SerializerMethodField(read_only=True)

    # ==================== CAMPOS DE ESCRITURA ====================
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    ciudad = serializers.PrimaryKeyRelatedField(
        queryset=SubRegion.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Bodega
        fields = [
            'id', 'codigo', 'nombre',
            'ciudad', 'ciudad_detalle',
            'direccion', 'telefono', 'capacidad_m3',
            'responsable', 'responsable_detalle',
            'es_principal', 'permite_ventas', 'is_active',
            'total_productos', 'valor_total_inventario',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'codigo', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('apps.inventario')

    # ==================== REPRESENTACIÓN ====================

    def to_representation(self, instance):
        """Personaliza respuesta"""
        representation = super().to_representation(instance)

        if 'responsable_detalle' in representation:
            representation['responsable'] = representation.pop('responsable_detalle')

        if 'ciudad_detalle' in representation:
            representation['ciudad'] = representation.pop('ciudad_detalle')

        return representation

    # ==================== MÉTODOS DE SERIALIZACIÓN ====================

    def get_ciudad_detalle(self, obj):
        """Información de ciudad"""
        if obj.ciudad:
            return {
                'id': obj.ciudad.id,
                'name': obj.ciudad.name,
                'region': obj.ciudad.region.name if obj.ciudad.region else None
            }
        return None

    def get_total_productos(self, obj):
        """Total de productos con stock en bodega"""
        return obj.stocks.filter(cantidad__gt=0).count()

    def get_valor_total_inventario(self, obj):
        """Valor total del inventario en esta bodega"""
        valor = obj.stocks.annotate(
            valor_item=F('cantidad') * F('costo_promedio_bodega')
        ).aggregate(total=Sum('valor_item'))['total']

        return float(valor) if valor else 0.0

    # ==================== VALIDACIONES ====================

    def validate_nombre(self, value):
        """Valida unicidad del nombre"""
        value = value.strip()

        if not value:
            raise ValidationError("El nombre no puede estar vacío")

        queryset = Bodega.objects.filter(
            nombre__iexact=value,
            empresa=self.get_empresa_from_context()
        )
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise ValidationError(f"Ya existe una bodega con el nombre '{value}'")

        return value

    def validate_responsable(self, value):
        """Valida que el responsable esté activo"""
        if value and not value.is_active:
            raise ValidationError("El empleado seleccionado no está activo")
        return value

    def validate_capacidad_m3(self, value):
        """Valida que la capacidad sea positiva"""
        if value is not None and value <= 0:
            raise ValidationError("La capacidad debe ser mayor a cero")
        return value

    def validate_telefono(self, value):
        """Valida formato de teléfono"""
        if value:
            value = value.strip()
            if not re.match(r'^[\d\s\-\+\(\)]{7,20}$', value):
                raise ValidationError("Formato de teléfono no válido")
        return value

    def validate(self, attrs):
        """Validaciones cruzadas"""
        es_principal = attrs.get('es_principal', self.instance.es_principal if self.instance else False)

        # Solo una bodega principal
        if es_principal:
            queryset = Bodega.objects.filter(
                es_principal=True,
                is_active=True,
                empresa=self.get_empresa_from_context()
            )
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise ValidationError({
                    'es_principal': 'Ya existe una bodega principal activa'
                })

        # Auto-asignar responsable si no se especificó
        responsable = attrs.get('responsable', self.instance.responsable if self.instance else None)

        if not responsable:
            request = self.context.get('request')
            if request and hasattr(request, 'empleado'):
                attrs['responsable'] = request.empleado

        # Actualizar variable después de auto-asignación
        responsable = attrs.get('responsable')

        # Bodega con ventas debe tener responsable
        permite_ventas = attrs.get('permite_ventas', self.instance.permite_ventas if self.instance else False)

        if permite_ventas and not responsable:
            raise ValidationError({
                'permite_ventas': 'Una bodega que permite ventas debe tener un responsable asignado'
            })

        return attrs

    # ==================== GENERACIÓN DE CÓDIGO ====================

    def _generar_codigo_bodega(self, nombre, ciudad):
        """
        Genera código único: CIUDAD-NOMBRE-001

        Ejemplos:
        - Quito + Bodega Central → QUI-CENT-001
        - Guayaquil + Almacén Norte → GUA-NORT-001
        """
        # Prefijo ciudad (3 caracteres)
        if ciudad:
            ciudad_nombre = unidecode(ciudad.name).upper()
            prefijo_ciudad = re.sub(r'[^A-Z0-9]', '', ciudad_nombre)[:3]
        else:
            prefijo_ciudad = "GEN"

        prefijo_ciudad = prefijo_ciudad.ljust(3, 'X')

        # Prefijo nombre (4 caracteres)
        nombre_limpio = unidecode(nombre).upper()
        stopwords = ['BODEGA', 'ALMACEN', 'DEPOSITO', 'DE', 'DEL', 'LA', 'EL']
        palabras = [p for p in nombre_limpio.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre_limpio]

        if len(palabras) == 1:
            palabra = palabras[0]
            consonantes = re.sub(r'[AEIOU\s]', '', palabra)
            prefijo_bodega = consonantes[:4] if len(consonantes) >= 4 else palabra[:4]
        else:
            prefijo_bodega = ''.join([p[0] for p in palabras[:4]])

        prefijo_bodega = re.sub(r'[^A-Z0-9]', '', prefijo_bodega)[:4].ljust(4, 'X')

        # Correlativo (3 dígitos)
        patron_base = f"{prefijo_ciudad}-{prefijo_bodega}-"
        ultimo = Bodega.objects.filter(
            codigo__startswith=patron_base
        ).order_by('-codigo').first()

        nuevo_num = 1
        if ultimo:
            try:
                nuevo_num = int(ultimo.codigo.split('-')[-1]) + 1
            except:
                pass

        return f"{patron_base}{nuevo_num:03d}"

    # ==================== CREATE & UPDATE ====================

    def create(self, validated_data):
        """Crea bodega con código auto-generado"""
        responsable = validated_data.pop('responsable', None)
        ciudad = validated_data.pop('ciudad', None)

        codigo = self._generar_codigo_bodega(validated_data['nombre'], ciudad)

        validated_data['codigo'] = codigo
        validated_data['responsable'] = responsable
        validated_data['ciudad'] = ciudad

        bodega = super().create(validated_data)

        self.logger.info(
            f"Bodega creada | ID={bodega.id} | Codigo={bodega.codigo}"
        )

        return bodega

    def update(self, instance, validated_data):
        """Actualiza bodega (código no cambia)"""
        responsable = validated_data.pop('responsable', None)
        ciudad = validated_data.pop('ciudad', None)

        if responsable is not None:
            instance.responsable = responsable

        if ciudad is not None:
            instance.ciudad = ciudad

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        self.logger.info(
            f"Bodega actualizada | ID={instance.id} | Codigo={instance.codigo}"
        )

        return instance


class BodegaListSerializer(TenantSerializer):
    """Serializer simplificado para listados"""
    responsable_nombre = serializers.CharField(
        source='responsable.persona.full_name',
        read_only=True
    )
    ciudad_nombre = serializers.CharField(
        source='ciudad.name',
        read_only=True
    )

    class Meta:
        model = Bodega
        fields = [
            'id', 'codigo', 'nombre', 'ciudad_nombre',
            'responsable_nombre', 'es_principal',
            'permite_ventas', 'is_active'
        ]


class BodegaSimpleSerializer(TenantSerializer):
    """Serializer mínimo para selects"""

    class Meta:
        model = Bodega
        fields = ['id', 'codigo', 'nombre', 'es_principal']