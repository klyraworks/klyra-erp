# apis/inventario/ubicacion/ubicacion_viewset.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Count

from apps.inventario.models import Ubicacion, Bodega
from apis.inventario.ubicacion.ubicacion_serializer import UbicacionSerializer, UbicacionSimpleSerializer
from utils.mixins.permissions import PermissionCheckMixin
from apis.core.ViewSetBase import TenantViewSet

import logging


class UbicacionViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet para gestionar Ubicaciones dentro de bodegas.

    Permisos:
    - view_ubicacion: Ver ubicaciones
    - add_ubicacion: Crear ubicaciones
    - change_ubicacion: Editar ubicaciones
    - delete_ubicacion: Eliminar ubicaciones
    """
    queryset = Ubicacion.objects.select_related('bodega').all()
    serializer_class = UbicacionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('ubicacion_viewset')

    # ==================== SERIALIZER ====================

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return UbicacionSimpleSerializer
        return UbicacionSerializer

    # ==================== QUERYSET ====================

    def get_queryset(self):
        """Filtrar ubicaciones según permisos"""
        queryset = super().get_queryset()

        # Si no puede ver todas las bodegas, filtrar por sus bodegas asignadas
        if not self.request.user.has_perm('inventario.view_stock_todas_bodegas'):
            bodegas_usuario = Bodega.objects.filter(
                responsable__usuario=self.request.user
            ).values_list('id', flat=True)

            queryset = queryset.filter(bodega_id__in=bodegas_usuario)

        return queryset

    # ==================== CRUD ====================

    def list(self, request, *args, **kwargs):
        """
        Listar ubicaciones con filtros.
        Permiso: view_ubicacion
        """
        try:
            self.verificar_permiso('view_ubicacion')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por bodega (MUY COMÚN)
            bodega_id = request.query_params.get('bodega_id')
            if bodega_id:
                queryset = queryset.filter(bodega_id=bodega_id)

            # Búsqueda
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(pasillo__icontains=search) |
                    Q(estante__icontains=search) |
                    Q(nivel__icontains=search) |
                    Q(descripcion__icontains=search)
                )

            queryset = queryset.order_by('bodega__nombre', 'pasillo', 'estante', 'nivel')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error listando ubicaciones: {str(e)}")
            return Response(
                {'error': 'Error al obtener ubicaciones'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crear nueva ubicación.
        Permiso: add_ubicacion
        """
        try:
            self.verificar_permiso('add_ubicacion')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            ubicacion = serializer.save()

            self.logger.info(
                f"Ubicación creada por {request.user.username}",
                extra={
                    'ubicacion_id': ubicacion.id,
                    'bodega': ubicacion.bodega.nombre,
                    'ubicacion': f"{ubicacion.pasillo}-{ubicacion.estante}-{ubicacion.nivel}",
                    'creado_por': request.user.username
                }
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error creando ubicación: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalle de una ubicación.
        Permiso: view_ubicacion
        """
        try:
            self.verificar_permiso('view_ubicacion')
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Ubicacion.DoesNotExist:
            return Response(
                {'error': 'Ubicación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, *args, **kwargs):
        """
        Actualizar ubicación.
        Permiso: change_ubicacion
        """
        try:
            self.verificar_permiso('change_ubicacion')

            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            ubicacion = serializer.save()

            self.logger.info(
                f"Ubicación actualizada por {request.user.username}",
                extra={
                    'ubicacion_id': ubicacion.id,
                    'actualizado_por': request.user.username
                }
            )

            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error actualizando ubicación: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar ubicación (soft delete).
        Permiso: delete_ubicacion
        """
        try:
            self.verificar_permiso('delete_ubicacion')

            instance = self.get_object()

            # Verificar si tiene productos asignados
            from apps.inventario.models import Stock
            productos_en_ubicacion = Stock.objects.filter(
                ubicacion=instance
            ).count()

            if productos_en_ubicacion > 0:
                return Response(
                    {
                        'error': f'No se puede eliminar esta ubicación porque tiene {productos_en_ubicacion} producto(s) asignado(s)',
                        'productos_count': productos_en_ubicacion
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            ubicacion_nombre = f"{instance.pasillo}-{instance.estante}-{instance.nivel}"
            instance.delete()

            self.logger.info(
                f"Ubicación eliminada por {request.user.username}",
                extra={
                    'ubicacion': ubicacion_nombre,
                    'bodega': instance.bodega.nombre,
                    'eliminado_por': request.user.username
                }
            )

            return Response(
                {'message': 'Ubicación eliminada exitosamente'},
                status=status.HTTP_200_OK
            )

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error eliminando ubicación: {str(e)}")
            return Response(
                {'error': 'Error al eliminar ubicación'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='por-bodega/(?P<bodega_id>[^/.]+)')
    def por_bodega(self, request, bodega_id=None):
        """
        Listar ubicaciones de una bodega específica.
        GET /api/ubicaciones/por-bodega/{bodega_id}/
        Permiso: view_ubicacion
        """
        try:
            self.verificar_permiso('view_ubicacion')

            try:
                bodega = Bodega.objects.get(id=bodega_id)
            except Bodega.DoesNotExist:
                return Response(
                    {'error': 'Bodega no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )

            ubicaciones = self.get_queryset().filter(bodega=bodega)
            serializer = UbicacionSimpleSerializer(ubicaciones, many=True)

            return Response({
                'bodega': {
                    'id': str(bodega.id),
                    'nombre': bodega.nombre,
                    'codigo': bodega.codigo
                },
                'total_ubicaciones': ubicaciones.count(),
                'ubicaciones': serializer.data
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error obteniendo ubicaciones por bodega: {str(e)}")
            return Response(
                {'error': 'Error al obtener ubicaciones'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )