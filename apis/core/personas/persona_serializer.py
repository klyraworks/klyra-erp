# apis/core/personas/persona_serializer.py
from apis.core.SerializerBase import TenantSerializer
from apis.core.ciudad.ciudad_serializer import CiudadSerializer
from apps.core.models import Persona
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from utils.validators import (
    EcuadorianValidators,
    TextNormalizers,
    BusinessValidators,
    SerializerHelpers
)


# ==================== PERSONA ====================

class PersonaSerializer(TenantSerializer):
    """Serializer para creación/edición de Persona"""
    ciudad = CiudadSerializer(read_only=True)

    class Meta:
        model = Persona
        fields = [
            'id',
            'nombre1',
            'nombre2',
            'apellido1',
            'apellido2',
            'cedula',
            'pasaporte',
            'email',
            'telefono',
            'ciudad',
            'fecha_nacimiento',
        ]

    def validate_cedula(self, value):
        if value and len(value) != 10:
            raise ValidationError("La cédula debe tener 10 dígitos.")
        return value

    def validate_pasaporte(self, value):
        if value and len(value) < 5:
            raise ValidationError("El pasaporte debe tener al menos 5 caracteres.")
        return value

    def validate(self, attrs):
        cedula = attrs.get('cedula')
        pasaporte = attrs.get('pasaporte')
        if not cedula and not pasaporte:
            raise ValidationError("Debe proveer cédula o pasaporte.")
        return attrs

# ==================== PERSONA CREATE ====================

class PersonaCreateSerializer(serializers.Serializer):
    nombre1           = serializers.CharField(max_length=100)
    nombre2           = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    apellido1         = serializers.CharField(max_length=100)
    apellido2         = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    cedula            = serializers.CharField(max_length=10, required=False, allow_null=True, default=None)
    email             = serializers.EmailField(required=False, allow_null=True, default=None)
    telefono          = serializers.CharField(max_length=10, required=False, allow_null=True, default=None)
    ciudad_id         = serializers.IntegerField(required=False, allow_null=True, default=None)
    primera_direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    segunda_direccion = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    sexo              = serializers.ChoiceField(choices=[('M','Masculino'),('F','Femenino'),('O','Otro')], default='O')
    pasaporte         = serializers.CharField(max_length=9, required=False, allow_null=True, default=None)
    fecha_nacimiento  = serializers.DateField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        empresa = self.context['request'].empresa
        cedula  = attrs.get('cedula')

        if cedula and Persona.objects.filter(cedula=cedula, empresa=empresa).exists():
            raise ValidationError({"cedula": "Ya existe una persona con esta cédula en la empresa."})

        return attrs

# ==================== PERSONA UPDATE ====================

class PersonaUpdateSerializer(serializers.ModelSerializer):
    """Campos editables de Persona."""

    ciudad = CiudadSerializer(read_only=True)
    ciudad_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Persona
        fields = [
            'nombre1',
            'nombre2',
            'apellido1',
            'apellido2',
            'email',
            'telefono',
            'fecha_nacimiento',
            'ciudad',
            'ciudad_id',
        ]

    def get_ciudad(self, obj):
        if obj.ciudad:
            return {'id': str(obj.ciudad.id), 'name': obj.ciudad.nombre, 'display_name': obj.ciudad.display_name, 'geoname_id': obj.ciudad.geoname_id}
        return None