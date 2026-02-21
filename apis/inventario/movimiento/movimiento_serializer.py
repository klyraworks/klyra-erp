# apis/inventario/movimiento/movimiento_serializer.py
import logging
from decimal import Decimal
from datetime import date

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apps.inventario.models import (
    MovimientoInventario,
    DetalleMovimiento,
    Stock,
    Producto,
    Bodega,
)


class DetalleMovimientoSerializer(TenantSerializer):
    """Serializer para DetalleMovimiento."""

    producto_nombre  = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo  = serializers.CharField(source='producto.codigo', read_only=True)
    unidad_medida    = serializers.CharField(source='producto.unidad_medida.nombre', read_only=True)
    stock_anterior   = serializers.IntegerField(read_only=True)
    stock_posterior  = serializers.IntegerField(read_only=True)

    producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.filter(is_active=True),
        write_only=True,
    )

    class Meta:
        model  = DetalleMovimiento
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo',
            'cantidad', 'costo_unitario', 'lote', 'fecha_vencimiento',
            'unidad_medida', 'stock_anterior', 'stock_posterior', 'observaciones',
        ]
        read_only_fields = ['id', 'stock_anterior', 'stock_posterior']

    def validate_cantidad(self, value):
        if value is None or value <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")
        return value

    def validate_costo_unitario(self, value):
        if value is not None and value < 0:
            raise ValidationError("El costo unitario no puede ser negativo.")
        return value

    def validate(self, attrs):
        producto          = attrs.get('producto')
        fecha_vencimiento = attrs.get('fecha_vencimiento')
        if producto and producto.es_perecedero and not fecha_vencimiento:
            raise ValidationError({
                'fecha_vencimiento': 'La fecha de vencimiento es obligatoria para productos perecederos.',
            })
        return attrs


