# apis/inventario/kitcomponente/kitcomponente_serializer.py
import logging

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apps.inventario.models import (Producto, Marca, UnidadMedida, KitComponente, UnidadConversion, Stock)

# ==================== SERIALIZER KITCOMPONENTE ====================

class KitComponenteSerializer(TenantSerializer):
    componente_nombre = serializers.CharField(source='componente.nombre', read_only=True)
    componente_codigo = serializers.CharField(source='componente.codigo', read_only=True)
    componente_precio = serializers.DecimalField(
        source='componente.precio_venta', max_digits=10, decimal_places=2,
        coerce_to_string=False, read_only=True
    )

    class Meta:
        model  = KitComponente
        fields = [
            'id', 'componente', 'componente_nombre', 'componente_codigo',
            'componente_precio', 'cantidad', 'es_opcional', 'observaciones'
        ]
        read_only_fields = ['id']