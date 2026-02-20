# apis/inventario/unidad_medida/unidad_medida_viewset.py
import logging

from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apis.inventario.unidad_medida.unidad_medida_serializer import UnidadMedidaSerializer, UnidadMedidaSimpleSerializer
from apps.inventario.models import UnidadMedida
from utils.mixins.permissions import PermissionCheckMixin
from apis.core.ViewSetBase import TenantViewSet


class UnidadMedidaViewSet(PermissionCheckMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar Unidades de Medida.

    Permisos:
    - view_unidadmedida: Ver unidades (Todos)
    - add_unidadmedida: Crear unidades (Supervisor, Gerente)
    - change_unidadmedida: Editar unidades (Supervisor, Gerente)
    - delete_unidadmedida: Eliminar unidades (Supervisor, Gerente)
    """
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('unidad_medida_viewset')

    def get_queryset(self):
        """Filtra unidades activas"""
        queryset = super().get_queryset()

        incluir_inactivas = self.request.query_params.get('incluir_inactivas', 'false')
        if incluir_inactivas.lower() in ['true', '1', 'yes']:
            queryset = self.queryset.filter(is_active=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return UnidadMedidaSimpleSerializer
        return UnidadMedidaSerializer

    # ==================== CRUD ====================

    def list(self, request, *args, **kwargs):
        """Listar unidades. Permiso: view_unidadmedida"""
        try:
            self.verificar_permiso('view_unidadmedida')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por tipo
            tipo = request.query_params.get('tipo', None)
            if tipo:
                queryset = queryset.filter(tipo=tipo)

            # Búsqueda
            search = request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(codigo__icontains=search) |
                    Q(nombre__icontains=search) |
                    Q(abreviatura__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error listando unidades: {str(e)}")
            return Response({'error': 'Error al obtener unidades'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """Crear unidad. Permiso: add_unidadmedida"""
        try:
            self.verificar_permiso('add_unidadmedida')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            unidad = serializer.save()

            self.logger.info(f"Unidad creada: {unidad.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """Obtener unidad. Permiso: view_unidadmedida"""
        try:
            self.verificar_permiso('view_unidadmedida')
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """Actualizar unidad. Permiso: change_unidadmedida"""
        try:
            self.verificar_permiso('change_unidadmedida')

            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Eliminar unidad. Permiso: delete_unidadmedida"""
        try:
            self.verificar_permiso('delete_unidadmedida')

            instance = self.get_object()

            if instance.productos.filter(is_active=True).exists():
                return Response(
                    {'error': 'No se puede eliminar una unidad con productos activos'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance.is_active = False
            instance.save()

            return Response({'message': 'Unidad desactivada exitosamente'})

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """Activar unidad. Permiso: delete_unidadmedida"""
        try:
            self.verificar_permiso('delete_unidadmedida')

            unidad = self.get_object()
            unidad.is_active = True
            unidad.save()

            serializer = self.get_serializer(unidad)
            return Response({
                'message': 'Unidad activada exitosamente',
                'unidad': serializer.data
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='por-tipo')
    def por_tipo(self, request):
        """
        Agrupar unidades por tipo.
        GET /api/unidades-medida/por-tipo/
        Permiso: view_unidadmedida
        """
        try:
            self.verificar_permiso('view_unidadmedida')

            tipos = ['unidad', 'peso', 'volumen', 'longitud', 'area', 'tiempo']
            resultado = {}

            for tipo in tipos:
                unidades = self.get_queryset().filter(tipo=tipo)
                if unidades.exists():
                    serializer = UnidadMedidaSimpleSerializer(unidades, many=True)
                    resultado[tipo] = serializer.data

            return Response(resultado)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error agrupando por tipo: {str(e)}")
            return Response({'error': 'Error al agrupar unidades'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)