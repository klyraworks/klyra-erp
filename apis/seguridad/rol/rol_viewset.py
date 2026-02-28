# apis/seguridad/rol/rol_viewset.py
import logging

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.seguridad.models import Rol
from apis.seguridad.rol.rol_serializer import (
    RolListSerializer,
    RolDetailSerializer,
    RolCreateSerializer,
    RolUpdateSerializer,
    _sincronizar_permisos_empleados,
)


class RolViewSet(TenantViewSet):
    """
    ViewSet para gestión de roles.

    Endpoints:
        GET    /api/roles/                              - Listar
        POST   /api/roles/                              - Crear
        GET    /api/roles/{id}/                         - Detalle
        PUT    /api/roles/{id}/                         - Actualizar
        PATCH  /api/roles/{id}/                         - Actualizar parcial
        DELETE /api/roles/{id}/                         - Eliminar
        GET    /api/roles/buscar/                       - Búsqueda para selects
        GET    /api/roles/grupos-disponibles/           - Grupos Django del sistema
        POST   /api/roles/{id}/asignar-grupos/          - Reemplaza grupos del rol

    Permisos:
        - ver_rol:      GET (list, retrieve, buscar, grupos-disponibles)
        - crear_rol:    POST
        - editar_rol:   PUT, PATCH, asignar-grupos
        - eliminar_rol: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apps.seguridad')
    queryset         = Rol.objects.all()
    serializer_class = RolDetailSerializer

    search_fields   = ['codigo', 'nombre']
    ordering_fields = ['codigo', 'nombre', 'nivel_jerarquico', 'created_at']
    ordering        = ['-nivel_jerarquico', 'nombre']

    def get_serializer_class(self):
        if self.action == 'list':
            return RolListSerializer
        elif self.action in ('update', 'partial_update'):
            return RolUpdateSerializer
        elif self.action == 'create':
            return RolCreateSerializer
        return RolDetailSerializer

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'grupos_django__permissions',
            'empleados',
        )

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_rol')
    def list(self, request, *args, **kwargs):
        """Listar roles."""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar roles: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener roles",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('crear_rol')
    def create(self, request, *args, **kwargs):
        """Crear nuevo rol."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Rol creado | ID={instancia.id} | Codigo={instancia.codigo} | "
                f"Usuario={request.user.id}"
            )

            instancia = self.get_queryset().get(id=instancia.id)

            return StandardResponse.success(
                data=RolDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Rol creado exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear rol: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear rol",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('ver_rol')
    def retrieve(self, request, *args, **kwargs):
        """Detalle de un rol con grupos y permisos."""
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=RolDetailSerializer(instancia, context={'request': request}).data
            )

        except Exception as e:
            self.logger.error(f"Error al obtener rol: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener rol",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_rol')
    def update(self, request, *args, **kwargs):
        """
        Actualizar rol.
        Si se envía grupos_django_ids, sincroniza user_permissions
        en todos los empleados con este rol.
        """
        try:
            partial   = kwargs.pop('partial', False)
            instancia = self.get_object()

            serializer = RolUpdateSerializer(
                instancia, data=request.data,
                partial=partial, context={'request': request},
            )
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                instancia = serializer.save()

            self.logger.info(
                f"Rol actualizado | ID={instancia.id} | Usuario={request.user.id}"
            )

            instancia = self.get_queryset().get(id=instancia.id)

            return StandardResponse.success(
                data=RolDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Rol actualizado exitosamente",
            )

        except Exception as e:
            self.logger.error(f"Error al actualizar rol: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar rol",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('editar_rol')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_rol')
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete de rol.
        Validación: no se puede eliminar si tiene empleados activos asignados.
        """
        try:
            instancia = self.get_object()

            from apps.seguridad.models import Empleado
            empleados_activos = Empleado.objects.filter(
                rol=instancia,
                deleted_at__isnull=True, is_active=True
            ).count()

            if empleados_activos > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar el rol '{instancia.nombre}' "
                            f"porque tiene {empleados_activos} empleado(s) activo(s) asignado(s).",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_destroy(instancia)

            self.logger.info(
                f"Rol eliminado | ID={instancia.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Rol eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT,
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar rol: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar rol",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_rol')
    def buscar(self, request):
        """
        Búsqueda para selects y autocompletes.
        GET /api/roles/buscar/?q=texto
        """
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return StandardResponse.success(data={'results': [], 'total': 0})

            resultados = self.get_queryset().filter(
                Q(nombre__icontains=query) | Q(codigo__icontains=query)
            )[:20]

            serializer = RolListSerializer(resultados, many=True)
            return StandardResponse.success(data={
                'results': serializer.data,
                'total':   len(serializer.data),
            })

        except Exception as e:
            self.logger.error(f"Error en búsqueda de roles: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar roles",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], url_path='grupos-disponibles')
    @requiere_permiso('ver_rol')
    def grupos_disponibles(self, request):
        """
        Lista todos los grupos Django del sistema con sus permisos.
        Usado para construir el selector de grupos en el frontend.
        GET /api/roles/grupos-disponibles/?q=ventas
        """
        try:
            grupos = Group.objects.prefetch_related('permissions__content_type')

            query = request.query_params.get('q', '').strip()
            if query:
                grupos = grupos.filter(name__icontains=query)

            grupos = grupos.order_by('name')

            data = [
                {
                    'id':       grupo.id,
                    'nombre':   grupo.name,
                    'permisos': list(grupo.permissions.values('id', 'codename', 'name')),
                }
                for grupo in grupos
            ]

            return StandardResponse.success(data={
                'total':  len(data),
                'grupos': data,
            })

        except Exception as e:
            self.logger.error(f"Error al obtener grupos disponibles: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener grupos disponibles",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'], url_path='asignar-grupos')
    @requiere_permiso('editar_rol')
    def asignar_grupos(self, request, pk=None):
        """
        Reemplaza los grupos Django del rol y sincroniza user_permissions
        en todos los empleados activos con este rol.

        POST /api/roles/{id}/asignar-grupos/
        Body: { "grupos_ids": [1, 2, 3] }
        """
        try:
            instancia  = self.get_object()
            grupos_ids = request.data.get('grupos_ids', [])

            if not isinstance(grupos_ids, list):
                return StandardResponse.validation_error(
                    {'grupos_ids': ['Debe ser una lista de IDs.']}
                )

            grupos    = Group.objects.filter(id__in=grupos_ids)
            invalidos = set(grupos_ids) - set(grupos.values_list('id', flat=True))

            if invalidos:
                return StandardResponse.validation_error(
                    {'grupos_ids': [f'Los siguientes IDs no existen: {list(invalidos)}']}
                )

            with transaction.atomic():
                instancia.grupos_django.set(grupos)
                _sincronizar_permisos_empleados(instancia)

            self.logger.info(
                f"Grupos asignados | Rol={instancia.id} | "
                f"Grupos={grupos.count()} | Usuario={request.user.id}"
            )

            instancia = self.get_queryset().get(id=instancia.id)

            return StandardResponse.success(
                data=RolDetailSerializer(instancia, context={'request': request}).data,
                mensaje=f"Grupos actualizados. {grupos.count()} grupo(s) asignado(s).",
            )

        except Exception as e:
            self.logger.error(f"Error al asignar grupos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al asignar grupos al rol",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )