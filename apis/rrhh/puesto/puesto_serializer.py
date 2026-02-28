# apis/rrhh/puesto/puesto_serializer.py
import logging

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apps.rrhh.models import Puesto, Departamento


class PuestoListSerializer(TenantSerializer):
    """Campos mínimos para tablas y selects."""

    departamento_nombre = serializers.CharField(source='departamento.nombre', read_only=True)
    total_empleados     = serializers.SerializerMethodField()

    class Meta:
        model  = Puesto
        fields = ['id', 'codigo', 'nombre', 'departamento_nombre', 'total_empleados']

    def get_total_empleados(self, obj):
        return obj.empleados.filter(deleted_at__isnull=True, is_active=True).count()


class PuestoDetailSerializer(TenantSerializer):
    """Campos completos con relaciones anidadas."""

    departamento    = serializers.SerializerMethodField()
    total_empleados = serializers.SerializerMethodField()

    class Meta:
        model  = Puesto
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'departamento',
            'salario_minimo', 'salario_maximo',
            'total_empleados',
            'is_active', 'created_at', 'updated_at',
        ]

    def get_departamento(self, obj):
        if obj.departamento:
            return {
                'id':     str(obj.departamento.id),
                'codigo': obj.departamento.codigo,
                'nombre': obj.departamento.nombre,
            }
        return None

    def get_total_empleados(self, obj):
        return obj.empleados.filter(deleted_at__isnull=True, is_active=True).count()


class PuestoCreateSerializer(TenantSerializer):
    """Campos para creación."""

    departamento_id = serializers.UUIDField(write_only=True)

    class Meta:
        model  = Puesto
        fields = ['nombre', 'descripcion', 'departamento_id', 'salario_minimo', 'salario_maximo']

    def validate_departamento_id(self, value):
        empresa = self.context['request'].empresa
        if not Departamento.objects.filter(
            id=value, empresa=empresa, deleted_at__isnull=True
        ).exists():
            raise ValidationError("El departamento no existe o no pertenece a esta empresa.")
        return value

    def validate(self, attrs):
        empresa = self.context['request'].empresa
        nombre  = attrs.get('nombre', '').strip()

        if Puesto.objects.filter(nombre=nombre, empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError({"nombre": "Ya existe un puesto con este nombre."})

        salario_minimo = attrs.get('salario_minimo')
        salario_maximo = attrs.get('salario_maximo')
        if salario_minimo and salario_maximo and salario_maximo < salario_minimo:
            raise ValidationError({"salario_maximo": "El salario máximo debe ser mayor o igual al salario mínimo."})

        return attrs

    def create(self, validated_data):
        departamento_id = validated_data.pop('departamento_id')
        validated_data['departamento'] = Departamento.objects.get(id=departamento_id)
        return super().create(validated_data)


class PuestoUpdateSerializer(TenantSerializer):
    """Campos editables."""

    departamento_id = serializers.UUIDField(required=False, write_only=True)

    class Meta:
        model  = Puesto
        fields = ['nombre', 'descripcion', 'departamento_id', 'salario_minimo', 'salario_maximo']

    def validate_departamento_id(self, value):
        empresa = self.context['request'].empresa
        if not Departamento.objects.filter(
            id=value, empresa=empresa, deleted_at__isnull=True
        ).exists():
            raise ValidationError("El departamento no existe o no pertenece a esta empresa.")
        return value

    def validate(self, attrs):
        nombre = attrs.get('nombre')
        if nombre:
            empresa = self.context['request'].empresa
            qs = Puesto.objects.filter(
                nombre=nombre.strip(), empresa=empresa, deleted_at__isnull=True
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise ValidationError({"nombre": "Ya existe un puesto con este nombre."})

        salario_minimo = attrs.get('salario_minimo', getattr(self.instance, 'salario_minimo', None))
        salario_maximo = attrs.get('salario_maximo', getattr(self.instance, 'salario_maximo', None))
        if salario_minimo and salario_maximo and salario_maximo < salario_minimo:
            raise ValidationError({"salario_maximo": "El salario máximo debe ser mayor o igual al salario mínimo."})

        return attrs

    def update(self, instance, validated_data):
        departamento_id = validated_data.pop('departamento_id', ...)
        if departamento_id is not ...:
            instance.departamento = Departamento.objects.get(id=departamento_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance