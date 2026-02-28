# apis/seguridad/empleado/empleado_serializer.py
import logging

from apis.core.SerializerBase import TenantSerializer
from apis.core.ciudad.ciudad_serializer import CiudadSerializer
from apps.core.models import Persona
from apps.rrhh.models import Departamento, HistorialPuesto
from apps.seguridad.models import Empleado, Rol
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apis.core.personas.persona_serializer import PersonaSerializer, PersonaUpdateSerializer

logger = logging.getLogger('apps.seguridad')


# ==================== EMPLEADO — CREATE ====================

class EmpleadoCreateSerializer(serializers.Serializer):
    """
    Serializer para creación completa de empleado.

    Maneja la creación compuesta:
        Persona → User → Empleado → ActivationToken
    """

    # -- Persona anidada
    persona = PersonaSerializer()

    # -- Datos del empleado
    salario            = serializers.DecimalField(max_digits=10, decimal_places=2)
    fecha_contratacion = serializers.DateField()
    estado             = serializers.ChoiceField(choices=Empleado.ESTADO_CHOICES, default='activo')

    # -- Relaciones opcionales
    rol_id             = serializers.UUIDField(required=False, allow_null=True)
    departamento_id    = serializers.UUIDField(required=False, allow_null=True)
    puesto_id          = serializers.UUIDField(required=False, allow_null=True)

    # -- Control de acceso
    crear_acceso       = serializers.BooleanField(default=True, help_text="Si es True, crea usuario del sistema y envía email de activación.")

    def validate_salario(self, value):
        if value <= 0:
            raise ValidationError("El salario debe ser mayor a cero.")
        return value

    def validate_rol_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].tenant
        if not Rol.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("El rol no existe o no pertenece a esta empresa.")
        return value

    def validate_departamento_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].tenant
        if not Departamento.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("El departamento no existe o no pertenece a esta empresa.")
        return value

    def validate(self, attrs):
        empresa = self.context['request'].tenant
        persona_data = attrs.get('persona', {})
        cedula = persona_data.get('cedula')
        email = persona_data.get('email')

        # Cédula única en la empresa
        if cedula and Persona.objects.filter(cedula=cedula, empresa=empresa).exists():
            raise ValidationError({"persona": {"cedula": "Ya existe una persona con esta cédula en la empresa."}})

        # Email único para el User (si se va a crear acceso)
        if attrs.get('crear_acceso') and email:
            if User.objects.filter(email=email).exists():
                raise ValidationError({"persona": {"email": "Ya existe un usuario con este email en el sistema."}})

        return attrs


# ==================== EMPLEADO — LIST ====================

class EmpleadoListSerializer(TenantSerializer):
    """Vista compacta para listado"""

    nombre_completo = serializers.SerializerMethodField()
    cedula          = serializers.CharField(source='persona.cedula', read_only=True)
    email           = serializers.CharField(source='persona.email', read_only=True)
    rol_nombre      = serializers.CharField(source='rol.nombre', read_only=True)
    departamento_nombre = serializers.CharField(source='departamento.nombre', read_only=True)
    tiene_acceso    = serializers.SerializerMethodField()

    class Meta:
        model = Empleado
        fields = [
            'id',
            'codigo',
            'nombre_completo',
            'cedula',
            'email',
            'puesto',
            'estado',
            'rol_nombre',
            'departamento_nombre',
            'cuenta_activada',
            'fecha_contratacion',
            'tiene_acceso',
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name()

    def get_tiene_acceso(self, obj):
        return obj.usuario_id is not None


# ==================== EMPLEADO — DETAIL ====================

class EmpleadoDetailSerializer(TenantSerializer):
    """Vista completa para retrieve"""

    persona         = PersonaSerializer(read_only=True)
    rol             = serializers.SerializerMethodField()
    departamento    = serializers.SerializerMethodField()
    puesto          = serializers.SerializerMethodField()
    username        = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Empleado
        fields = [
            'id',
            'codigo',
            'persona',
            'username',
            'puesto',
            'salario',
            'fecha_contratacion',
            'fecha_terminacion',
            'estado',
            'rol',
            'departamento',
            'debe_cambiar_password',
            'cuenta_activada',
            'fecha_activacion',
            'created_at',
            'updated_at',
        ]

    def get_rol(self, obj):
        if obj.rol:
            return {'id': str(obj.rol.id), 'nombre': obj.rol.nombre, 'codigo': obj.rol.codigo, 'descripcion': obj.rol.descripcion}
        return None

    def get_departamento(self, obj):
        if obj.departamento:
            return {'id': str(obj.departamento.id), 'nombre': obj.departamento.nombre, 'codigo': obj.departamento.codigo, 'descripcion': obj.departamento.descripcion}
        return None

    def get_puesto(self, obj):
        if obj.puesto:
            return {'id': str(obj.puesto.id), 'nombre': obj.puesto.nombre, 'codigo': obj.puesto.codigo, 'descripcion': obj.puesto.descripcion}
        return None


# ==================== CAMBIAR ESTADO ====================

class CambiarEstadoSerializer(serializers.Serializer):
    """Serializer para cambio de estado del empleado"""

    estado        = serializers.ChoiceField(choices=Empleado.ESTADO_CHOICES)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate_estado(self, value):
        empleado = self.context.get('empleado')
        if empleado and empleado.estado == value:
            raise ValidationError(f"El empleado ya se encuentra en estado '{value}'.")
        return value


# ==================== ACTUALIZAR EMPLEADO ====================

class EmpleadoUpdateSerializer(TenantSerializer):

    persona         = PersonaUpdateSerializer(required=False)
    rol_id          = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    puesto_id       = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    departamento_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Empleado
        fields = [
            'persona',
            'salario',
            'fecha_contratacion',
            'fecha_terminacion',
            'estado',
            'rol_id',
            'puesto_id',
            'departamento_id',
        ]

    def validate_salario(self, value):
        if value is not None and value <= 0:
            raise ValidationError("El salario debe ser mayor a cero.")
        return value

    def validate_rol_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Rol.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("El rol no existe o no pertenece a esta empresa.")
        return value

    def validate_departamento_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Departamento.objects.filter(id=value, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("El departamento no existe o no pertenece a esta empresa.")
        return value

    def update(self, instance, validated_data):
        # Actualizar Persona si viene en el request
        persona_data = validated_data.pop('persona', None)
        if persona_data:
            for attr, value in persona_data.items():
                setattr(instance.persona, attr, value)
            instance.persona.save()

        # FKs con Ellipsis para distinguir None de no enviado
        rol_id          = validated_data.pop('rol_id', ...)
        departamento_id = validated_data.pop('departamento_id', ...)
        puesto_id       = validated_data.pop('puesto_id', ...)

        if rol_id is not ...:
            instance.rol_id = rol_id
        if departamento_id is not ...:
            instance.departamento_id = departamento_id
        if puesto_id is not ...:
            instance.puesto_id = puesto_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance