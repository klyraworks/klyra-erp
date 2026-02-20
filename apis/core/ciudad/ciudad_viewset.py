# apis/base/ciudad_viewset.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from cities_light.models import SubRegion
from apis.core.ciudad.ciudad_serializer import CiudadSerializer

import logging


class CiudadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet READ-ONLY para ciudades (SubRegion de cities_light).

    Este ViewSet es de solo lectura ya que las ciudades vienen
    de la base de datos de GeoNames y no deben modificarse.

    Endpoints:
    - GET /api/ciudades/ - Listar todas las ciudades
    - GET /api/ciudades/?search=quito - Buscar ciudades
    - GET /api/ciudades/{id}/ - Ver detalle de una ciudad
    """
    queryset = SubRegion.objects.select_related('region', 'region__country').all()
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']  # Solo lectura

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('ciudad_viewset')

    def get_queryset(self):
        """Optimizar queryset"""
        queryset = super().get_queryset()

        # Por defecto, solo mostrar ciudades de Ecuador (optimización)
        # Si tu sistema es solo para Ecuador, esto reduce drásticamente la carga
        pais = self.request.query_params.get('pais', 'Ecuador')
        if pais:
            queryset = queryset.filter(region__country__name=pais)

        return queryset.order_by('name')

    def list(self, request, *args, **kwargs):
        """
        Listar ciudades con búsqueda opcional.

        Query params:
        - search: Buscar por nombre de ciudad
        - pais: Filtrar por país (default: Ecuador)
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Búsqueda por nombre
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(name__icontains=search)

            # Sin paginación para selects (performance)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            self.logger.error(f"Error listando ciudades: {str(e)}")
            return Response(
                {'error': 'Error al obtener ciudades'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Ver detalle de una ciudad"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except SubRegion.DoesNotExist:
            return Response(
                {'error': 'Ciudad no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo ciudad: {str(e)}")
            return Response(
                {'error': 'Error al obtener ciudad'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )