# apis/core/ciudad/ciudad_viewset.py
import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from apis.core.response_handler import StandardResponse
from cities_light.models import SubRegion
from apis.core.ciudad.ciudad_serializer import CiudadSerializer, CiudadSimpleSerializer
from rest_framework.decorators import action

class CiudadViewSet(ReadOnlyModelViewSet):
    """
    ViewSet READ-ONLY para ciudades (SubRegion de cities_light).
    No hereda TenantViewSet — los datos son globales, no por empresa.

    Endpoints:
        GET /api/ciudades/              - Listar (con ?search= y ?pais=)
        GET /api/ciudades/{id}/         - Detalle
        GET /api/ciudades/buscar/       - Búsqueda para selects (paginada a 20)
    """

    logger           = logging.getLogger('apps.base')
    queryset         = SubRegion.objects.select_related('region', 'region__country').all()
    serializer_class = CiudadSerializer
    permission_classes = [IsAuthenticated]
    http_method_names  = ['get']

    search_fields   = ['name']
    ordering_fields = ['name']
    ordering        = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        pais = self.request.query_params.get('pais', 'Ecuador')
        if pais:
            queryset = queryset.filter(region__country__name=pais)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def list(self, request, *args, **kwargs):
        """Listar ciudades. Query params: ?search=quito &pais=Ecuador"""
        try:
            queryset = self.get_queryset()

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar ciudades: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener ciudades",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, *args, **kwargs):
        """Detalle de una ciudad."""
        try:
            instancia  = self.get_object()
            serializer = self.get_serializer(instancia)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al obtener ciudad: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener ciudad",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """
        Búsqueda optimizada para selects — máximo 20 resultados.
        GET /api/ciudades/buscar/?q=quito&pais=Ecuador
        GET /api/ciudades/buscar/?id=123
        """
        try:
            id_param = request.query_params.get('id', '').strip()
            q_param = request.query_params.get('q', '').strip()

            if not id_param and not q_param:
                return StandardResponse.success(data={'results': [], 'total': 0})

            if id_param:
                try:
                    filtro = Q(id=int(id_param))
                except ValueError:
                    return StandardResponse.validation_error(
                        {'id': ['El parámetro id debe ser un número entero.']}
                    )
            else:
                filtro = (
                        Q(name__icontains=q_param) |
                        Q(display_name__icontains=q_param) |
                        Q(geoname_code__icontains=q_param)
                )

            resultados = self.get_queryset().filter(filtro)[:20]
            serializer = CiudadSimpleSerializer(resultados, many=True)

            return StandardResponse.success(data={
                'results': serializer.data,
                'total': len(serializer.data),
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de ciudades: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar ciudades",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )