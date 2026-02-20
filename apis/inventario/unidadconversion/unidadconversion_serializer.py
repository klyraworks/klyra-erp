# apis/inventario/unidadconversion/unidadconversion_serializer.py
from rest_framework import serializers

from apps.inventario.models import UnidadConversion
from apis.core.SerializerBase import TenantSerializer


class UnidadConversionSerializer(TenantSerializer):
    unidad_origen_nombre  = serializers.CharField(source='unidad_origen.nombre', read_only=True)
    unidad_destino_nombre = serializers.CharField(source='unidad_destino.nombre', read_only=True)

    class Meta:
        model  = UnidadConversion
        fields = [
            'id', 'unidad_origen', 'unidad_origen_nombre',
            'unidad_destino', 'unidad_destino_nombre', 'factor_conversion'
        ]
        read_only_fields = ['id']