class MovimientoInventarioSerializer(TenantSerializer):
    """
    Serializer para MovimientoInventario.
    Maneja entradas, salidas, transferencias, ajustes y mermas.
    """

    logger = logging.getLogger('apps.inventario')

    # READ-ONLY
    detalles              = DetalleMovimientoSerializer(many=True, read_only=True)
    responsable_nombre    = serializers.SerializerMethodField()
    bodega_origen_nombre  = serializers.CharField(source='bodega_origen.nombre', read_only=True)
    bodega_destino_nombre = serializers.CharField(source='bodega_destino.nombre', read_only=True)
    autorizado_por_nombre = serializers.SerializerMethodField()
    tipo_display          = serializers.CharField(source='get_tipo_display', read_only=True)
    fecha_local           = serializers.SerializerMethodField()

    # WRITE-ONLY
    from apps.seguridad.models import Empleado

    detalles_data = DetalleMovimientoSerializer(many=True, write_only=True)
    responsable   = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(is_active=True),
        required=False, allow_null=True, write_only=True,
    )
    bodega_origen = serializers.PrimaryKeyRelatedField(
        queryset=Bodega.objects.filter(is_active=True),
        required=False, allow_null=True, write_only=True,
    )
    bodega_destino = serializers.PrimaryKeyRelatedField(
        queryset=Bodega.objects.filter(is_active=True),
        required=False, allow_null=True, write_only=True,
    )

    class Meta:
        model  = MovimientoInventario
        fields = [
            'id', 'numero', 'fecha', 'tipo', 'tipo_display', 'fecha_local',
            'bodega_origen', 'bodega_origen_nombre',
            'bodega_destino', 'bodega_destino_nombre',
            'responsable', 'responsable_nombre', 'referencia', 'observaciones',
            'autorizado_por', 'autorizado_por_nombre',
            'detalles', 'detalles_data', 'estado', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'fecha', 'created_at', 'updated_at']

    # ==================== GET METHODS ====================

    def get_fecha_local(self, obj):
        import pytz
        request = self.context.get('request')
        if request and hasattr(request.user, 'timezone'):
            tz = pytz.timezone(request.user.timezone)
        else:
            tz = pytz.timezone('America/Guayaquil')
        return obj.fecha.astimezone(tz).strftime('%Y-%m-%dT%H:%M:%S')

    def get_responsable_nombre(self, obj):
        if obj.responsable:
            return obj.responsable.persona.full_name()
        return None

    def get_autorizado_por_nombre(self, obj):
        if obj.autorizado_por:
            return obj.autorizado_por.get_full_name()
        return None

    # ==================== VALIDATIONS ====================

    def validate_tipo(self, value):
        tipos_validos = ['entrada', 'salida', 'transferencia', 'ajuste', 'devolucion', 'merma']
        if value not in tipos_validos:
            raise ValidationError(f"Tipo debe ser uno de: {', '.join(tipos_validos)}.")
        return value

    def validate_detalles_data(self, value):
        if not value:
            raise ValidationError("Debe incluir al menos un producto en el movimiento.")

        for detalle in value:
            producto = detalle.get('producto')
            if not producto:
                raise ValidationError("Cada detalle debe incluir un producto.")

            # Auto-llenar costo unitario
            if not detalle.get('costo_unitario'):
                costo_auto = (
                    getattr(producto, 'ultimo_costo', None) or
                    getattr(producto, 'costo_promedio', None) or
                    producto.precio_compra
                )
                detalle['costo_unitario'] = costo_auto

            # Auto-generar número de lote
            if not detalle.get('lote'):
                detalle['lote'] = self._generar_numero_lote(producto)

            # Auto-calcular fecha vencimiento para perecederos
            if producto.es_perecedero and not detalle.get('fecha_vencimiento'):
                if producto.dias_vida_util:
                    from datetime import timedelta
                    detalle['fecha_vencimiento'] = (
                        timezone.now().date() + timedelta(days=producto.dias_vida_util)
                    )
                else:
                    raise ValidationError({
                        'fecha_vencimiento': (
                            f'El producto "{producto.nombre}" es perecedero pero no tiene '
                            'días de vida útil configurados. Configure dias_vida_util o '
                            'proporcione fecha_vencimiento manualmente.'
                        )
                    })

        return value

    def validate(self, attrs):
        tipo           = attrs.get('tipo')
        bodega_origen  = attrs.get('bodega_origen')
        bodega_destino = attrs.get('bodega_destino')

        # Auto-generar referencia si no se provee
        referencia = attrs.get('referencia', '').strip()
        if not referencia:
            attrs['referencia'] = self._generar_referencia_automatica(tipo)

        if tipo == 'entrada':
            if not bodega_destino:
                raise ValidationError({'bodega_destino': 'La bodega destino es obligatoria para entradas.'})
            if bodega_origen:
                raise ValidationError({'bodega_origen': 'Las entradas no deben tener bodega origen.'})

        elif tipo == 'salida':
            if not bodega_origen:
                raise ValidationError({'bodega_origen': 'La bodega origen es obligatoria para salidas.'})
            if bodega_destino:
                raise ValidationError({'bodega_destino': 'Las salidas no deben tener bodega destino.'})

        elif tipo == 'transferencia':
            if not bodega_origen:
                raise ValidationError({'bodega_origen': 'Las transferencias requieren bodega origen.'})
            if not bodega_destino:
                raise ValidationError({'bodega_destino': 'Las transferencias requieren bodega destino.'})
            if bodega_origen == bodega_destino:
                raise ValidationError({'bodega_destino': 'La bodega destino debe ser diferente a la bodega origen.'})

        elif tipo == 'merma':
            if not bodega_origen:
                raise ValidationError({'bodega_origen': 'La bodega origen es obligatoria para mermas.'})

        return attrs

    # ==================== HELPER METHODS ====================

    def _generar_numero_movimiento(self, tipo):
        prefijos = {
            'entrada': 'ENT', 'salida': 'SAL', 'transferencia': 'TRF',
            'ajuste': 'AJU', 'devolucion': 'DEV', 'merma': 'MER',
        }
        prefijo = prefijos.get(tipo, 'MOV')
        fecha   = self.get_fecha_empresa().strftime('%Y%m%d')

        ultimo = MovimientoInventario.objects.filter(
            numero__startswith=f"{prefijo}-{fecha}"
        ).order_by('-numero').first()

        nuevo_numero = int(ultimo.numero.split('-')[-1]) + 1 if ultimo else 1
        return f"{prefijo}-{fecha}-{nuevo_numero:04d}"

    def _generar_numero_lote(self, producto):
        prefijo = producto.codigo.split('-')[0][:4]
        fecha   = self.get_fecha_empresa().strftime('%Y%m%d')
        patron  = f'L-{prefijo}-{fecha}-'

        ultimo = DetalleMovimiento.objects.filter(
            producto=producto, lote__startswith=patron
        ).order_by('-lote').first()

        if ultimo:
            try:
                nuevo_num = int(ultimo.lote.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1

        return f'L-{prefijo}-{fecha}-{nuevo_num:03d}'

    def _generar_referencia_automatica(self, tipo):
        prefijos = {
            'entrada': 'ENT-REF', 'salida': 'SAL-REF', 'transferencia': 'TRF-REF',
            'ajuste': 'AJU-REF', 'devolucion': 'DEV-REF', 'merma': 'MER-REF',
        }
        prefijo = prefijos.get(tipo, 'MOV-REF')
        fecha   = self.get_fecha_empresa().strftime('%Y%m%d')

        ultimo = MovimientoInventario.objects.filter(
            tipo=tipo, referencia__startswith=f"{prefijo}-{fecha}"
        ).order_by('-referencia').first()

        if ultimo:
            try:
                nuevo_num = int(ultimo.referencia.split('-')[-1]) + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1

        return f"{prefijo}-{fecha}-{nuevo_num:03d}"

    def _validar_stock_disponible(self, bodega, producto, cantidad_requerida):
        try:
            inventario       = Stock.objects.get(bodega=bodega, producto=producto)
            stock_disponible = inventario.cantidad - inventario.stock_reservado

            if stock_disponible < cantidad_requerida:
                raise ValidationError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {stock_disponible}, Requerido: {cantidad_requerida}."
                )
            return inventario.cantidad

        except Stock.DoesNotExist:
            raise ValidationError(
                f"El producto {producto.nombre} no tiene inventario en esta bodega."
            )

    def _actualizar_inventario(self, bodega, producto, cantidad, es_suma=True):
        inventario, _ = Stock.objects.get_or_create(
            bodega=bodega, producto=producto, empresa=bodega.empresa,
            defaults={'cantidad': 0},
        )
        stock_anterior = inventario.cantidad

        if es_suma:
            inventario.cantidad += cantidad
        else:
            inventario.cantidad -= cantidad
        inventario.save()

        return stock_anterior, inventario.cantidad

    # ==================== CREATE ====================

    def create(self, validated_data):
        """
        Crea movimiento con actualización automática de stocks.
        Proceso: validar stock → crear movimiento → crear detalles → actualizar inventarios.
        """
        detalles_data  = validated_data.pop('detalles_data')
        bodega_origen  = validated_data.pop('bodega_origen', None)
        bodega_destino = validated_data.pop('bodega_destino', None)
        responsable    = validated_data.pop('responsable', None)
        tipo           = validated_data.get('tipo')

        with transaction.atomic():
            validated_data['numero']         = self._generar_numero_movimiento(tipo)
            validated_data['bodega_origen']  = bodega_origen
            validated_data['bodega_destino'] = bodega_destino
            validated_data['responsable']    = responsable

            movimiento = super().create(validated_data)

            for detalle_data in detalles_data:
                producto       = detalle_data.pop('producto')
                cantidad       = detalle_data.get('cantidad')
                costo_unitario = detalle_data.get('costo_unitario')

                stock_anterior  = None
                stock_posterior = None

                if tipo in ['salida', 'transferencia', 'merma'] and bodega_origen:
                    stock_anterior = self._validar_stock_disponible(bodega_origen, producto, cantidad)

                if tipo == 'entrada' and bodega_destino:
                    stock_anterior, stock_posterior = self._actualizar_inventario(
                        bodega_destino, producto, cantidad, es_suma=True
                    )
                elif tipo == 'salida' and bodega_origen:
                    stock_anterior, stock_posterior = self._actualizar_inventario(
                        bodega_origen, producto, cantidad, es_suma=False
                    )
                elif tipo == 'transferencia':
                    stock_anterior, _ = self._actualizar_inventario(
                        bodega_origen, producto, cantidad, es_suma=False
                    )
                    _, stock_posterior = self._actualizar_inventario(
                        bodega_destino, producto, cantidad, es_suma=True
                    )
                elif tipo == 'merma' and bodega_origen:
                    stock_anterior, stock_posterior = self._actualizar_inventario(
                        bodega_origen, producto, cantidad, es_suma=False
                    )

                DetalleMovimiento.objects.create(
                    empresa         = movimiento.empresa,
                    movimiento      = movimiento,
                    producto        = producto,
                    cantidad        = cantidad,
                    costo_unitario  = costo_unitario,
                    lote            = detalle_data.get('lote'),
                    fecha_vencimiento = detalle_data.get('fecha_vencimiento'),
                    observaciones   = detalle_data.get('observaciones', ''),
                    stock_anterior  = stock_anterior,
                    stock_posterior = stock_posterior,
                )

                if tipo == 'entrada' and costo_unitario:
                    producto.ultimo_costo = costo_unitario
                    producto.save(update_fields=['ultimo_costo'])

                    try:
                        producto.actualizar_costo_promedio()
                    except Exception as e:
                        self.logger.warning(
                            f"No se pudo actualizar costo promedio | Producto={producto.nombre} | Error={str(e)}"
                        )

        self.logger.info(
            f"Movimiento creado | Numero={movimiento.numero} | Tipo={tipo} | "
            f"Productos={len(detalles_data)} | Usuario={self.context['request'].user.id}"
        )

        return movimiento

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        raise ValidationError(
            "Los movimientos de inventario no se pueden modificar. "
            "Use la acción 'anular' si necesita revertir el movimiento."
        )

    # ==================== REPRESENTATION ====================

    def to_representation(self, instance):
        data     = super().to_representation(instance)
        detalles = instance.detalles.all()

        data['total_productos'] = detalles.count()
        data['cantidad_total']  = sum(d.cantidad for d in detalles)
        data['responsable']     = self.get_responsable_nombre(instance)

        if detalles.filter(costo_unitario__isnull=False).exists():
            data['costo_total'] = float(
                sum((d.costo_unitario or 0) * d.cantidad for d in detalles)
            )

        return data