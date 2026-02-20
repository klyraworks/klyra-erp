# apis/inventario/marca/marca_serializer.py
from rest_framework import serializers
from apps.inventario.models import Marca
from cities_light.models import Country
from utils.validators import TextNormalizers


class MarcaListSerializer(serializers.ModelSerializer):
    """Serializer para listar marcas (vista simplificada)"""
    pais_origen_nombre = serializers.CharField(source='pais_origen.name', read_only=True)
    total_productos = serializers.IntegerField(read_only=True)  # Viene del annotate() del viewset

    class Meta:
        model = Marca
        fields = [
            'id',
            'codigo',
            'nombre',
            'pais_origen',
            'pais_origen_nombre',
            'logo',
            'total_productos',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'codigo', 'total_productos', 'created_at']

    def to_representation(self, instance):
        """Enriquece la respuesta"""
        data = super().to_representation(instance)
        data['estado'] = 'Activa' if instance.is_active else 'Inactiva'
        return data


class MarcaSerializer(serializers.ModelSerializer):
    """Serializer completo para crear/editar marcas"""
    pais_origen_nombre = serializers.CharField(source='pais_origen.name', read_only=True)
    total_productos = serializers.IntegerField(read_only=True)  # Viene del annotate()

    class Meta:
        model = Marca
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'pais_origen',
            'pais_origen_nombre',
            'logo',
            'is_active',
            'total_productos',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        read_only_fields = [
            'id',
            'codigo',
            'total_productos',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        extra_kwargs = {
            'descripcion': {'required': False, 'allow_blank': True},
            'pais_origen': {'required': False, 'allow_null': True},
            'logo': {'required': False, 'allow_null': True},
        }

    def get_empresa_from_context(self):
        """Obtiene empresa del contexto del request"""
        request = self.context.get('request')
        if request and hasattr(request, 'empresa'):
            return request.empresa
        return None

    def validate_nombre(self, value):
        """Validar que el nombre no esté duplicado (normalizado)"""
        empresa = self.get_empresa_from_context()
        if not empresa:
            raise serializers.ValidationError("No se pudo identificar la empresa")

        # RESCATADO: Normalización de texto
        nombre_normalizado = TextNormalizers.normalize_text(value)

        queryset = Marca.objects.filter(
            empresa=empresa,
            nombre__iexact=nombre_normalizado,
            deleted_at__isnull=True
        )

        # Si es edición, excluir la instancia actual
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                f"Ya existe una marca con el nombre '{nombre_normalizado}'"
            )

        return nombre_normalizado

    def validate(self, attrs):
        """Validaciones cruzadas"""
        # Validar que el país exista si se proporciona
        pais_origen = attrs.get('pais_origen')
        if pais_origen:
            if not Country.objects.filter(id=pais_origen.id).exists():
                raise serializers.ValidationError({
                    'pais_origen': 'El país seleccionado no es válido'
                })

        return attrs

    def to_representation(self, instance):
        """Enriquece la respuesta"""
        data = super().to_representation(instance)
        # RESCATADO: Campo estado legible
        data['estado'] = 'Activa' if instance.is_active else 'Inactiva'
        return data


class MarcaSimpleSerializer(serializers.ModelSerializer):
    """Serializer mínimo para dropdowns/selects"""

    class Meta:
        model = Marca
        fields = ['id', 'codigo', 'nombre']
        read_only_fields = ['id', 'codigo', 'nombre']