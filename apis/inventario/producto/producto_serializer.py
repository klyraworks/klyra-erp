import logging
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apis.inventario.unidadconversion.unidadconversion_serializer import UnidadConversionSerializer
from apis.inventario.kitcomponente.kitcomponente_serializer import KitComponenteSerializer
from apps.inventario.models import (
    Producto, Categoria, Marca, UnidadMedida,
    KitComponente, UnidadConversion, Stock
)


logger = logging.getLogger('apps.inventario')


# ==================== AUXILIARES ====================

class StockBodegaSerializer(TenantSerializer):
    bodega_nombre  = serializers.CharField(source='bodega.nombre', read_only=True)
    bodega_codigo  = serializers.CharField(source='bodega.codigo', read_only=True)
    es_principal   = serializers.BooleanField(source='bodega.es_principal', read_only=True)
    permite_ventas = serializers.BooleanField(source='bodega.permite_ventas', read_only=True)
    cantidad_disponible = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True
    )

    class Meta:
        model  = Stock
        fields = [
            'id', 'bodega', 'bodega_nombre', 'bodega_codigo',
            'es_principal', 'permite_ventas',
            'cantidad', 'stock_reservado', 'cantidad_disponible',
        ]
        read_only_fields = ['id']


# ==================== LIST ====================

class ProductoListSerializer(TenantSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    marca_nombre     = serializers.CharField(source='marca.nombre', read_only=True)
    unidad_abrev     = serializers.CharField(source='unidad_medida.abreviatura', read_only=True)
    stock_total      = serializers.SerializerMethodField()
    stock_estado     = serializers.SerializerMethodField()

    class Meta:
        model  = Producto
        fields = [
            'id', 'codigo', 'codigo_aux', 'nombre', 'tipo', 'es_kit',
            'precio_venta', 'stock_minimo',
            'categoria_nombre', 'marca_nombre', 'unidad_abrev',
            'stock_total', 'stock_estado', 'is_active',
        ]

    def get_stock_total(self, obj):
        if hasattr(obj, 'stock_total_anotado'):
            return obj.stock_total_anotado or 0
        return sum(s.cantidad for s in obj.stocks.all())

    def get_stock_estado(self, obj):
        if hasattr(obj, 'stock_estado_calc'):
            return obj.stock_estado_calc
        stock = self.get_stock_total(obj)
        return _calcular_stock_estado(stock, obj.stock_minimo)


# ==================== DETAIL ====================

class ProductoDetailSerializer(TenantSerializer):
    categoria     = serializers.SerializerMethodField()
    marca         = serializers.SerializerMethodField()
    unidad_medida = serializers.SerializerMethodField()
    precio_compra  = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    precio_venta   = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    costo_promedio = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    ultimo_costo   = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    componentes    = KitComponenteSerializer(many=True, read_only=True)
    conversiones   = UnidadConversionSerializer(many=True, read_only=True)
    inventarios    = serializers.SerializerMethodField()
    margen_ganancia = serializers.SerializerMethodField()
    stock_total     = serializers.SerializerMethodField()
    stock_estado    = serializers.SerializerMethodField()
    tipo_display    = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Producto
        fields = [
            'id', 'codigo', 'codigo_aux', 'nombre', 'descripcion',
            'categoria', 'marca', 'unidad_medida',
            'tipo', 'tipo_display', 'es_kit',
            'precio_compra', 'precio_venta', 'stock_minimo',
            'iva', 'codigo_barras',
            'es_perecedero', 'dias_vida_util',
            'peso', 'imagen',
            'costo_promedio', 'ultimo_costo',
            'margen_ganancia', 'stock_total', 'stock_estado',
            'componentes', 'conversiones', 'inventarios',
            'is_active', 'created_at', 'updated_at',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and not request.user.has_perm('inventario.ver_costo_compra'):
            self.fields.pop('precio_compra', None)
            self.fields.pop('costo_promedio', None)
            self.fields.pop('ultimo_costo', None)
            self.fields.pop('margen_ganancia', None)

    def get_categoria(self, obj):
        if obj.categoria:
            return {'id': str(obj.categoria.id), 'nombre': obj.categoria.nombre, 'codigo': obj.categoria.codigo}
        return None

    def get_marca(self, obj):
        if obj.marca:
            return {'id': str(obj.marca.id), 'nombre': obj.marca.nombre}
        return None

    def get_unidad_medida(self, obj):
        if obj.unidad_medida:
            return {
                'id': str(obj.unidad_medida.id),
                'nombre': obj.unidad_medida.nombre,
                'abreviatura': obj.unidad_medida.abreviatura,
            }
        return None

    def get_margen_ganancia(self, obj):
        if obj.precio_compra and obj.precio_venta and obj.precio_compra > 0:
            margen = obj.precio_venta - obj.precio_compra
            return {
                'monto': float(margen),
                'porcentaje': round(float((margen / obj.precio_compra) * 100), 2),
            }
        return None

    def get_stock_total(self, obj):
        if hasattr(obj, 'stock_total_anotado'):
            return obj.stock_total_anotado or 0
        return sum(s.cantidad for s in obj.stocks.all())

    def get_stock_estado(self, obj):
        if hasattr(obj, 'stock_estado_calc'):
            return obj.stock_estado_calc
        return _calcular_stock_estado(self.get_stock_total(obj), obj.stock_minimo)

    def get_inventarios(self, obj):
        request = self.context.get('request')
        stocks = obj.stocks.select_related('bodega', 'ubicacion').all()
        if request and not request.user.has_perm('inventario.view_stock_todas_bodegas'):
            stocks = stocks.filter(bodega__responsable__usuario=request.user)
        return StockBodegaSerializer(stocks, many=True).data


# ==================== CREATE ====================

class ProductoCreateSerializer(serializers.Serializer):
    nombre           = serializers.CharField(max_length=200)
    descripcion      = serializers.CharField(required=False, allow_blank=True)
    codigo_aux       = serializers.CharField(max_length=50, required=False, allow_null=True)
    categoria_id     = serializers.UUIDField()
    marca_id         = serializers.UUIDField(required=False, allow_null=True)
    unidad_medida_id = serializers.IntegerField()
    tipo             = serializers.ChoiceField(choices=['simple', 'kit', 'servicio'])
    es_kit           = serializers.BooleanField(default=False)
    precio_compra    = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_venta     = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_minimo     = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva              = serializers.BooleanField(default=False)
    codigo_barras    = serializers.CharField(max_length=50, required=False, allow_blank=True)
    es_perecedero    = serializers.BooleanField(default=False)
    dias_vida_util   = serializers.IntegerField(required=False, allow_null=True)
    peso             = serializers.DecimalField(max_digits=8, decimal_places=3, required=False, allow_null=True)
    imagen           = serializers.ImageField(required=False, allow_null=True)
    componentes_data = KitComponenteSerializer(many=True, required=False, write_only=True)
    conversiones_data = UnidadConversionSerializer(many=True, required=False, write_only=True)

    def validate_categoria_id(self, value):
        empresa = self.context['request'].empresa
        if not Categoria.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("La categoría no existe o no pertenece a esta empresa.")
        return value

    def validate_marca_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Marca.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("La marca no existe o no pertenece a esta empresa.")
        return value

    def validate_unidad_medida_id(self, value):
        if not UnidadMedida.objects.filter(id=value).exists():
            raise ValidationError("La unidad de medida no existe.")
        return value

    def validate_nombre(self, value):
        value = value.strip()
        empresa = self.context['request'].empresa
        if Producto.objects.filter(nombre__iexact=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError(f"Ya existe un producto con el nombre '{value}'.")
        return value

    def validate_codigo_barras(self, value):
        if not value:
            return value
        empresa = self.context['request'].empresa
        if Producto.objects.filter(codigo_barras=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError(f"El código de barras '{value}' ya está registrado.")
        return value

    def validate_precio_venta(self, value):
        if value <= 0:
            raise ValidationError("El precio de venta debe ser mayor a 0.")
        return value

    def validate_precio_compra(self, value):
        if value < 0:
            raise ValidationError("El precio de compra no puede ser negativo.")
        return value

    def validate(self, attrs):
        es_kit = attrs.get('es_kit', False)
        tipo   = attrs.get('tipo')
        if es_kit and tipo != 'kit':
            raise ValidationError({"tipo": "Si es_kit es True, el tipo debe ser 'kit'."})
        if tipo == 'kit':
            attrs['es_kit'] = True
        if attrs.get('es_perecedero') and not attrs.get('dias_vida_util'):
            raise ValidationError({"dias_vida_util": "Los productos perecederos requieren días de vida útil."})
        return attrs


# ==================== UPDATE ====================

class ProductoUpdateSerializer(TenantSerializer):
    categoria_id      = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    marca_id          = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    unidad_medida_id  = serializers.IntegerField(required=False, write_only=True)
    componentes_data  = KitComponenteSerializer(many=True, required=False, write_only=True)
    conversiones_data = UnidadConversionSerializer(many=True, required=False, write_only=True)

    class Meta:
        model  = Producto
        fields = [
            'nombre', 'descripcion', 'codigo_aux',
            'categoria_id', 'marca_id', 'unidad_medida_id',
            'tipo', 'es_kit',
            'precio_compra', 'precio_venta', 'stock_minimo',
            'iva', 'codigo_barras',
            'es_perecedero', 'dias_vida_util',
            'peso', 'imagen',
            'componentes_data', 'conversiones_data',
        ]

    def validate_nombre(self, value):
        value = value.strip()
        empresa = self.context['request'].empresa
        qs = Producto.objects.filter(nombre__iexact=value, empresa=empresa, deleted_at__isnull=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Ya existe un producto con el nombre '{value}'.")
        return value

    def validate_codigo_barras(self, value):
        if not value:
            return value
        empresa = self.context['request'].empresa
        qs = Producto.objects.filter(codigo_barras=value, empresa=empresa, deleted_at__isnull=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"El código de barras '{value}' ya está registrado.")
        return value

    def validate_categoria_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Categoria.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("La categoría no existe o no pertenece a esta empresa.")
        return value

    def validate_marca_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Marca.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("La marca no existe o no pertenece a esta empresa.")
        return value

    def validate_unidad_medida_id(self, value):
        if value is None:
            return value
        if not UnidadMedida.objects.filter(id=value).exists():
            raise ValidationError("La unidad de medida no existe.")
        return value

    def validate(self, attrs):
        es_kit = attrs.get('es_kit', self.instance.es_kit if self.instance else False)
        tipo   = attrs.get('tipo', self.instance.tipo if self.instance else None)
        if es_kit and tipo != 'kit':
            raise ValidationError({"tipo": "Si es_kit es True, el tipo debe ser 'kit'."})
        if attrs.get('es_perecedero', getattr(self.instance, 'es_perecedero', False)):
            dias = attrs.get('dias_vida_util', getattr(self.instance, 'dias_vida_util', None))
            if not dias:
                raise ValidationError({"dias_vida_util": "Los productos perecederos requieren días de vida útil."})
        return attrs

    def update(self, instance, validated_data):
        componentes_data  = validated_data.pop('componentes_data', ...)
        conversiones_data = validated_data.pop('conversiones_data', ...)
        categoria_id      = validated_data.pop('categoria_id', ...)
        marca_id          = validated_data.pop('marca_id', ...)
        unidad_medida_id  = validated_data.pop('unidad_medida_id', ...)

        if categoria_id is not ...:
            instance.categoria_id = categoria_id
        if marca_id is not ...:
            instance.marca_id = marca_id
        if unidad_medida_id is not ...:
            instance.unidad_medida_id = unidad_medida_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if componentes_data is not ... and instance.es_kit:
            instance.componentes.all().delete()
            _crear_componentes(instance, componentes_data)

        if conversiones_data is not ...:
            instance.conversiones.all().delete()
            _crear_conversiones(instance, conversiones_data)

        return instance


# ==================== HELPERS COMPARTIDOS ====================

def _calcular_stock_estado(stock_total, stock_minimo):
    if not stock_total or stock_total <= 0:
        return 'agotado'
    elif stock_total <= stock_minimo:
        return 'bajo'
    elif stock_total <= stock_minimo * 1.5:
        return 'medio'
    return 'normal'


def _crear_componentes(producto, componentes_data):
    componentes = []
    for comp_data in componentes_data:
        componente = comp_data['componente']
        if componente.id == producto.id:
            raise ValidationError("Un producto no puede ser componente de sí mismo.")
        if componente.es_kit:
            raise ValidationError("Los kits no pueden contener otros kits como componentes.")
        componentes.append(KitComponente(
            kit=producto,
            componente=componente,
            cantidad=comp_data['cantidad'],
            es_opcional=comp_data.get('es_opcional', False),
            observaciones=comp_data.get('observaciones', ''),
            empresa=producto.empresa,
        ))
    KitComponente.objects.bulk_create(componentes)


def _crear_conversiones(producto, conversiones_data):
    conversiones = []
    for conv_data in conversiones_data:
        if conv_data['unidad_origen'] == conv_data['unidad_destino']:
            raise ValidationError("La unidad de origen y destino no pueden ser iguales.")
        conversiones.append(UnidadConversion(
            producto=producto,
            unidad_origen=conv_data['unidad_origen'],
            unidad_destino=conv_data['unidad_destino'],
            factor_conversion=conv_data['factor_conversion'],
            empresa=producto.empresa,
        ))
    UnidadConversion.objects.bulk_create(conversiones)