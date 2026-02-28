# apis/rrhh/puesto/puesto_viewset.py
import logging

from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.rrhh.models import Puesto
from apis.rrhh.puesto.puesto_serializer import (
    PuestoListSerializer,
    PuestoDetailSerializer,
    PuestoCreateSerializer,
    PuestoUpdateSerializer,
)
from django.db.models import Q

class PuestoViewSet(TenantViewSet):
    """
    ViewSet para gestión de puestos de trabajo.

    Endpoints:
        GET    /api/puestos/              - Listar
        POST   /api/puestos/              - Crear
        GET    /api/puestos/{id}/         - Detalle
        PUT    /api/puestos/{id}/         - Actualizar
        PATCH  /api/puestos/{id}/         - Actualizar parcial
        DELETE /api/puestos/{id}/         - Eliminar
        GET    /api/puestos/buscar/       - Búsqueda para selects

    Permisos:
        - ver_puesto:      GET (list, retrieve, buscar)
        - crear_puesto:    POST
        - editar_puesto:   PUT, PATCH
        - eliminar_puesto: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apps.rrhh')
    queryset         = Puesto.objects.all()
    serializer_class = PuestoDetailSerializer

    filterset_fields = ['departamento']
    search_fields    = ['codigo', 'nombre']
    ordering_fields  = ['codigo', 'nombre', 'salario_minimo', 'salario_maximo', 'created_at']
    ordering         = ['nombre']

    def get_serializer_class(self):
        if self.action == 'list':
            return PuestoListSerializer
        elif self.action in ('update', 'partial_update'):
            return PuestoUpdateSerializer
        elif self.action == 'create':
            return PuestoCreateSerializer
        return PuestoDetailSerializer

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'departamento',
            'created_by',
            'updated_by',
        )

        departamento_id = self.request.query_params.get('departamento_id')
        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_puesto')
    def list(self, request, *args, **kwargs):
        """Listar puestos."""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar puestos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener puestos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('crear_puesto')
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Puesto creado | ID={instancia.id} | Codigo={instancia.codigo} | "
                f"Usuario={request.user.id}"
            )

            instancia = self.get_queryset().get(id=instancia.id)

            return StandardResponse.success(
                data=PuestoDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Puesto creado exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear puesto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear puesto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('ver_puesto')
    def retrieve(self, request, *args, **kwargs):
        """Detalle de un puesto."""
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=PuestoDetailSerializer(instancia, context={'request': request}).data
            )

        except Exception as e:
            self.logger.error(f"Error al obtener puesto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener puesto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_puesto')
    def update(self, request, *args, **kwargs):
        """Actualizar puesto."""
        try:
            partial   = kwargs.pop('partial', False)
            instancia = self.get_object()

            serializer = PuestoUpdateSerializer(
                instancia, data=request.data,
                partial=partial, context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Puesto actualizado | ID={instancia.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=PuestoDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Puesto actualizado exitosamente",
            )

        except Exception as e:
            self.logger.error(f"Error al actualizar puesto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar puesto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_puesto')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_puesto')
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete de puesto.
        Validación: no se puede eliminar si tiene empleados activos asignados.
        """
        try:
            instancia = self.get_object()

            empleados_activos = instancia.empleado_set.filter(deleted_at__isnull=True, is_active=True).count()

            if empleados_activos > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar el puesto '{instancia.nombre}' "
                            f"porque tiene {empleados_activos} empleado(s) activo(s) asignado(s).",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_destroy(instancia)

            self.logger.info(
                f"Puesto eliminado | ID={instancia.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Puesto eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar puesto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar puesto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_puesto')
    def buscar(self, request):
        """
        Búsqueda para selects y autocompletes.
        GET /api/puestos/buscar/?q=texto&departamento_id=uuid
        """
        try:
            if request.query_params.get('id', '').strip():
                query = request.query_params.get('id').strip()
                filtro = Q(id=query)
                resultados = self.get_queryset().filter(filtro)[:1]
            else:
                query = request.query_params.get('q', '').strip()
                if not query:
                    return StandardResponse.success(data={'results': [], 'total': 0})
                filtro = Q(nombre__icontains=query) | Q(codigo__icontains=query)
                resultados = self.get_queryset().filter(filtro)[:20]

            serializer = PuestoListSerializer(resultados, many=True)
            return StandardResponse.success(data={
                'results': serializer.data,
                'total': len(serializer.data),
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de puestos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar puestos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )