# apis/inventario/stock/inventario_bodega_serializer.py
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from django.utils import timezone
import pytz
from apis.core.SerializerBase import TenantSerializer

from apps.inventario.models import (
    MovimientoInventario,
    DetalleMovimiento,
    Stock,
    Producto,
    Bodega
)

from apis.inventario.producto.producto_serializer import ProductoSerializer, ProductoSimpleSerializer
from apis.inventario.bodega.bodega_serializer import BodegaSimpleSerializer
from django.contrib.auth.models import User

from utils.validators import BusinessValidators
import logging


class InventarioBodegaListSerializer(TenantSerializer):
    """
    Serializer simplificado para listados de inventario.
    Optimizado para consultas masivas sin datos anidados pesados.
    """

    # Información del producto
    producto_id = serializers.UUIDField(source='producto.id', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    unidad_medida = serializers.CharField(source='producto.unidad_medida.abreviatura', read_only=True)

    # Información de la bodega
    bodega_id = serializers.UUIDField(source='bodega.id', read_only=True)
    bodega_codigo = serializers.CharField(source='bodega.codigo', read_only=True)
    bodega_nombre = serializers.CharField(source='bodega.nombre', read_only=True)

    # Stock calculado
    stock_disponible = serializers.SerializerMethodField()

    # Estado del stock
    estado_stock = serializers.SerializerMethodField()
    necesita_reposicion = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = [
            'id',
            'producto_id', 'producto_codigo', 'producto_nombre',
            'categoria_nombre', 'unidad_medida',
            'bodega_id', 'bodega_codigo', 'bodega_nombre',
            'cantidad', 'stock_reservado', 'stock_disponible',
            'estado_stock', 'necesita_reposicion'
        ]

    def get_stock_disponible(self, obj):
        """Calcula stock disponible (cantidad - reservado)"""
        return obj.cantidad - obj.stock_reservado

    def get_estado_stock(self, obj):
        """Determina el estado del stock (crítico, bajo, normal)"""
        stock_minimo = getattr(obj.producto, 'stock_minimo', 0)

        if obj.cantidad == 0:
            return 'sin_stock'
        elif obj.cantidad <= stock_minimo / 2:
            return 'critico'
        elif obj.cantidad <= stock_minimo:
            return 'bajo'
        else:
            return 'normal'

    def get_necesita_reposicion(self, obj):
        """Indica si necesita reposición"""
        stock_minimo = getattr(obj.producto, 'stock_minimo', 0)
        return obj.cantidad <= stock_minimo


class StockSerializer(TenantSerializer):
    """
    Serializer completo para Stock.
    Incluye información detallada del producto y bodega.
    """

    # READ-ONLY - Información enriquecida del producto
    producto_detalle = serializers.SerializerMethodField()

    # READ-ONLY - Información enriquecida de la bodega
    bodega_detalle = serializers.SerializerMethodField()

    # READ-ONLY - Información de ubicación
    ubicacion_nombre = serializers.CharField(source='ubicacion.nombre', read_only=True)

    # Campos calculados
    stock_disponible = serializers.SerializerMethodField()
    valor_inventario = serializers.SerializerMethodField()
    estado_stock = serializers.SerializerMethodField()
    necesita_reposicion = serializers.SerializerMethodField()
    porcentaje_reservado = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = [
            'id',
            'producto', 'producto_detalle',
            'bodega', 'bodega_detalle',
            'ubicacion', 'ubicacion_nombre',
            'cantidad', 'stock_reservado', 'stock_disponible',
            'valor_inventario', 'estado_stock', 'necesita_reposicion',
            'porcentaje_reservado',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'cantidad', 'stock_reservado',
            'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('inventario_bodega_serializer')

    # ==================== MÉTODOS DE SERIALIZACIÓN ====================

    def get_producto_detalle(self, obj):
        """Retorna información completa del producto"""
        producto = obj.producto
        return {
            'id': str(producto.id),
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'categoria': {
                'id': str(producto.categoria.id) if producto.categoria else None,
                'nombre': producto.categoria.nombre if producto.categoria else None
            } if producto.categoria else None,
            'marca': {
                'id': str(producto.marca.id) if producto.marca else None,
                'nombre': producto.marca.nombre if producto.marca else None
            } if producto.marca else None,
            'unidad_medida': {
                'nombre': producto.unidad_medida.nombre if producto.unidad_medida else None,
                'abreviatura': producto.unidad_medida.abreviatura if producto.unidad_medida else None
            } if producto.unidad_medida else None,
            'precio_compra': float(producto.precio_compra) if producto.precio_compra else 0,
            'precio_venta': float(producto.precio_venta) if producto.precio_venta else 0,
            'stock_minimo': producto.stock_minimo,
            'stock_total': producto.stock,
            'es_perecedero': producto.es_perecedero,
            'imagen': producto.imagen.url if producto.imagen else None
        }

    def get_bodega_detalle(self, obj):
        """Retorna información completa de la bodega"""
        bodega = obj.bodega
        return {
            'id': str(bodega.id),
            'codigo': bodega.codigo,
            'nombre': bodega.nombre,
            'ciudad': bodega.ciudad.name if bodega.ciudad else None,
            'es_principal': bodega.es_principal,
            'permite_ventas': bodega.permite_ventas,
            'responsable': {
                'id': str(bodega.responsable.id) if bodega.responsable else None,
                'nombre': bodega.responsable.persona.full_name() if bodega.responsable else None
            } if bodega.responsable else None
        }

    def get_stock_disponible(self, obj):
        """Calcula stock disponible"""
        return obj.stock_disponible

    def get_valor_inventario(self, obj):
        """Calcula valor del inventario (cantidad × precio_compra)"""
        try:
            precio_compra = obj.producto.precio_compra or 0
            return float(obj.cantidad * precio_compra)
        except Exception as e:
            self.logger.warning(f"Error calculando valor inventario: {e}")
            return 0.0

    def get_estado_stock(self, obj):
        """
        Determina el estado del stock.
        Retorna: 'sin_stock', 'critico', 'bajo', 'normal'
        """
        stock_minimo = obj.producto.stock_minimo or 0

        if obj.cantidad == 0:
            return 'sin_stock'
        elif obj.cantidad <= stock_minimo / 2:
            return 'critico'
        elif obj.cantidad <= stock_minimo:
            return 'bajo'
        else:
            return 'normal'

    def get_necesita_reposicion(self, obj):
        """Indica si el producto necesita reposición"""
        stock_minimo = obj.producto.stock_minimo or 0
        return obj.cantidad <= stock_minimo

    def get_porcentaje_reservado(self, obj):
        """Calcula porcentaje de stock reservado"""
        if obj.cantidad == 0:
            return 0.0
        return round((obj.stock_reservado / obj.cantidad) * 100, 2)

    # ==================== REPRESENTACIÓN ====================

    def to_representation(self, instance):
        """Enriquece la respuesta con información adicional"""
        data = super().to_representation(instance)

        # Agregar alertas si hay problemas
        alertas = []

        if instance.cantidad == 0:
            alertas.append({
                'tipo': 'sin_stock',
                'mensaje': 'Producto sin stock'
            })
        elif self.get_necesita_reposicion(instance):
            alertas.append({
                'tipo': 'reposicion',
                'mensaje': 'Producto necesita reposición'
            })

        if instance.stock_reservado > 0:
            alertas.append({
                'tipo': 'reservas',
                'mensaje': f'{instance.stock_reservado} unidades reservadas'
            })

        if alertas:
            data['alertas'] = alertas

        return data