# apis/personas/cliente_serializer.py

from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.personas.persona_serializer import PersonaCreateSerializer
from apis.core.SerializerBase import TenantSerializer
from apps.personas.models import Cliente
from apps.core.models import Persona


class ClienteListSerializer(TenantSerializer):
    nombre_facturacion = serializers.SerializerMethodField()

    class Meta:
        model  = Cliente
        fields = [
            'id', 'codigo', 'razon_social', 'tipo', 'tipo_identificacion',
            'identificacion', 'nombre_facturacion', 'is_active',
        ]

    def get_nombre_facturacion(self, obj):
        return obj.get_nombre_facturacion()


class ClienteDetailSerializer(TenantSerializer):
    nombre_facturacion = serializers.SerializerMethodField()
    credito_usado      = serializers.SerializerMethodField()
    persona_info       = serializers.SerializerMethodField()
    limite_credito     = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    credito_disponible = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    descuento_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False)

    class Meta:
        model  = Cliente
        fields = [
            'id', 'codigo', 'tipo', 'tipo_identificacion', 'identificacion',
            'razon_social', 'email_facturacion', 'telefono_facturacion', 'direccion',
            'limite_credito', 'credito_disponible', 'credito_usado', 'descuento_porcentaje',
            'nombre_facturacion', 'persona_info', 'is_active',
            'created_at', 'updated_at',
        ]

    def get_nombre_facturacion(self, obj):
        return obj.get_nombre_facturacion()

    def get_credito_usado(self, obj):
        return float(obj.limite_credito - obj.credito_disponible)

    def get_persona_info(self, obj):
        if obj.persona:
            return {
                'id':     str(obj.persona.id),
                'nombre': obj.persona.full_name(),
                'email':  obj.persona.email,
                'telefono': obj.persona.telefono,
            }
        return None


class ClienteCreateSerializer(serializers.Serializer):
    tipo                 = serializers.ChoiceField(choices=Cliente.TIPO_CHOICES)
    tipo_identificacion  = serializers.ChoiceField(choices=Cliente.TIPO_IDENTIFICACION_CHOICES)
    identificacion       = serializers.CharField(max_length=20)
    razon_social         = serializers.CharField(max_length=255)
    limite_credito       = serializers.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    descuento_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    email_facturacion    = serializers.EmailField(required=False, allow_blank=True, default='')
    telefono_facturacion = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    direccion            = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    persona_id           = serializers.UUIDField(required=False, allow_null=True, default=None)
    persona_data         = PersonaCreateSerializer(required=False, default=None)

    def validate_persona_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Persona.objects.filter(id=value, empresa=empresa).exists():
            raise ValidationError("La persona no existe o no pertenece a esta empresa.")
        # Verificar que esa persona no sea ya cliente en esta empresa
        if Cliente.objects.filter(persona_id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("Esta persona ya está registrada como cliente en la empresa.")
        return value

    def validate(self, attrs):
        empresa             = self.context['request'].empresa
        persona_id          = attrs.get('persona_id')
        persona_data        = attrs.get('persona_data')
        identificacion      = attrs.get('identificacion', '')
        tipo_identificacion = attrs.get('tipo_identificacion')
        tipo                = attrs.get('tipo')

        if not persona_id and not persona_data:
            raise ValidationError("Debe proveer persona_id o persona_data.")
        if persona_id and persona_data:
            raise ValidationError("No puede enviar persona_id y persona_data simultáneamente.")

        if Cliente.objects.filter(identificacion=identificacion, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError({"identificacion": "Ya existe un cliente con esta identificación."})

        if tipo_identificacion == 'ruc' and len(identificacion) != 13:
            raise ValidationError({"identificacion": "El RUC debe tener 13 dígitos."})
        if tipo_identificacion == 'cedula' and len(identificacion) != 10:
            raise ValidationError({"identificacion": "La cédula debe tener 10 dígitos."})
        if tipo == 'juridica' and tipo_identificacion != 'ruc':
            raise ValidationError({"tipo_identificacion": "Las personas jurídicas requieren RUC."})

        return attrs


class ClienteUpdateSerializer(TenantSerializer):
    persona_id           = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    limite_credito       = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    descuento_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model  = Cliente
        fields = [
            'tipo', 'tipo_identificacion', 'identificacion', 'razon_social',
            'limite_credito', 'descuento_porcentaje',
            'email_facturacion', 'telefono_facturacion', 'direccion',
            'persona_id',
        ]

    def validate(self, attrs):
        tipo_identificacion = attrs.get('tipo_identificacion', self.instance.tipo_identificacion)
        tipo                = attrs.get('tipo', self.instance.tipo)
        identificacion      = attrs.get('identificacion', self.instance.identificacion)
        empresa             = self.context['request'].empresa

        # Unicidad (excluir instancia actual)
        if 'identificacion' in attrs:
            qs = Cliente.objects.filter(
                identificacion=identificacion,
                empresa=empresa,
                deleted_at__isnull=True
            ).exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({"identificacion": "Ya existe un cliente con esta identificación."})

        if tipo_identificacion == 'ruc' and len(identificacion) != 13:
            raise ValidationError({"identificacion": "El RUC debe tener 13 dígitos."})
        if tipo_identificacion == 'cedula' and len(identificacion) != 10:
            raise ValidationError({"identificacion": "La cédula debe tener 10 dígitos."})
        if tipo == 'juridica' and tipo_identificacion != 'ruc':
            raise ValidationError({"tipo_identificacion": "Las personas jurídicas requieren RUC."})

        return attrs

    def update(self, instance, validated_data):
        persona_id = validated_data.pop('persona_id', ...)
        if persona_id is not ...:
            instance.persona_id = persona_id

        # Si cambia limite_credito, ajustar credito_disponible
        if 'limite_credito' in validated_data:
            diferencia = validated_data['limite_credito'] - instance.limite_credito
            instance.credito_disponible = max(
                Decimal('0.00'),
                instance.credito_disponible + diferencia
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class SaldoCreditoSerializer(serializers.Serializer):
    """Solo lectura — saldo de crédito."""
    limite_credito     = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    credito_disponible = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    credito_usado      = serializers.SerializerMethodField()
    porcentaje_usado   = serializers.SerializerMethodField()

    def get_credito_usado(self, obj):
        return float(obj.limite_credito - obj.credito_disponible)

    def get_porcentaje_usado(self, obj):
        if obj.limite_credito <= 0:
            return 0.0
        return round(float((obj.limite_credito - obj.credito_disponible) / obj.limite_credito * 100), 2)