# apis/rrhh/departamento/departamento_viewset.py
import logging

from django.db.models import Prefetch
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.rrhh.models import Departamento
from apis.rrhh.departamento.departamento_serializer import (
    DepartamentoListSerializer,
    DepartamentoDetailSerializer,
    DepartamentoCreateSerializer,
    DepartamentoUpdateSerializer,
)


class DepartamentoViewSet(TenantViewSet):
    """
    ViewSet para gestión de departamentos organizacionales.

    Endpoints:
        GET    /api/departamentos/              - Listar
        POST   /api/departamentos/              - Crear
        GET    /api/departamentos/{id}/         - Detalle
        PUT    /api/departamentos/{id}/         - Actualizar
        PATCH  /api/departamentos/{id}/         - Actualizar parcial
        DELETE /api/departamentos/{id}/         - Eliminar
        GET    /api/departamentos/buscar/       - Búsqueda para selects

    Permisos:
        - ver_departamento:      GET (list, retrieve, buscar)
        - crear_departamento:    POST
        - editar_departamento:   PUT, PATCH
        - eliminar_departamento: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apps.rrhh')
    queryset         = Departamento.objects.all()
    serializer_class = DepartamentoDetailSerializer

    filterset_fields = ['jefe']
    search_fields    = ['codigo', 'nombre']
    ordering_fields  = ['codigo', 'nombre', 'created_at']
    ordering         = ['nombre']

    def get_serializer_class(self):
        if self.action == 'list':
            return DepartamentoListSerializer
        elif self.action in ('update', 'partial_update'):
            return DepartamentoUpdateSerializer
        elif self.action == 'create':
            return DepartamentoCreateSerializer
        return DepartamentoDetailSerializer

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        return super().get_queryset().select_related(
            'jefe__persona',
            'created_by',
            'updated_by',
        )

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_departamento')
    def list(self, request, *args, **kwargs):
        """Listar departamentos."""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar departamentos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener departamentos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('crear_departamento')
    def create(self, request, *args, **kwargs):
        """Crear nuevo departamento."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Departamento creado | ID={instancia.id} | Codigo={instancia.codigo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=DepartamentoDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Departamento creado exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear departamento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear departamento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('ver_departamento')
    def retrieve(self, request, *args, **kwargs):
        """Detalle de un departamento."""
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=DepartamentoDetailSerializer(instancia, context={'request': request}).data
            )

        except Exception as e:
            self.logger.error(f"Error al obtener departamento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener departamento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_departamento')
    def update(self, request, *args, **kwargs):
        """Actualizar departamento."""
        try:
            partial   = kwargs.pop('partial', False)
            instancia = self.get_object()

            serializer = DepartamentoUpdateSerializer(
                instancia, data=request.data,
                partial=partial, context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Departamento actualizado | ID={instancia.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=DepartamentoDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Departamento actualizado exitosamente",
            )

        except Exception as e:
            self.logger.error(f"Error al actualizar departamento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar departamento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_departamento')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_departamento')
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete de departamento.
        Validación: no se puede eliminar si tiene empleados activos asignados.
        """
        try:
            instancia = self.get_object()

            empleados_activos = instancia.empleados.filter(
                deleted_at__isnull=True, is_active=True
            ).count()

            if empleados_activos > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar el departamento '{instancia.nombre}' "
                            f"porque tiene {empleados_activos} empleado(s) activo(s) asignado(s).",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_destroy(instancia)

            self.logger.info(
                f"Departamento eliminado | ID={instancia.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Departamento eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar departamento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar departamento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_departamento')
    def buscar(self, request):
        """
        Búsqueda para selects y autocompletes.
        GET /api/departamentos/buscar/?q=texto
        """
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return StandardResponse.success(data={'results': [], 'total': 0})

            resultados = self.get_queryset().filter(
                nombre__icontains=query
            )[:20]

            serializer = DepartamentoListSerializer(resultados, many=True)
            return StandardResponse.success(data={
                'results': serializer.data,
                'total': len(serializer.data),
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de departamentos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar departamentos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )