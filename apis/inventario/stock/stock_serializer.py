import logging
from rest_framework import serializers
from django.db.models import F

from apis.core.SerializerBase import TenantSerializer
from apps.inventario.models import Stock


logger = logging.getLogger('apps.inventario')


class InventarioBodegaListSerializer(TenantSerializer):
    producto_id      = serializers.UUIDField(source='producto.id', read_only=True)
    producto_codigo  = serializers.CharField(source='producto.codigo', read_only=True)
    producto_nombre  = serializers.CharField(source='producto.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    unidad_medida    = serializers.CharField(source='producto.unidad_medida.abreviatura', read_only=True)
    bodega_id        = serializers.UUIDField(source='bodega.id', read_only=True)
    bodega_codigo    = serializers.CharField(source='bodega.codigo', read_only=True)
    bodega_nombre    = serializers.CharField(source='bodega.nombre', read_only=True)
    stock_disponible    = serializers.SerializerMethodField()
    estado_stock        = serializers.SerializerMethodField()
    necesita_reposicion = serializers.SerializerMethodField()

    class Meta:
        model  = Stock
        fields = [
            'id',
            'producto_id', 'producto_codigo', 'producto_nombre',
            'categoria_nombre', 'unidad_medida',
            'bodega_id', 'bodega_codigo', 'bodega_nombre',
            'cantidad', 'stock_reservado', 'stock_disponible',
            'estado_stock', 'necesita_reposicion',
        ]

    def get_stock_disponible(self, obj):
        return max(obj.cantidad - obj.stock_reservado, 0)

    def get_estado_stock(self, obj):
        stock_minimo = obj.producto.stock_minimo or 0
        if obj.cantidad == 0:
            return 'sin_stock'
        elif obj.cantidad <= stock_minimo / 2:
            return 'critico'
        elif obj.cantidad <= stock_minimo:
            return 'bajo'
        return 'normal'

    def get_necesita_reposicion(self, obj):
        return obj.cantidad <= (obj.producto.stock_minimo or 0)


class StockSerializer(TenantSerializer):
    producto_detalle    = serializers.SerializerMethodField()
    bodega_detalle      = serializers.SerializerMethodField()
    stock_disponible    = serializers.SerializerMethodField()
    valor_inventario    = serializers.SerializerMethodField()
    estado_stock        = serializers.SerializerMethodField()
    necesita_reposicion = serializers.SerializerMethodField()
    porcentaje_reservado = serializers.SerializerMethodField()

    class Meta:
        model  = Stock
        fields = [
            'id',
            'producto', 'producto_detalle',
            'bodega', 'bodega_detalle',
            'ubicacion',
            'cantidad', 'stock_reservado', 'stock_disponible',
            'valor_inventario', 'estado_stock', 'necesita_reposicion',
            'porcentaje_reservado',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'cantidad', 'stock_reservado', 'created_at', 'updated_at']

    def get_producto_detalle(self, obj):
        p = obj.producto
        return {
            'id': str(p.id),
            'codigo': p.codigo,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'categoria': {'id': str(p.categoria.id), 'nombre': p.categoria.nombre} if p.categoria else None,
            'marca': {'id': str(p.marca.id), 'nombre': p.marca.nombre} if p.marca else None,
            'unidad_medida': {
                'nombre': p.unidad_medida.nombre,
                'abreviatura': p.unidad_medida.abreviatura,
            } if p.unidad_medida else None,
            'precio_venta': float(p.precio_venta) if p.precio_venta else 0,
            'stock_minimo': float(p.stock_minimo) if p.stock_minimo else 0,
            'es_perecedero': p.es_perecedero,
            'imagen': p.imagen.url if p.imagen else None,
        }

    def get_bodega_detalle(self, obj):
        b = obj.bodega
        return {
            'id': str(b.id),
            'codigo': b.codigo,
            'nombre': b.nombre,
            'es_principal': b.es_principal,
            'permite_ventas': b.permite_ventas,
            'responsable': {
                'id': str(b.responsable.id),
                'nombre': b.responsable.persona.full_name(),
            } if b.responsable else None,
        }

    def get_stock_disponible(self, obj):
        return max(obj.cantidad - obj.stock_reservado, 0)

    def get_valor_inventario(self, obj):
        try:
            return float(obj.cantidad * (obj.producto.precio_compra or 0))
        except Exception:
            return 0.0

    def get_estado_stock(self, obj):
        stock_minimo = obj.producto.stock_minimo or 0
        if obj.cantidad == 0:
            return 'sin_stock'
        elif obj.cantidad <= stock_minimo / 2:
            return 'critico'
        elif obj.cantidad <= stock_minimo:
            return 'bajo'
        return 'normal'

    def get_necesita_reposicion(self, obj):
        return obj.cantidad <= (obj.producto.stock_minimo or 0)

    def get_porcentaje_reservado(self, obj):
        if obj.cantidad == 0:
            return 0.0
        return round((obj.stock_reservado / obj.cantidad) * 100, 2)