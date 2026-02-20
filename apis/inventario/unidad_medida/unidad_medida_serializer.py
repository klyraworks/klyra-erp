# apis/inventario/unidad_medida/unidad_medida_serializer.py
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.inventario.models import UnidadMedida
from utils.validators import TextNormalizers
from apis.core.SerializerBase import TenantSerializer

import logging


class UnidadMedidaSerializer(serializers.ModelSerializer):
    """Serializer completo para unidades de medida"""

    # READ-ONLY
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    productos_count = serializers.SerializerMethodField()

    class Meta:
        model = UnidadMedida
        fields = [
            'id', 'codigo', 'nombre', 'abreviatura', 'tipo', 'tipo_display',
            'productos_count'
        ]
        read_only_fields = ['id', 'codigo']  # ← codigo read-only

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('unidad_medida_serializer')

    # ==================== SERIALIZATION ====================

    def get_productos_count(self, obj):
        """Cantidad de productos usando esta unidad"""
        return obj.productos.filter(is_active=True).count()

    def to_representation(self, instance):
        """Enriquece la respuesta"""
        data = super().to_representation(instance)
        return data

    # ==================== VALIDATIONS ====================

    # NOTA: validate_codigo eliminado porque el código se genera automáticamente

    def validate_nombre(self, value):
        """Valida unicidad del nombre"""
        value = TextNormalizers.normalize_text(value)

        if self.instance and self.instance.nombre == value:
            return value

        if UnidadMedida.objects.filter(nombre__iexact=value).exists():
            raise ValidationError(f"La unidad {value} ya existe")

        return value

    def validate_abreviatura(self, value):
        """Valida abreviatura"""
        value = TextNormalizers.normalize_text(value).upper()

        if len(value) > 10:
            raise ValidationError("La abreviatura no puede tener más de 10 caracteres")

        return value

    # ==================== CREATE ====================

    def create(self, validated_data):
        """Crea unidad de medida"""
        try:
            with transaction.atomic():
                unidad = super().create(**validated_data)

                self.logger.info(
                    f"Unidad de medida creada: {unidad.id} - {unidad.codigo}",
                    extra={
                        'unidad_id': unidad.id,
                        'codigo': unidad.codigo,
                        'nombre': unidad.nombre
                    }
                )

                return unidad

        except Exception as e:
            self.logger.exception(f"Error creando unidad: {str(e)}")
            raise ValidationError(f"Error al crear unidad de medida: {str(e)}")

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        """Actualiza unidad de medida"""
        try:
            with transaction.atomic():
                for field, value in validated_data.items():
                    setattr(instance, field, value)

                instance.save()

                self.logger.info(
                    f"Unidad actualizada: {instance.id}",
                    extra={'unidad_id': instance.id}
                )

                return instance

        except Exception as e:
            self.logger.exception(f"Error actualizando unidad: {str(e)}")
            raise ValidationError(f"Error al actualizar unidad: {str(e)}")


class UnidadMedidaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado"""

    class Meta:
        model = UnidadMedida
        fields = ['id', 'codigo', 'nombre', 'abreviatura', 'tipo']

"""
Ejemplo de JSON para Unidad de Medida simple:
{
    'nombre': 'Hora',
    'abreviatura': 'HR',
    'tipo': 'tiempo'
}
"""