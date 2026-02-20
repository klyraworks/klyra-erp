# apis/inventario/ubicacion/ubicacion_serializer.py

from rest_framework import serializers
from apps.inventario.models import Ubicacion
from apis.core.SerializerBase import TenantSerializer


class UbicacionSerializer(TenantSerializer):
    """Serializer para Ubicaciones en bodegas"""

    bodega_nombre = serializers.CharField(source='bodega.nombre', read_only=True)
    bodega_codigo = serializers.CharField(source='bodega.codigo', read_only=True)
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Ubicacion
        fields = [
            'id',
            'bodega',
            'bodega_nombre',
            'bodega_codigo',
            'pasillo',
            'estante',
            'nivel',
            'descripcion',
            'nombre_completo',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_nombre_completo(self, obj):
        """Retorna formato: Pasillo-Estante-Nivel"""
        return f"{obj.pasillo}-{obj.estante}-{obj.nivel}"

    def validate(self, data):
        """Validar que no exista la misma ubicación en la bodega"""
        bodega = data.get('bodega')
        pasillo = data.get('pasillo')
        estante = data.get('estante')
        nivel = data.get('nivel')

        # En actualización, excluir la instancia actual
        ubicacion_id = self.instance.id if self.instance else None

        existe = Ubicacion.objects.filter(
            bodega=bodega,
            pasillo=pasillo,
            estante=estante,
            nivel=nivel
        ).exclude(id=ubicacion_id).exists()

        if existe:
            raise serializers.ValidationError(
                f"Ya existe una ubicación {pasillo}-{estante}-{nivel} en esta bodega"
            )

        return data


class UbicacionSimpleSerializer(TenantSerializer):
    """Serializer simplificado para selects y listados rápidos"""

    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Ubicacion
        fields = ['id', 'pasillo', 'estante', 'nivel', 'nombre', 'descripcion']

    def get_nombre(self, obj):
        return f"{obj.pasillo}-{obj.estante}-{obj.nivel}"