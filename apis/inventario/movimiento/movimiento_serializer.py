# apis/inventario/movimiento/movimiento_serializer.py
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

from apis.inventario.producto.producto_serializer import ProductoSerializer
from django.contrib.auth.models import User

from utils.validators import BusinessValidators
import logging


class DetalleMovimientoSerializer(TenantSerializer):
    """
    Serializer para DetalleMovimiento.
    Representa cada línea de producto en un movimiento de inventario.
    """

    # READ-ONLY - Información enriquecida
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    unidad_medida = serializers.CharField(source='producto.unidad_medida.nombre', read_only=True)
    stock_anterior = serializers.IntegerField(read_only=True)
    stock_posterior = serializers.IntegerField(read_only=True)

    # WRITE - UUIDs para creación
    producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.filter(is_active=True),
        write_only=True
    )

    class Meta:
        model = DetalleMovimiento
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo',
            'cantidad', 'costo_unitario', 'lote', 'fecha_vencimiento',
            'unidad_medida', 'stock_anterior', 'stock_posterior', 'observaciones'
        ]
        read_only_fields = ['id', 'stock_anterior', 'stock_posterior']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('detalle_movimiento_serializer')

    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva"""
        return BusinessValidators.validate_positive_integer(value, "cantidad")

    def validate_costo_unitario(self, value):
        """Valida que el costo sea positivo si se proporciona"""
        if value is not None:
            return BusinessValidators.validate_positive_amount(value, "costo unitario")
        return value

    def validate_producto(self, value):
        """Valida que el producto exista y esté activo"""
        if not value.is_active:
            raise ValidationError(f"Producto {value.nombre} está inactivo")
        return value

    def validate(self, attrs):
        """Validaciones cruzadas"""
        producto = attrs.get('producto')
        fecha_vencimiento = attrs.get('fecha_vencimiento')

        # Si el producto es perecedero, validar fecha de vencimiento
        if producto and producto.es_perecedero and not fecha_vencimiento:
            raise ValidationError({
                'fecha_vencimiento': 'La fecha de vencimiento es obligatoria para productos perecederos'
            })

        return attrs


class MovimientoInventarioSerializer(TenantSerializer):
    """
    Serializer para MovimientoInventario.
    Maneja entradas, salidas, transferencias y ajustes de inventario.

    Funcionalidades:
    - Validación de stock disponible en salidas
    - Actualización automática de Stock
    - Tracking de stock antes/después
    - Generación automática de número de movimiento
    """

    # READ-ONLY - Información enriquecida
    detalles = DetalleMovimientoSerializer(many=True, read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.full_name', read_only=True)
    bodega_origen_nombre = serializers.CharField(source='bodega_origen.nombre', read_only=True)
    bodega_destino_nombre = serializers.CharField(source='bodega_destino.nombre', read_only=True)
    autorizado_por_nombre = serializers.CharField(source='autorizado_por.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    fecha_local = serializers.SerializerMethodField()

    # WRITE-ONLY - Para creación (UUID fields)
    from apps.seguridad.models import Empleado

    detalles_data = DetalleMovimientoSerializer(many=True, write_only=True)
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True
    )
    bodega_origen = serializers.PrimaryKeyRelatedField(
        queryset=Bodega.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True
    )
    bodega_destino = serializers.PrimaryKeyRelatedField(
        queryset=Bodega.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = MovimientoInventario
        fields = [
            'id', 'numero', 'fecha', 'tipo', 'tipo_display', 'fecha_local',
            'bodega_origen', 'bodega_origen_nombre',
            'bodega_destino', 'bodega_destino_nombre',
            'responsable', 'responsable_nombre', 'referencia', 'observaciones',
            'autorizado_por', 'autorizado_por_nombre',
            'detalles', 'detalles_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'numero', 'fecha', 'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('movimiento_inventario_serializer')

    # ==================== GETS ====================
    def get_fecha_local(self, obj):
        """Usa zona horaria del usuario si está disponible"""
        import pytz

        request = self.context.get('request')

        if request and hasattr(request.user, 'timezone'):
            # Si el usuario tiene zona horaria configurada
            user_tz = pytz.timezone(request.user.timezone)
        else:
            # Zona horaria por defecto (Ecuador)
            user_tz = pytz.timezone('America/Guayaquil')

        return obj.fecha.astimezone(user_tz).strftime('%Y-%m-%dT%H:%M:%S')

    # ==================== VALIDATIONS ====================

    def validate_tipo(self, value):
        """Valida el tipo de movimiento"""
        tipos_validos = ['entrada', 'salida', 'transferencia', 'ajuste', 'devolucion', 'merma']
        if value not in tipos_validos:
            raise ValidationError(f"Tipo debe ser uno de: {', '.join(tipos_validos)}")
        return value

    def validate_detalles_data(self, value):
        """Enriquece automáticamente los detalles con datos del producto"""
        from django.utils import timezone
        from datetime import timedelta

        if not value or len(value) == 0:
            raise ValidationError("Debe incluir al menos un producto en el movimiento")

        for detalle in value:
            producto = detalle.get('producto')

            if not producto:
                raise ValidationError("Cada detalle debe incluir un producto")

            # 1. AUTO-LLENAR COSTO UNITARIO
            if not detalle.get('costo_unitario'):
                # Prioridad: ultimo_costo > costo_promedio > precio_compra
                costo_auto = (
                        getattr(producto, 'ultimo_costo', None) or
                        getattr(producto, 'costo_promedio', None) or
                        producto.precio_compra
                )
                detalle['costo_unitario'] = costo_auto
                self.logger.info(
                    f"Costo auto-asignado para {producto.nombre}: {costo_auto}"
                )

            # 2. AUTO-GENERAR LOTE si no existe
            if not detalle.get('lote'):
                detalle['lote'] = self._generar_numero_lote(producto)
                self.logger.info(
                    f"Lote auto-generado para {producto.nombre}: {detalle['lote']}"
                )

            # 3. AUTO-CALCULAR FECHA VENCIMIENTO para perecederos
            if producto.es_perecedero:
                if not detalle.get('fecha_vencimiento'):
                    if producto.dias_vida_util:
                        detalle['fecha_vencimiento'] = (
                                timezone.now().date() +
                                timedelta(days=producto.dias_vida_util)
                        )
                        self.logger.info(
                            f"Fecha vencimiento auto-calculada para {producto.nombre}: "
                            f"{detalle['fecha_vencimiento']} "
                            f"(+{producto.dias_vida_util} días)"
                        )
                    else:
                        raise ValidationError({
                            'fecha_vencimiento':
                                f'El producto "{producto.nombre}" es perecedero pero no tiene '
                                'días de vida útil configurados. Debe proporcionar fecha_vencimiento '
                                'manualmente o configurar dias_vida_util en el producto.'
                        })

        return value

    def validate(self, attrs):
        """Validaciones cruzadas según el tipo de movimiento"""
        tipo = attrs.get('tipo')
        bodega_origen = attrs.get('bodega_origen')
        bodega_destino = attrs.get('bodega_destino')
        referencia = attrs.get('referencia', '').strip()

        if not referencia:
            attrs['referencia'] = self._generar_referencia_automatica(tipo)
            self.logger.info(f"Referencia auto-generada: {attrs['referencia']}")

        # ENTRADA: Requiere bodega destino
        if tipo == 'entrada':
            if not bodega_destino:
                raise ValidationError({
                    'bodega_destino': 'La bodega destino es obligatoria para entradas'
                })
            if bodega_origen:
                raise ValidationError({
                    'bodega_origen': 'Las entradas no deben tener bodega origen'
                })

        # SALIDA: Requiere bodega origen
        elif tipo == 'salida':
            if not bodega_origen:
                raise ValidationError({
                    'bodega_origen': 'La bodega origen es obligatoria para salidas'
                })
            if bodega_destino:
                raise ValidationError({
                    'bodega_destino': 'Las salidas no deben tener bodega destino'
                })

        # TRANSFERENCIA: Requiere ambas bodegas
        elif tipo == 'transferencia':
            if not bodega_origen or not bodega_destino:
                raise ValidationError({
                    'bodega_origen': 'Las transferencias requieren bodega origen',
                    'bodega_destino': 'Las transferencias requieren bodega destino'
                })
            if bodega_origen == bodega_destino:
                raise ValidationError({
                    'bodega_destino': 'La bodega destino debe ser diferente a la bodega origen'
                })

        # MERMA: Requiere bodega origen
        elif tipo == 'merma':
            if not bodega_origen:
                raise ValidationError({
                    'bodega_origen': 'La bodega origen es obligatoria para mermas'
                })

        return attrs

    # ==================== HELPER METHODS ====================

    def _generar_numero_movimiento(self, tipo):
        """Genera número único de movimiento usando timezone de la empresa"""

        prefijos = {
            'entrada': 'ENT',
            'salida': 'SAL',
            'transferencia': 'TRF',
            'ajuste': 'AJU',
            'devolucion': 'DEV',
            'merma': 'MER'
        }

        prefijo = prefijos.get(tipo, 'MOV')

        # Obtiene la fecha de la empresa
        fecha = self.get_fecha_empresa().strftime('%Y%m%d')

        # Buscar último número del día
        ultimo = MovimientoInventario.objects.filter(
            numero__startswith=f"{prefijo}-{fecha}"
        ).order_by('-numero').first()

        if ultimo:
            ultimo_numero = int(ultimo.numero.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1

        return f"{prefijo}-{fecha}-{nuevo_numero:04d}"

    def _generar_numero_lote(self, producto):
        """
        Genera lote automático similar al código de producto.
        Formato: L-PREFIJO-YYYYMM-001
        Ejemplo: L-CPCH-202412-001
        """
        # Usar el prefijo del producto (primeras letras del código)
        prefijo = producto.codigo.split('-')[0][:4]  # CPCH de CPCH-TRA-0001
        fecha = self.get_fecha_empresa().strftime('%Y%m%d')

        # Buscar último lote del mes para este producto
        patron = f'L-{prefijo}-{fecha}-'
        ultimo = DetalleMovimiento.objects.filter(
            producto=producto,
            lote__startswith=patron
        ).order_by('-lote').first()

        if ultimo:
            try:
                ultimo_num = int(ultimo.lote.split('-')[-1])
                nuevo_num = ultimo_num + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1

        return f'L-{prefijo}-{fecha}-{nuevo_num:03d}'

    def _validar_stock_disponible(self, bodega, producto, cantidad_requerida):
        """Valida que haya stock suficiente en la bodega"""
        try:
            inventario = Stock.objects.get(
                bodega=bodega,
                producto=producto
            )
            stock_disponible = inventario.cantidad - inventario.stock_reservado

            if stock_disponible < cantidad_requerida:
                raise ValidationError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {stock_disponible}, Requerido: {cantidad_requerida}"
                )

            return inventario.cantidad

        except Stock.DoesNotExist:
            raise ValidationError(
                f"El producto {producto.nombre} no tiene inventario en esta bodega"
            )

    def _actualizar_inventario(self, bodega, producto, cantidad, es_suma=True):
        """Actualiza el inventario en una bodega específica"""
        inventario, created = Stock.objects.get_or_create(
            bodega=bodega,
            producto=producto,
            empresa=bodega.empresa,
            defaults={'cantidad': 0}
        )

        stock_anterior = inventario.cantidad

        if es_suma:
            inventario.cantidad += cantidad
        else:
            inventario.cantidad -= cantidad

        inventario.save()

        # Actualizar stock global del producto
        if es_suma:
            producto.stock += cantidad
        else:
            producto.stock -= cantidad
        producto.save()

        return stock_anterior, inventario.cantidad

    def _generar_referencia_automatica(self, tipo):
        """
        Genera referencia automática si el usuario no proporciona una.
        Formato: TIPO-YYYYMMDD-001
        """

        prefijos = {
            'entrada': 'ENT-REF',
            'salida': 'SAL-REF',
            'transferencia': 'TRF-REF',
            'ajuste': 'AJU-REF',
            'devolucion': 'DEV-REF',
            'merma': 'MER-REF'
        }

        prefijo = prefijos.get(tipo, 'MOV-REF')
        fecha = self.get_fecha_empresa().strftime('%Y%m%d')

        # Buscar última referencia del día
        ultimo = MovimientoInventario.objects.filter(
            tipo=tipo,
            referencia__startswith=f"{prefijo}-{fecha}"
        ).order_by('-referencia').first()

        if ultimo:
            try:
                ultimo_num = int(ultimo.referencia.split('-')[-1])
                nuevo_num = ultimo_num + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1

        return f"{prefijo}-{fecha}-{nuevo_num:03d}"

    # ==================== CREATE ====================

    def create(self, validated_data):
        """
        Crea movimiento de inventario con actualización automática de stocks.
        Proceso:
        1. Validar stock disponible (si es salida/transferencia)
        2. Crear movimiento
        3. Crear detalles
        4. Actualizar inventarios
        5. Registrar stocks antes/después
        """
        detalles_data = validated_data.pop('detalles_data')
        bodega_origen = validated_data.pop('bodega_origen', None)
        bodega_destino = validated_data.pop('bodega_destino', None)
        responsable = validated_data.pop('responsable', None)
        tipo = validated_data.get('tipo')

        request = self.context.get('request')

        try:
            with transaction.atomic():
                # Generar número de movimiento
                numero = self._generar_numero_movimiento(tipo)

                # Preparar datos para creación
                validated_data['numero'] = numero
                validated_data['bodega_origen'] = bodega_origen
                validated_data['bodega_destino'] = bodega_destino
                validated_data['responsable'] = responsable

                # Usar super() para asignar empresa automáticamente
                movimiento = super().create(validated_data)

                # Procesar cada detalle
                for detalle_data in detalles_data:
                    producto = detalle_data.pop('producto')
                    cantidad = detalle_data.get('cantidad')
                    costo_unitario = detalle_data.get('costo_unitario')

                    stock_anterior = None
                    stock_posterior = None

                    # Validar stock para salidas/transferencias
                    if tipo in ['salida', 'transferencia', 'merma'] and bodega_origen:
                        stock_anterior = self._validar_stock_disponible(
                            bodega_origen, producto, cantidad
                        )

                    # Actualizar inventarios según tipo
                    if tipo == 'entrada' and bodega_destino:
                        stock_anterior, stock_posterior = self._actualizar_inventario(
                            bodega_destino, producto, cantidad, es_suma=True
                        )

                    elif tipo == 'salida' and bodega_origen:
                        stock_anterior, stock_posterior = self._actualizar_inventario(
                            bodega_origen, producto, cantidad, es_suma=False
                        )

                    elif tipo == 'transferencia':
                        stock_origen_antes, stock_origen_despues = self._actualizar_inventario(
                            bodega_origen, producto, cantidad, es_suma=False
                        )
                        stock_destino_antes, stock_destino_despues = self._actualizar_inventario(
                            bodega_destino, producto, cantidad, es_suma=True
                        )
                        stock_anterior = stock_origen_antes
                        stock_posterior = stock_origen_despues

                    elif tipo == 'merma' and bodega_origen:
                        stock_anterior, stock_posterior = self._actualizar_inventario(
                            bodega_origen, producto, cantidad, es_suma=False
                        )

                    # Crear detalle directamente (sin serializer anidado)
                    DetalleMovimiento.objects.create(
                        empresa=movimiento.empresa,
                        movimiento=movimiento,
                        producto=producto,
                        cantidad=detalle_data.get('cantidad'),
                        costo_unitario=detalle_data.get('costo_unitario'),
                        lote=detalle_data.get('lote'),
                        fecha_vencimiento=detalle_data.get('fecha_vencimiento'),
                        observaciones=detalle_data.get('observaciones', ''),
                        stock_anterior=stock_anterior,
                        stock_posterior=stock_posterior
                    )

                    if tipo == 'entrada' and costo_unitario:
                        producto.ultimo_costo = costo_unitario
                        producto.save(update_fields=['ultimo_costo'])

                        try:
                            producto.actualizar_costo_promedio()
                        except Exception as e:
                            self.logger.warning(f"No se pudo actualizar costo promedio para {producto.nombre}: {e}")

                self.logger.info(
                    f"Movimiento {tipo} creado: {movimiento.numero}",
                    extra={
                        'movimiento_id': str(movimiento.id),
                        'numero': movimiento.numero,
                        'tipo': tipo,
                        'cantidad_productos': len(detalles_data)
                    }
                )

                return movimiento

        except ValidationError as e:
            self.logger.warning(f"Validación fallida en movimiento: {str(e)}")
            raise
        except Exception as e:
            self.logger.exception(f"Error creando movimiento: {str(e)}")
            raise ValidationError(f"Error al crear movimiento: {str(e)}")

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        """
        Los movimientos NO se pueden editar una vez creados.
        Solo se pueden anular y crear uno nuevo.
        """
        raise ValidationError(
            "Los movimientos de inventario no se pueden modificar. "
            "Use la acción 'anular' si necesita revertir el movimiento."
        )

    # ==================== REPRESENTATION ====================

    def to_representation(self, instance):
        """Enriquece la respuesta con información adicional"""
        data = super().to_representation(instance)

        # Calcular totales
        detalles = instance.detalles.all()
        data['total_productos'] = detalles.count()
        data['cantidad_total'] = sum(d.cantidad for d in detalles)
        data['responsable'] = {'id': instance.responsable.id, 'nombre_completo': instance.responsable.persona.full_name()} if instance.responsable else None

        if detalles.filter(costo_unitario__isnull=False).exists():
            data['costo_total'] = float(sum(
                (d.costo_unitario or 0) * d.cantidad for d in detalles
            ))

        return data


"""
Ejemplo de JSON para crear un movimiento de entrada:
{
  "tipo": "entrada",
  "bodega_destino": "f97a62bb-fd41-4736-a11c-e3bce3b23fed",
  "referencia": "COMPRA-PROVEEDOR-001",
  "observaciones": "Entrada de productos de proveedor Dell",
  "responsable": "c012cb64-e9e4-4884-a364-78738fcdd61b",
  "detalles_data": [
    {
      "producto": "3be9b44e-3b24-4d8d-bd70-385718177371",
      "cantidad": 3,
      "observaciones": "Lote de compra"
    }
  ]
}

Ejemplo de JSON para crear un movimiento de salida:
{
  "tipo": "salida",
  "bodega_origen": "f97a62bb-fd41-4736-a11c-e3bce3b23fed",
  "referencia": "COMPRA-PROVEEDOR-001",
  "observaciones": "Entrada de productos de proveedor Dell",
  "responsable": "c012cb64-e9e4-4884-a364-78738fcdd61b",
  "detalles_data": [
    {
      "producto": "3be9b44e-3b24-4d8d-bd70-385718177371",
      "cantidad": 3,
      "observaciones": "Lote de compra"
    }
  ]
}

# http://127.0.0.1:8000/api/movimientos-inventario/crear-entrada/
{
    "bodega_destino": "1c6c87a3-0a3a-4878-a0e1-a08aee947205",
    "observaciones": "Ingreso de producto a Bodega Central",
    "detalles_data": [
        {
            "producto": "fd87d709-a089-4892-817a-06f4cab9c1a2",
            "cantidad": 20
        },
        {
            "producto": "78b6e874-1710-4e4b-9dca-2638a7cd857e",
            "cantidad": 20
        }
    ]
}
# RESPUESTA
{
    "message": "Entrada de inventario registrada exitosamente",
    "movimiento": {
        "id": "501ee8e5-dc23-4bcb-9378-49991157ad97",
        "numero": "ENT-20251221-0001",
        "fecha": "2025-12-21T04:48:35.173643Z",
        "tipo": "entrada",
        "tipo_display": "Entrada",
        "bodega_destino_nombre": "Bodega Central",
        "referencia": "ENT-REF-20251221-001",
        "observaciones": "Ingreso de producto a Bodega Central",
        "autorizado_por": null,
        "detalles": [
            {
                "id": "03ed6852-9c44-4e83-9f42-ad591892cc1e",
                "producto_nombre": "Pastillas de freno TVS Apache",
                "producto_codigo": "PFTA-SIS-0001",
                "cantidad": 20,
                "costo_unitario": "25.50",
                "lote": "L-PFTA-202512-001",
                "fecha_vencimiento": null,
                "unidad_medida": "Par",
                "stock_anterior": 0,
                "stock_posterior": 20,
                "observaciones": ""
            },
            {
                "id": "9ff1afba-50fe-49a1-a9c5-fd05c0e43a2d",
                "producto_nombre": "Kit de embrague Bajaj Pulsar",
                "producto_codigo": "KEBP-MOT-0001",
                "cantidad": 20,
                "costo_unitario": "85.00",
                "lote": "L-KEBP-202512-001",
                "fecha_vencimiento": null,
                "unidad_medida": "Set",
                "stock_anterior": 0,
                "stock_posterior": 20,
                "observaciones": ""
            }
        ],
        "created_at": "2025-12-21T04:48:35.173643Z",
        "updated_at": "2025-12-21T04:48:35.173643Z",
        "total_productos": 2,
        "cantidad_total": 40,
        "responsable": null,
        "costo_total": 2210.0
    }
}



"""