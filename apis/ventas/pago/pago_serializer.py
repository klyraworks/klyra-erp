# apis/ventas/venta/pago_serializer.py

from rest_framework import serializers
from decimal import Decimal
import logging

from apps.ventas.models import Venta, Pago
from utils.validators import BusinessValidators
from apis.core.SerializerBase import TenantSerializer


class PagoSerializer(TenantSerializer):
    """Serializer para Pagos de ventas"""

    venta = serializers.PrimaryKeyRelatedField(
        queryset=Venta.objects.filter(is_active=True),
        write_only=True
    )
    fecha_local = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = [
            'id', 'fecha', 'monto', 'metodo', 'referencia',
            'observaciones', 'venta', 'fecha_local'
        ]
        read_only_fields = ['id', 'fecha']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('pago_serializer')

    def get_fecha_local(self, obj):
        """Usa zona horaria del usuario si está disponible"""
        from django.utils import timezone
        import pytz

        request = self.context.get('request')

        if request and hasattr(request.user, 'timezone'):
            user_tz = pytz.timezone(request.user.timezone)
        else:
            user_tz = pytz.timezone('America/Guayaquil')

        return obj.fecha.astimezone(user_tz).strftime('%Y-%m-%dT%H:%M:%S')

    def validate_monto(self, value):
        """Valida que el monto sea positivo"""
        return BusinessValidators.validate_positive_amount(value, "monto")

    def validate(self, attrs):
        """Validaciones cruzadas"""
        venta = attrs.get('venta')
        monto = attrs.get('monto')

        # Validar que la venta no esté anulada
        if venta.estado == 'anulada':
            raise serializers.ValidationError({
                'venta': 'No se puede registrar pagos en ventas anuladas'
            })

        # Validar que el monto no exceda el saldo pendiente
        if monto > venta.saldo_pendiente:
            raise serializers.ValidationError({
                'monto': f'El monto (${monto}) excede el saldo pendiente (${venta.saldo_pendiente})'
            })

        return attrs

    def create(self, validated_data):
        """Crea pago y actualiza saldo de la venta"""
        venta = validated_data.get('venta')

        # CRÍTICO: Heredar empresa de la venta
        validated_data['empresa'] = venta.empresa

        # Crear pago
        pago = super().create(validated_data)

        self.logger.info(
            f"Pago registrado: {pago.referencia} - ${pago.monto}",
            extra={'pago_id': str(pago.id), 'venta_id': str(venta.id)}
        )

        return pago

    def to_representation(self, instance):
        """Representación personalizada del Pago"""
        representation = super().to_representation(instance)
        representation['venta'] = {
            'id': str(instance.venta.id),
            'numero': instance.venta.numero,
            'cliente': instance.venta.cliente.get_nombre_facturacion(),
            'total': str(instance.venta.total),
            'saldo_pendiente': str(instance.venta.saldo_pendiente),
            'estado': instance.venta.estado,
        }
        return representation