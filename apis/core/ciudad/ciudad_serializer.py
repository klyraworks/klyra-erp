# apis/core/ciudad/ciudad_serializer.py

from rest_framework import serializers
from cities_light.models import SubRegion, Region, Country


class CiudadSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para ciudades - para selects"""

    region = serializers.CharField(source='region.name', read_only=True, allow_null=True)
    pais_nombre = serializers.CharField(source='region.country.name', read_only=True)
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = SubRegion
        fields = [
            'id',
            'name',
            'region',
            'pais_nombre',
            'nombre_completo'
        ]

    def get_nombre_completo(self, obj):
        """Retorna: Ciudad, Provincia, País"""
        partes = [obj.name]
        if obj.region:
            partes.append(obj.region.name)
            if obj.region.country:
                partes.append(obj.region.country.name)
        return ', '.join(partes)


class CiudadSerializer(serializers.ModelSerializer):
    """Serializer completo para ciudades"""

    region = serializers.SerializerMethodField()
    pais = serializers.SerializerMethodField()

    class Meta:
        model = SubRegion
        fields = [
            'id',
            'name',
            'display_name',
            'geoname_id',
            'region',
            'pais'
        ]

    def get_region(self, obj):
        """Información de la región/provincia"""
        if not obj.region:
            return None
        return {
            'id': obj.region.id,
            'name': obj.region.name,
            'geoname_id': obj.region.geoname_id
        }

    def get_pais(self, obj):
        """Información del país"""
        if not obj.region or not obj.region.country:
            return None
        return {
            'id': obj.region.country.id,
            'name': obj.region.country.name,
            'code2': obj.region.country.code2,
            'code3': obj.region.country.code3
        }


class RegionSerializer(serializers.ModelSerializer):
    """Serializer para regiones/provincias"""

    pais_nombre = serializers.CharField(source='country.name', read_only=True)
    total_ciudades = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = [
            'id',
            'name',
            'display_name',
            'geoname_id',
            'pais_nombre',
            'total_ciudades'
        ]

    def get_total_ciudades(self, obj):
        """Cuenta cuántas ciudades tiene esta región"""
        return obj.subregion_set.count()