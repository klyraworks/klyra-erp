# apis/rrhh/departamento/departamento_serializer.py
import logging

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apps.rrhh.models import Departamento
from apps.seguridad.models import Empleado


class DepartamentoListSerializer(TenantSerializer):
    """Campos mínimos para tablas y selects."""

    jefe_nombre = serializers.SerializerMethodField()
    total_empleados = serializers.SerializerMethodField()

    class Meta:
        model  = Departamento
        fields = ['id', 'codigo', 'nombre', 'jefe_nombre', 'total_empleados', 'is_active']

    def get_jefe_nombre(self, obj):
        if obj.jefe:
            return obj.jefe.persona.full_name()
        return None

    def get_total_empleados(self, obj):
        return obj.empleados.filter(deleted_at__isnull=True, is_active=True).count()


class DepartamentoDetailSerializer(TenantSerializer):
    """Campos completos con relaciones anidadas."""

    jefe    = serializers.SerializerMethodField()
    total_empleados = serializers.SerializerMethodField()

    class Meta:
        model  = Departamento
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'jefe', 'total_empleados',
            'is_active', 'created_at', 'updated_at',
        ]

    def get_jefe(self, obj):
        if obj.jefe:
            return {
                'id':     str(obj.jefe.id),
                'codigo': obj.jefe.codigo,
                'nombre': obj.jefe.persona.full_name(),
            }
        return None

    def get_total_empleados(self, obj):
        return obj.empleados.filter(deleted_at__isnull=True, is_active=True).count()


class DepartamentoCreateSerializer(TenantSerializer):
    """Campos para creación."""

    jefe_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Departamento
        fields = ['nombre', 'descripcion', 'jefe_id']

    def validate_jefe_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Empleado.objects.filter(
            id=value, empresa=empresa,
            deleted_at__isnull=True, is_active=True
        ).exists():
            raise ValidationError("El empleado no existe o no pertenece a esta empresa.")
        return value

    def validate(self, attrs):
        empresa = self.context['request'].empresa
        nombre  = attrs.get('nombre', '').strip()

        if Departamento.objects.filter(nombre=nombre, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError({"nombre": "Ya existe un departamento con este nombre."})

        return attrs

    def create(self, validated_data):
        jefe_id = validated_data.pop('jefe_id', None)
        if jefe_id:
            validated_data['jefe'] = Empleado.objects.get(id=jefe_id)
        return super().create(validated_data)


class DepartamentoUpdateSerializer(TenantSerializer):
    """Campos editables."""

    jefe_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Departamento
        fields = ['nombre', 'descripcion', 'jefe_id']

    def validate_jefe_id(self, value):
        if value is None:
            return value
        empresa = self.context['request'].empresa
        if not Empleado.objects.filter(
            id=value, empresa=empresa,
            deleted_at__isnull=True, is_active=True
        ).exists():
            raise ValidationError("El empleado no existe o no pertenece a esta empresa.")
        return value

    def validate(self, attrs):
        nombre = attrs.get('nombre')
        if nombre:
            empresa = self.context['request'].empresa
            qs = Departamento.objects.filter(
                nombre=nombre.strip(), empresa=empresa, deleted_at__isnull=True
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise ValidationError({"nombre": "Ya existe un departamento con este nombre."})
        return attrs

    def update(self, instance, validated_data):
        # Ellipsis distingue None (limpiar jefe) de campo no enviado
        jefe_id = validated_data.pop('jefe_id', ...)
        if jefe_id is not ...:
            instance.jefe_id = jefe_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance