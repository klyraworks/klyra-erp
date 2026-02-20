# apis/inventario/producto/producto_serializer.py
import logging

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apis.inventario.categoria.categoria_viewset import CategoriaSerializer
from apis.inventario.bodega.bodega_serializer import BodegaSerializer, BodegaSimpleSerializer
from apis.inventario.marca.marca_viewset import MarcaSerializer
from apis.inventario.unidad_medida.unidad_medida_viewset import UnidadMedidaSerializer
from apps.inventario.models import (Producto, Marca, UnidadMedida, KitComponente, UnidadConversion, Stock)
from utils.validators import BusinessValidators

# ==================== SERIALIZERS AUXILIARES ====================

class KitComponenteSerializer(TenantSerializer):
    """Serializer para componentes de kits"""
    componente_nombre = serializers.CharField(source='componente.nombre', read_only=True)
    componente_codigo = serializers.CharField(source='componente.codigo', read_only=True)
    componente_precio = serializers.DecimalField(source='componente.precio_venta', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = KitComponente
        fields = [
            'id', 'componente', 'componente_nombre', 'componente_codigo',
            'componente_precio', 'cantidad', 'es_opcional', 'observaciones'
        ]
        read_only_fields = ['id']


class UnidadConversionSerializer(TenantSerializer):
    """Serializer para conversiones de unidades"""
    unidad_origen_nombre = serializers.CharField(source='unidad_origen.nombre', read_only=True)
    unidad_destino_nombre = serializers.CharField(source='unidad_destino.nombre', read_only=True)

    class Meta:
        model = UnidadConversion
        fields = [
            'id', 'unidad_origen', 'unidad_origen_nombre',
            'unidad_destino', 'unidad_destino_nombre', 'factor_conversion'
        ]
        read_only_fields = ['id']


class StockSerializer(TenantSerializer):
    """Serializer para conversiones de unidades"""
    cantidad = serializers.IntegerField(read_only=True)
    stock_reservado = serializers.IntegerField(read_only=True)
    bodega = BodegaSimpleSerializer(read_only=True)


    class Meta:
        model = Stock
        fields = [
            'id', 'cantidad', 'stock_reservado', 'bodega'
        ]
        read_only_fields = ['id']


# ==================== SERIALIZER PRINCIPAL ====================


class ProductoSerializer(TenantSerializer):
    """
    Serializer completo para gestión de productos.

    Soporta:
    - Productos simples
    - Kits/paquetes con componentes
    - Servicios
    - Conversiones de unidades

    OPTIMIZACIONES:
    - Usa annotate del ViewSet para evitar queries en to_representation
    - total_componentes_count (annotated)
    - costo_componentes_sum (annotated)
    - stock_estado_calc (annotated)
    """

    # READ-ONLY - Relaciones anidadas
    categoria_detalle = CategoriaSerializer(source='categoria', read_only=True)
    marca_detalle = MarcaSerializer(source='marca', read_only=True)
    unidad_medida_detalle = UnidadMedidaSerializer(source='unidad_medida', read_only=True)
    componentes_detalle = KitComponenteSerializer(source='componentes', many=True, read_only=True)
    conversiones_detalle = UnidadConversionSerializer(source='conversiones', many=True, read_only=True)

    # WRITE - Para crear/actualizar componentes de kit
    componentes_data = KitComponenteSerializer(many=True, write_only=True, required=False)
    conversiones_data = UnidadConversionSerializer(many=True, write_only=True, required=False)
    inventarios = StockSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'tipo', 'es_kit',
            'categoria', 'categoria_detalle',
            'marca', 'marca_detalle',
            'unidad_medida', 'unidad_medida_detalle',
            'precio_compra', 'precio_venta', 'stock_minimo',
            'iva', 'codigo_barras', 'es_perecedero', 'dias_vida_util',
            'peso', 'imagen', 'is_active',
            'componentes_detalle', 'componentes_data',
            'conversiones_detalle', 'conversiones_data',
            'created_at', 'updated_at', 'inventarios'
        ]
        read_only_fields = ['id', 'codigo', 'created_at', 'updated_at']
        extra_kwargs = {
            'categoria': {'required': False, 'allow_null': True},
            'marca': {'required': False, 'allow_null': True},
            'unidad_medida': {'required': False, 'allow_null': True},
            'descripcion': {'required': False, 'allow_blank': True},
            'codigo_barras': {'required': False, 'allow_blank': True},
            'imagen': {'required': False, 'allow_null': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('producto_serializer')

        # Si el usuario no tiene permiso para ver costos, ocultar precio_compra
        request = self.context.get('request')
        if request and not request.user.has_perm('inventario.ver_costo_compra'):
            self.fields.pop('precio_compra', None)

    # ==================== SERIALIZATION ====================

    def to_representation(self, instance):
        """
        Enriquece la respuesta con información calculada.

        Usa valores annotated en lugar de queries
        """
        data = super().to_representation(instance)

        # Estado del producto
        data['estado'] = 'Activo' if instance.is_active else 'Inactivo'

        # OPTIMIZACIÓN: Usar stock_estado_calc (annotated en ViewSet)
        if hasattr(instance, 'stock_estado_calc'):
            data['stock_estado'] = instance.stock_estado_calc
        else:
            # Fallback si no viene annotated (ej: en create/update)
            data['stock_estado'] = self._get_stock_estado(instance)

        # Margen de ganancia (solo si puede ver costos)
        request = self.context.get('request')
        if request and request.user.has_perm('inventario.ver_costo_compra'):
            if instance.precio_compra and instance.precio_venta:
                margen = instance.precio_venta - instance.precio_compra
                margen_porcentaje = (margen / instance.precio_compra) * 100
                data['margen_ganancia'] = {
                    'monto': float(margen),
                    'porcentaje': round(float(margen_porcentaje), 2)
                }

        # OPTIMIZACIÓN: Información de kit sin queries adicionales
        if instance.es_kit:
            # Usar annotate en lugar de .count()
            if hasattr(instance, 'total_componentes_count'):
                data['total_componentes'] = instance.total_componentes_count
            else:
                # Fallback: Si viene con prefetch_related, no hace query extra
                data['total_componentes'] = len(instance.componentes.all())

            # Usar annotate en lugar de loop
            if hasattr(instance, 'costo_componentes_sum'):
                data['costo_componentes'] = float(instance.costo_componentes_sum or 0)
            else:
                # Fallback: Calcular solo si no viene annotated
                data['costo_componentes'] = self._calcular_costo_kit(instance)

        # Tipo legible
        data['tipo_display'] = instance.get_tipo_display()

        return data

    def _get_stock_estado(self, instance):
        """Determina el estado del stock (fallback si no viene annotated)"""
        if instance.stock <= 0:
            return 'agotado'
        elif instance.stock <= instance.stock_minimo:
            return 'bajo'
        elif instance.stock <= instance.stock_minimo * 1.5:
            return 'medio'
        return 'normal'

    def _calcular_costo_kit(self, instance):
        """
        Calcula el costo total de los componentes del kit.
        Solo se usa como fallback si no viene annotated
        """
        try:
            # Si viene con prefetch_related, esto no genera queries
            total = sum(
                comp.componente.precio_compra * comp.cantidad
                for comp in instance.componentes.all()
            )
            return float(total)
        except:
            return 0

    # ==================== VALIDATIONS ====================

    def validate_nombre(self, value):
        """Valida unicidad del nombre"""
        value = value.strip()
        empresa = self.get_empresa_from_context()

        if self.instance and self.instance.nombre == value:
            return value

        if Producto.objects.filter(nombre__iexact=value, empresa=empresa).exists():
            raise serializers.ValidationError(f"El producto: [{value.upper()}] ya existe")

        return value

    def validate_codigo_barras(self, value):
        """Valida código de barras si existe"""
        if not value:
            return value

        value = value.strip()

        if self.instance and self.instance.codigo_barras == value:
            return value

        if Producto.objects.filter(codigo_barras=value).exists():
            raise serializers.ValidationError(f"El código de barras {value} ya está registrado")

        return value

    def validate_precio_compra(self, value):
        """Valida precio de compra"""
        if value < 0:
            raise serializers.ValidationError("El precio de compra <strong>no puede ser negativo</strong>")
        return value

    def validate_precio_venta(self, value):
        """Valida que el precio de venta sea positivo y no exceda límites razonables"""
        if value <= 0:
            raise serializers.ValidationError("El precio de venta debe <strong>ser mayor a 0</strong>")
        # if value > 1000000:
        #     raise serializers.ValidationError("El precio de venta excede el límite permitido")
        return value

    def validate_stock(self, value):
        """Valida stock"""
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo")
        return value

    def validate_stock_minimo(self, value):
        """Valida stock mínimo"""
        if value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo")
        return value

    def validate_dias_vida_util(self, value):
        """Valida días de vida útil para productos perecederos"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Los días de vida útil deben ser mayores a 0")
        return value

    def validate_peso(self, value):
        """Valida peso del producto"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor a 0")
        return value

    # ==================== CROSS-FIELD VALIDATION ====================

    def validate(self, attrs):
        """Validaciones cruzadas"""
        tipo = attrs.get('tipo', getattr(self.instance, 'tipo', 'simple'))
        es_kit = attrs.get('es_kit', getattr(self.instance, 'es_kit', False))
        es_perecedero = attrs.get('es_perecedero', getattr(self.instance, 'es_perecedero', False))

        # Validar coherencia tipo-es_kit
        if tipo == 'kit' and not es_kit:
            attrs['es_kit'] = True
        elif tipo != 'kit' and es_kit:
            raise serializers.ValidationError("Si es_kit=True, el tipo debe ser [kit]")

        # Validar días de vida útil para perecederos
        if es_perecedero:
            dias = attrs.get('dias_vida_util', getattr(self.instance, 'dias_vida_util', None))
            if not dias:
                raise serializers.ValidationError("Los productos perecederos requieren días de vida útil")

        # Validar precio de venta > precio de compra
        precio_compra = attrs.get('precio_compra', getattr(self.instance, 'precio_compra', None))
        precio_venta = attrs.get('precio_venta', getattr(self.instance, 'precio_venta', None))

        if precio_compra and precio_venta and precio_venta <= precio_compra:
            self.logger.warning(
                f"Precio de venta ({precio_venta}) menor o igual al de compra ({precio_compra})"
            )

        # Validar que kits no tengan stock manual
        if es_kit and 'stock' in attrs and attrs['stock'] != 0:
            self.logger.warning("Los kits no deberían tener stock manual, se calcula por componentes")

        return attrs

    # ==================== CREATE ====================

    def create(self, validated_data):
        """Crea producto con componentes y conversiones en transacción"""
        componentes_data = validated_data.pop('componentes_data', [])
        conversiones_data = validated_data.pop('conversiones_data', [])

        try:
            with transaction.atomic():
                # 1. Crear producto
                validated_data['stock'] = 0
                validated_data['is_active'] = True
                validated_data['empresa'] = self.get_empresa_from_context()
                producto = Producto.objects.create(**validated_data)

                self.logger.info(
                    f"Producto creado: {producto.id} - {producto.codigo}",
                    extra={
                        'producto_id': producto.id,
                        'codigo': producto.codigo,
                        'nombre': producto.nombre,
                        'tipo': producto.tipo
                    }
                )

                # 2. Crear componentes si es kit
                if producto.es_kit and componentes_data:
                    self._crear_componentes(producto, componentes_data)

                # 3. Crear conversiones de unidades
                if conversiones_data:
                    self._crear_conversiones(producto, conversiones_data)

                return producto

        except Exception as e:
            self.logger.exception(f"Error creando producto: {str(e)}")
            raise serializers.ValidationError(f"Error al crear producto: {str(e)}")

    def _crear_componentes(self, producto, componentes_data):
        componentes = []

        try:
            for comp_data in componentes_data:
                componente = comp_data['componente']

                if componente.id == producto.id:
                    raise serializers.ValidationError(
                        "Un producto no puede ser componente de sí mismo"
                    )

                if componente.es_kit:
                    raise serializers.ValidationError(
                        "Los kits no pueden contener otros kits como componentes"
                    )

                componentes.append(
                    KitComponente(
                        kit=producto,
                        componente=componente,
                        cantidad=comp_data['cantidad'],
                        es_opcional=comp_data.get('es_opcional', False),
                        observaciones=comp_data.get('observaciones', ''),
                        empresa=producto.empresa

                    )
                )

            KitComponente.objects.bulk_create(componentes)
            self.logger.info(f"Componentes creados para kit {producto.id}: {len(componentes_data)}")
        except Exception as e:
            self.logger.exception(f"Error creando componentes para kit {producto.id}: {str(e)}")
            raise serializers.ValidationError(f"Error al crear componentes del kit: {str(e)}")

    def _crear_conversiones(self, producto, conversiones_data):
        """Crea conversiones de unidades"""
        conversiones = []

        for conv_data in conversiones_data:

            if conv_data['unidad_origen'] == conv_data['unidad_destino']:
                raise ValidationError("La unidad de origen y destino no pueden ser iguales")

            conversiones.append(
                UnidadConversion(
                    producto=producto,
                    unidad_origen=conv_data['unidad_origen'],
                    unidad_destino=conv_data['unidad_destino'],
                    factor_conversion=conv_data['factor_conversion'],
                    empresa=producto.empresa
                )
            )

        self.logger.info(f"Conversiones creadas para producto {producto.id}: {len(conversiones_data)}")

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        """Actualiza producto con tracking de cambios"""
        componentes_data = validated_data.pop('componentes_data', None)
        conversiones_data = validated_data.pop('conversiones_data', None)

        try:
            with transaction.atomic():
                cambios_criticos = {}

                # 1. Actualizar campos del producto
                for field, value in validated_data.items():
                    old_value = getattr(instance, field)
                    if old_value != value:
                        # Trackear cambios críticos
                        if field in ['precio_compra', 'precio_venta', 'stock']:
                            cambios_criticos[field] = {
                                'anterior': str(old_value),
                                'nuevo': str(value)
                            }
                        setattr(instance, field, value)

                instance.save()

                # 2. Actualizar componentes si es kit
                if componentes_data is not None and instance.es_kit:
                    # Eliminar componentes existentes
                    instance.componentes.all().delete()
                    # Crear nuevos componentes
                    self._crear_componentes(instance, componentes_data)

                # 3. Actualizar conversiones
                if conversiones_data is not None:
                    instance.conversiones.all().delete()
                    self._crear_conversiones(instance, conversiones_data)

                # Log
                log_data = {
                    'producto_id': instance.id,
                    'codigo': instance.codigo
                }

                if cambios_criticos:
                    log_data['cambios_criticos'] = cambios_criticos

                self.logger.info(
                    f"Producto {instance.id} actualizado",
                    extra=log_data
                )

                return instance

        except Exception as e:
            self.logger.exception(f"Error actualizando producto: {str(e)}")
            raise


# ==================== SERIALIZER SIMPLIFICADO ====================

class ProductoSimpleSerializer(TenantSerializer):
    """
    Serializer simplificado para listados rápidos.

    Usa stock_estado_calc annotated del ViewSet
    """
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    marca_nombre = serializers.CharField(source='marca.nombre', read_only=True)
    stock_estado = serializers.SerializerMethodField()
    unidad_medida = serializers.CharField(source='unidad_medida.nombre', read_only=True)
    inventarios = StockSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'codigo_aux', 'nombre', 'tipo', 'precio_venta', 'stock_minimo', 'stock_estado',
            'categoria_nombre', 'marca_nombre', 'is_active',
            'descripcion', 'unidad_medida', 'inventarios'
        ]

    def get_stock_estado(self, obj):
        """
        Usar annotate si existe, fallback a cálculo
        """
        if hasattr(obj, 'stock_estado_calc'):
            return obj.stock_estado_calc

        # Fallback: calcular desde stocks
        stock_total = sum(s.cantidad for s in obj.stocks.all())

        if stock_total <= 0:
            return 'agotado'
        elif stock_total <= obj.stock_minimo:
            return 'bajo'
        elif stock_total <= obj.stock_minimo * 1.5:
            return 'medio'
        return 'normal'

"""
Ejemplo de JSON para crear un producto simple:
{
    "productos": [
        {
            "nombre": "Discos de freno Yamaha YZF-R3",
            "descripcion": "Disco de freno delantero perforado para Yamaha YZF-R3 2020-2023",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "a30aea77-6e33-47bf-9ec9-6c5f02f99ee9",
            "marca": "9f356665-4db4-424a-aafb-43f5acc1d75a",
            "unidad_medida": "12df4fc9-4329-4182-a6b4-e8994710dbc9",
            "precio_compra": 95.00,
            "precio_venta": 135.00,
            "stock_minimo": 3,
            "iva": true,
            "codigo_barras": "7501334562903",
            "es_perecedero": false,
            "peso": 2.8
        },
        {
            "nombre": "Alternador Honda CBR 600RR",
            "descripcion": "Alternador completo 12V para Honda CBR 600RR 2015-2020",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "032503ac-1d8a-489d-8ed6-6d1b34f074f1",
            "marca": "1f90553e-ee91-42cd-9d3a-5f16127443d7",
            "unidad_medida": "5ef5bce5-0c50-43dc-8f90-d300b864bd59",
            "precio_compra": 120.00,
            "precio_venta": 165.00,
            "stock_minimo": 2,
            "iva": true,
            "codigo_barras": "7501334562904",
            "es_perecedero": false,
            "peso": 3.2
        },
        {
            "nombre": "Kit de embrague Suzuki GSX-R750",
            "descripcion": "Kit completo de embrague húmedo para Suzuki GSX-R750 2017-2022",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "3372122b-a2c9-4c1b-ab8f-6b64c306b853",
            "marca": "9bcd244b-48d9-49c3-b2cf-c49ed816c096",
            "unidad_medida": "a8992d0e-f190-42c3-9ce9-7df23294fd07",
            "precio_compra": 180.00,
            "precio_venta": 245.00,
            "stock_minimo": 2,
            "iva": true,
            "codigo_barras": "7501334562905",
            "es_perecedero": false,
            "peso": 2.5
        },
        {
            "nombre": "Horquilla invertida KTM Duke 390",
            "descripcion": "Horquilla delantera invertida completa para KTM Duke 390 2017-2023",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "49f6ebd2-8b39-4fca-90aa-8d62493b22e7",
            "marca": "baf63d49-cf8a-44d8-9844-bb88b330a8ca",
            "unidad_medida": "5ef5bce5-0c50-43dc-8f90-d300b864bd59",
            "precio_compra": 320.00,
            "precio_venta": 420.00,
            "stock_minimo": 1,
            "iva": true,
            "codigo_barras": "7501334562906",
            "es_perecedero": false,
            "peso": 8.5
        },
        {
            "nombre": "Escape completo Ducati Panigale V4",
            "descripcion": "Sistema de escape completo racing para Ducati Panigale V4 2018-2023",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "c687439a-08c1-4591-833c-34d267671bf7",
            "marca": "57fda42c-dfa4-45b8-8f8c-3d51824be788",
            "unidad_medida": "a8992d0e-f190-42c3-9ce9-7df23294fd07",
            "precio_compra": 850.00,
            "precio_venta": 1150.00,
            "stock_minimo": 1,
            "iva": true,
            "codigo_barras": "7501334562907",
            "es_perecedero": false,
            "peso": 6.8
        },
        {
            "nombre": "Carenaje Harley-Davidson Sportster",
            "descripcion": "Juego de carenaje completo para Harley-Davidson Sportster 883",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "67369717-e3c5-4bfd-bf45-5dde18651779",
            "marca": "670371aa-4587-494c-b232-4e2985108628",
            "unidad_medida": "a8992d0e-f190-42c3-9ce9-7df23294fd07",
            "precio_compra": 280.00,
            "precio_venta": 380.00,
            "stock_minimo": 2,
            "iva": true,
            "codigo_barras": "7501334562908",
            "es_perecedero": false,
            "peso": 5.2
        },
        {
            "nombre": "Inyectores Kawasaki Ninja ZX-6R",
            "descripcion": "Juego de 4 inyectores de combustible para Kawasaki Ninja ZX-6R",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "d1ed44e1-ab0b-43f6-a746-10bcee06d2c0",
            "marca": "29816f6c-467a-4433-a491-3b1d1d91646d",
            "unidad_medida": "19992f01-5657-4c2e-9a91-784fc541b201",
            "precio_compra": 165.00,
            "precio_venta": 225.00,
            "stock_minimo": 2,
            "iva": true,
            "codigo_barras": "7501334562909",
            "es_perecedero": false,
            "peso": 1.8
        },
        {
            "nombre": "Llantas de aleación Hero Xtreme",
            "descripcion": "Par de llantas de aleación 17\" para Hero Xtreme 160R",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "79fbfd80-456a-49cb-af93-78dcddd82709",
            "marca": "862dbf63-6a45-4698-ad57-515a9714e466",
            "unidad_medida": "12df4fc9-4329-4182-a6b4-e8994710dbc9",
            "precio_compra": 110.00,
            "precio_venta": 155.00,
            "stock_minimo": 2,
            "iva": true,
            "codigo_barras": "7501334562910",
            "es_perecedero": false,
            "peso": 12.3
        },
        {
            "nombre": "Kit de herramientas premium",
            "descripcion": "Set profesional de herramientas para motocicletas de alta gama",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "3a0cba58-027a-43b4-93e0-b2e9b7c42ea9",
            "marca": "57fda42c-dfa4-45b8-8f8c-3d51824be788",
            "unidad_medida": "a8992d0e-f190-42c3-9ce9-7df23294fd07",
            "precio_compra": 75.00,
            "precio_venta": 105.00,
            "stock_minimo": 3,
            "iva": true,
            "codigo_barras": "7501334562911",
            "es_perecedero": false,
            "peso": 4.5
        },
        {
            "nombre": "Radiador de aluminio TVS Apache RR310",
            "descripcion": "Radiador de aluminio de alta eficiencia para TVS Apache RR310",
            "tipo": "simple",
            "es_kit": false,
            "categoria": "d0c42171-bb36-46f1-b1cb-fc2708d592bb",
            "marca": "c04430f1-0ac1-422a-a6cb-f49be9972810",
            "unidad_medida": "5ef5bce5-0c50-43dc-8f90-d300b864bd59",
            "precio_compra": 90.00,
            "precio_venta": 125.00,
            "stock_minimo": 3,
            "iva": true,
            "codigo_barras": "7501334562912",
            "es_perecedero": false,
            "peso": 2.7
        }
    ]
}

Ejemplo de JSON para crear un kit:
{
  "codigo": "KIT-001",
  "nombre": "Kit Oficina Básico",
  "descripcion": "Kit completo para equipar una oficina básica",
  "tipo": "kit",
  "es_kit": true,
  "categoria": "c1045b78-ac22-4f84-8db1-2ab06fe54d97",
  "marca": "7e8b3e97-ef24-4630-b95c-15086a565995",
  "unidad_medida": "477fbd99-7a3e-4d8a-965c-cb4af2f9ee56",
  "precio_compra": 800.00,
  "precio_venta": 1100.00,
  "stock": 0,
  "stock_minimo": 0,
  "iva": true,
  "componentes_data": [
    {
      "componente": "9026e018-d67a-4f92-971f-3196bae20e16",
      "cantidad": 1,
      "es_opcional": false,
      "observaciones": "Laptop Dell Inspiron 15"
    },
    {
      "componente": "99f19516-ca40-4a88-99dc-8f6ff6e3a176",
      "cantidad": 1,
      "es_opcional": false,
      "observaciones": "Mouse Dell 10k DPI"
    },
    {
      "componente": "43bfa394-c964-4384-8443-85c91a5d5efd",
      "cantidad": 1,
      "es_opcional": true,
      "observaciones": "Teclado mecánico"
    }
  ]
}

"""
