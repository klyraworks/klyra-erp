# apis/inventario/categoria/categoria_serializer.py
from rest_framework import serializers
from apps.inventario.models import Categoria
from utils.validators import TextNormalizers
from apis.core.SerializerBase import TenantSerializer


class CategoriaListSerializer(TenantSerializer):
    """Serializer para listar categorías (vista simplificada)"""
    categoria_padre_nombre = serializers.CharField(source='categoria_padre.nombre', read_only=True)
    total_productos = serializers.IntegerField(read_only=True)  # Viene del annotate()

    class Meta:
        model = Categoria
        fields = [
            'id',
            'codigo',
            'nombre',
            'nivel',
            'categoria_padre',
            'categoria_padre_nombre',
            'imagen',
            'total_productos',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'codigo', 'nivel', 'total_productos', 'created_at']

    def to_representation(self, instance):
        """Enriquece la respuesta"""
        data = super().to_representation(instance)
        data['estado'] = 'Activa' if instance.is_active else 'Inactiva'
        data['es_padre'] = instance.categorias_hijas.filter(is_active=True).exists()
        return data


class CategoriaSerializer(TenantSerializer):
    """Serializer completo para crear/editar categorías"""
    categoria_padre_nombre = serializers.CharField(source='categoria_padre.nombre', read_only=True)
    total_productos = serializers.IntegerField(read_only=True)
    total_subcategorias = serializers.IntegerField(read_only=True)

    class Meta:
        model = Categoria
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'categoria_padre',
            'categoria_padre_nombre',
            'nivel',
            'imagen',
            'total_productos',
            'total_subcategorias',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        read_only_fields = [
            'id',
            'codigo',
            'nivel',
            'total_productos',
            'total_subcategorias',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        extra_kwargs = {
            'descripcion': {'required': False, 'allow_blank': True},
            'categoria_padre': {'required': False, 'allow_null': True},
            'imagen': {'required': False, 'allow_null': True},
        }

    def get_empresa_from_context(self):
        """Obtiene empresa del contexto del request"""
        request = self.context.get('request')
        if request and hasattr(request, 'empresa'):
            return request.empresa
        return None

    def validate_nombre(self, value):
        """Validar que el nombre no esté duplicado bajo el mismo padre"""
        empresa = self.get_empresa_from_context()
        if not empresa:
            raise serializers.ValidationError("No se pudo identificar la empresa")

        # Normalización de texto
        nombre_normalizado = TextNormalizers.normalize_text(value)

        # Obtener categoria_padre del contexto
        categoria_padre = self.initial_data.get('categoria_padre')

        # Validar unicidad del nombre bajo el mismo padre
        queryset = Categoria.objects.filter(
            empresa=empresa,
            nombre__iexact=nombre_normalizado,
            categoria_padre=categoria_padre,
            deleted_at__isnull=True
        )

        # Si es edición, excluir la instancia actual
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            if categoria_padre:
                padre = Categoria.objects.get(id=categoria_padre)
                raise serializers.ValidationError(
                    f"Ya existe una subcategoría '{nombre_normalizado}' bajo '{padre.nombre}'"
                )
            else:
                raise serializers.ValidationError(
                    f"Ya existe una categoría principal con el nombre '{nombre_normalizado}'"
                )

        return nombre_normalizado

    def validate_categoria_padre(self, value):
        """Validar que la categoría padre exista y no exceda nivel máximo"""
        if value:
            # Validar que existe y está activa
            if not Categoria.objects.filter(id=value.id, is_active=True, deleted_at__isnull=True).exists():
                raise serializers.ValidationError("La categoría padre no existe o está inactiva")

            # Validar nivel máximo (máximo 4 niveles de profundidad)
            if value.nivel >= 4:
                raise serializers.ValidationError(
                    f"No se pueden crear más de 4 niveles de categorías. "
                    f"La categoría padre está en el nivel {value.nivel}."
                )

        return value

    def validate(self, attrs):
        """Validaciones cruzadas"""
        # Si es edición, no permitir cambiar padre si tiene productos
        if self.instance and 'categoria_padre' in attrs:
            if attrs['categoria_padre'] != self.instance.categoria_padre:
                # Verificar si tiene productos
                if self.instance.productos.filter(is_active=True, deleted_at__isnull=True).exists():
                    raise serializers.ValidationError({
                        'categoria_padre': 'No se puede cambiar la categoría padre porque tiene productos asociados'
                    })

                # Verificar si tiene subcategorías
                if self.instance.categorias_hijas.filter(is_active=True, deleted_at__isnull=True).exists():
                    raise serializers.ValidationError({
                        'categoria_padre': 'No se puede cambiar la categoría padre porque tiene subcategorías'
                    })

        return attrs

    def to_representation(self, instance):
        """Enriquece la respuesta"""
        data = super().to_representation(instance)
        data['estado'] = 'Activa' if instance.is_active else 'Inactiva'
        data['es_padre'] = instance.categorias_hijas.filter(is_active=True).exists()
        data['ruta_completa'] = self._get_ruta_completa(instance)
        return data

    def _get_ruta_completa(self, categoria):
        """Retorna la ruta completa de la categoría (ej: Electrónica > Computadoras > Laptops)"""
        ruta = [categoria.nombre]
        padre = categoria.categoria_padre

        while padre:
            ruta.insert(0, padre.nombre)
            padre = padre.categoria_padre

        return ' > '.join(ruta)


class CategoriaSimpleSerializer(TenantSerializer):
    """Serializer mínimo para dropdowns/selects"""

    class Meta:
        model = Categoria
        fields = ['id', 'codigo', 'nombre', 'nivel']
        read_only_fields = ['id', 'codigo', 'nombre', 'nivel']


class CategoriaTreeSerializer(TenantSerializer):
    """Serializer para vista de árbol jerárquico"""
    subcategorias = serializers.SerializerMethodField()
    total_productos = serializers.IntegerField(read_only=True)

    class Meta:
        model = Categoria
        fields = [
            'id',
            'codigo',
            'nombre',
            'nivel',
            'total_productos',
            'subcategorias'
        ]

    def get_subcategorias(self, obj):
        """Retorna subcategorías recursivamente"""
        subcategorias = obj.categorias_hijas.filter(
            is_active=True,
            deleted_at__isnull=True
        ).order_by('nombre')

        return CategoriaTreeSerializer(subcategorias, many=True).data