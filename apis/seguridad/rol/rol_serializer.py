# apis/seguridad/rol/rol_serializer.py
import logging

from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.core.SerializerBase import TenantSerializer
from apps.seguridad.models import Rol


class GrupoDjangoSerializer(serializers.ModelSerializer):
    """Serializer para Group de Django con sus permisos."""

    permisos = serializers.SerializerMethodField()

    class Meta:
        model  = Group
        fields = ['id', 'name', 'permisos']

    def get_permisos(self, obj):
        return list(obj.permissions.values('id', 'codename', 'name'))


class RolListSerializer(TenantSerializer):
    """Campos mínimos para tablas y selects."""

    total_empleados = serializers.SerializerMethodField()

    class Meta:
        model  = Rol
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'nivel_jerarquico', 'total_empleados',
        ]

    def get_total_empleados(self, obj):
        from apps.seguridad.models import Empleado
        return Empleado.objects.filter(rol=obj, deleted_at__isnull=True, is_active=True).count()


class RolDetailSerializer(TenantSerializer):
    """Campos completos incluyendo permisos técnicos y de negocio."""

    grupos_django   = GrupoDjangoSerializer(many=True, read_only=True)
    total_empleados = serializers.SerializerMethodField()

    class Meta:
        model  = Rol
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'nivel_jerarquico',
            # Permisos técnicos
            'grupos_django',
            # Permisos de negocio
            'monto_maximo_descuento',
            'monto_maximo_aprobacion',
            'limite_credito_clientes',
            'puede_aprobar_vacaciones',
            'puede_ver_salarios',
            'puede_modificar_precios',
            'puede_anular_documentos',
            # Meta
            'total_empleados',
            'is_active', 'created_at', 'updated_at',
        ]

    def get_total_empleados(self, obj):
        from apps.seguridad.models import Empleado
        return Empleado.objects.filter(rol=obj, deleted_at__isnull=True, is_active=True).count()


class RolCreateSerializer(TenantSerializer):
    """Campos para creación."""

    grupos_django_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        write_only=True,
    )

    class Meta:
        model  = Rol
        fields = [
            'nombre', 'descripcion', 'nivel_jerarquico',
            'grupos_django_ids',
            'monto_maximo_descuento', 'monto_maximo_aprobacion',
            'limite_credito_clientes', 'puede_aprobar_vacaciones',
            'puede_ver_salarios', 'puede_modificar_precios',
            'puede_anular_documentos',
        ]

    def validate_nombre(self, value):
        empresa = self.context['request'].empresa
        if Rol.objects.filter(nombre=value.strip(), empresa=empresa, deleted_at__isnull=True).exists():
            raise ValidationError("Ya existe un rol con este nombre.")
        return value

    def validate_grupos_django_ids(self, value):
        if not value:
            return value
        existentes = Group.objects.filter(id__in=value).values_list('id', flat=True)
        invalidos  = set(value) - set(existentes)
        if invalidos:
            raise ValidationError(f"Los siguientes IDs de grupos no existen: {list(invalidos)}")
        return value

    def create(self, validated_data):
        grupos_ids = validated_data.pop('grupos_django_ids', [])
        rol = super().create(validated_data)
        if grupos_ids:
            rol.grupos_django.set(Group.objects.filter(id__in=grupos_ids))
        return rol


class RolUpdateSerializer(TenantSerializer):
    """Campos editables."""

    grupos_django_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model  = Rol
        fields = [
            'nombre', 'descripcion', 'nivel_jerarquico',
            'grupos_django_ids',
            'monto_maximo_descuento', 'monto_maximo_aprobacion',
            'limite_credito_clientes', 'puede_aprobar_vacaciones',
            'puede_ver_salarios', 'puede_modificar_precios',
            'puede_anular_documentos',
        ]

    def validate_nombre(self, value):
        empresa = self.context['request'].empresa
        qs = Rol.objects.filter(nombre=value.strip(), empresa=empresa, deleted_at__isnull=True)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise ValidationError("Ya existe un rol con este nombre.")
        return value

    def validate_grupos_django_ids(self, value):
        if not value:
            return value
        existentes = Group.objects.filter(id__in=value).values_list('id', flat=True)
        invalidos  = set(value) - set(existentes)
        if invalidos:
            raise ValidationError(f"Los siguientes IDs de grupos no existen: {list(invalidos)}")
        return value

    def update(self, instance, validated_data):
        grupos_ids = validated_data.pop('grupos_django_ids', ...)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if grupos_ids is not ...:
            instance.grupos_django.set(
                Group.objects.filter(id__in=grupos_ids) if grupos_ids else []
            )
            _sincronizar_permisos_empleados(instance)

        return instance


def _sincronizar_permisos_empleados(rol):
    """
    Recolecta todos los Permission de los grupos del rol y los propaga
    a user_permissions de cada empleado activo. Efecto inmediato sin re-login.
    """
    logger   = logging.getLogger('apps.seguridad')
    permisos = Permission.objects.filter(group__in=rol.grupos_django.all()).distinct()

    from apps.seguridad.models import Empleado
    empleados = Empleado.objects.filter(
        rol=rol,
        deleted_at__isnull=True,
        is_active=True,
        usuario__isnull=False,
    ).select_related('usuario')

    for empleado in empleados:
        empleado.usuario.user_permissions.set(permisos)

    logger.info(
        f"Permisos sincronizados | Rol={rol.id} | "
        f"Empleados afectados={empleados.count()} | "
        f"Permisos={permisos.count()}"
    )