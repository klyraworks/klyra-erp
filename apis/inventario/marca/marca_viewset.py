# apis/inventario/marca/marca_viewset.py
import logging
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import Marca, Producto
from .marca_serializer import (
    MarcaSerializer,
    MarcaListSerializer,
    MarcaSimpleSerializer
)


class MarcaViewSet(TenantViewSet):
    """
    ViewSet para gestión de Marcas de productos

    Endpoints:
        GET    /api/inventario/marcas/              - Listar marcas
        POST   /api/inventario/marcas/              - Crear marca
        GET    /api/inventario/marcas/{id}/         - Detalle marca
        PUT    /api/inventario/marcas/{id}/         - Actualizar marca
        PATCH  /api/inventario/marcas/{id}/         - Actualizar parcial
        DELETE /api/inventario/marcas/{id}/         - Eliminar marca
        POST   /api/inventario/marcas/{id}/activar/ - Reactivar marca
        POST   /api/inventario/marcas/bulk_create/  - Crear múltiples marcas
        GET    /api/inventario/marcas/{id}/productos/ - Productos de la marca
        GET    /api/inventario/marcas/con-productos/ - Solo marcas con productos

    Permisos:
        - ver_marcas: GET (list, retrieve)
        - crear_marcas: POST
        - editar_marcas: PUT, PATCH
        - eliminar_marcas: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger = logging.getLogger('apps.inventario')
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return MarcaListSerializer
        elif self.action in ['con_productos', 'bulk_create']:
            return MarcaSimpleSerializer
        return MarcaSerializer

    filterset_fields = ['pais_origen', 'is_active']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering_fields = ['nombre', 'codigo', 'created_at']
    ordering = ['nombre']

    # ==================== QUERYSET OPTIMIZADO ====================
    def get_queryset(self):
        """Queryset con joins optimizados"""
        queryset = super().get_queryset().select_related(
            'pais_origen',
            'created_by',
            'updated_by'
        )

        # Anotar con conteo de productos
        queryset = queryset.annotate(
            total_productos=Count('productos', filter=Q(productos__deleted_at__isnull=True))
        )

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_marcas')
    def list(self, request, *args, **kwargs):
        """Listar marcas con filtros"""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Solo activas por defecto
            if request.query_params.get('incluir_inactivas') != 'true':
                queryset = queryset.filter(is_active=True)

            # Filtro por país
            pais_id = request.query_params.get('pais_id')
            if pais_id:
                queryset = queryset.filter(pais_origen_id=pais_id)

            # RESCATADO: Búsqueda adicional
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(codigo__icontains=search) |
                    Q(nombre__icontains=search) |
                    Q(descripcion__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar marcas: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener marcas",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_marcas')
    def create(self, request, *args, **kwargs):
        """Crear nueva marca"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            marca = serializer.save()

            self.logger.info(
                f"Marca creada | ID={marca.id} | "
                f"Codigo={marca.codigo} | Nombre={marca.nombre} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MarcaSerializer(marca).data,
                mensaje="Marca creada exitosamente",
                status_code=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            self.logger.warning(f"Validación fallida: {e.detail}")
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al crear marca: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_marcas')
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de marca"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return StandardResponse.success(data=serializer.data)
        except Exception as e:
            self.logger.error(f"Error al obtener marca: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_marcas')
    def update(self, request, *args, **kwargs):
        """Actualizar marca completa"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            marca = serializer.save()

            self.logger.info(
                f"Marca actualizada | ID={marca.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MarcaSerializer(marca).data,
                mensaje="Marca actualizada exitosamente"
            )

        except ValidationError as e:
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al actualizar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('eliminar_marcas')
    def destroy(self, request, *args, **kwargs):
        """Eliminar marca (soft delete)"""
        try:
            instance = self.get_object()

            # Validar que no tenga productos activos
            productos_activos = Producto.objects.filter(
                marca=instance,
                is_active=True,
                deleted_at__isnull=True
            ).count()

            if productos_activos > 0:
                return StandardResponse.error(
                    mensaje=f"No se puede eliminar la marca porque tiene {productos_activos} producto(s) asociado(s)",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Soft delete
            self.perform_destroy(instance)

            self.logger.info(
                f"Marca eliminada | ID={instance.id} | Codigo={instance.codigo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Marca eliminada exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            self.logger.error(f"Error al eliminar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_marcas')
    def activar(self, request, pk=None):
        """
        Reactivar marca desactivada

        Útil para recuperar marcas eliminadas por error
        """
        try:
            marca = self.get_object()

            if marca.is_active:
                return StandardResponse.info(
                    mensaje="La marca ya está activa",
                    data=MarcaSerializer(marca).data
                )

            marca.is_active = True
            marca.save(update_fields=['is_active', 'updated_at'])

            self.logger.info(
                f"Marca reactivada | ID={marca.id} | Codigo={marca.codigo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MarcaSerializer(marca).data,
                mensaje="Marca reactivada exitosamente"
            )

        except Exception as e:
            self.logger.error(f"Error al activar marca: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al activar marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @requiere_permiso('crear_marcas')
    def bulk_create(self, request):
        """Crear múltiples marcas en una sola operación"""
        try:
            # Validaciones iniciales
            if not isinstance(request.data, list):
                return StandardResponse.error(
                    mensaje="Se esperaba un array de marcas",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) == 0:
                return StandardResponse.error(
                    mensaje="El array no puede estar vacío",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) > 100:
                return StandardResponse.error(
                    mensaje="No se pueden crear más de 100 marcas a la vez",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            marcas_creadas = []
            errores = []

            # Procesar cada marca
            for idx, marca_data in enumerate(request.data):
                try:
                    serializer = MarcaSerializer(
                        data=marca_data,
                        context={'request': request}
                    )
                    serializer.is_valid(raise_exception=True)
                    marca = serializer.save()

                    marcas_creadas.append({
                        'id': str(marca.id),
                        'codigo': marca.codigo,
                        'nombre': marca.nombre
                    })

                except ValidationError as e:
                    errores.append({
                        'index': idx,
                        'nombre': marca_data.get('nombre', 'Sin nombre'),
                        'errores': e.detail
                    })
                except Exception as e:
                    self.logger.error(
                        f"Error crítico en bulk create | Index={idx} | Error={str(e)}",
                        exc_info=True
                    )
                    raise

            # Logging
            self.logger.info(
                f"Bulk create marcas | Creadas={len(marcas_creadas)} | "
                f"Errores={len(errores)} | Usuario={request.user.id}"
            )

            # SIMPLIFICADO: Delegar lógica al StandardResponse
            return StandardResponse.bulk_result(
                creados=marcas_creadas,
                errores=errores,
                recurso="marcas",
                recurso_genero="f"
            )

        except Exception as e:
            self.logger.error(f"Error en bulk create: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear marcas en lote",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_marcas')
    def productos(self, request, pk=None):
        """Ver productos de la marca"""
        try:
            marca = self.get_object()

            productos = Producto.objects.filter(
                marca=marca,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('categoria', 'unidad_medida').order_by('nombre')

            # Filtro por categoría
            categoria_id = request.query_params.get('categoria_id')
            if categoria_id:
                productos = productos.filter(categoria_id=categoria_id)

            items = []
            for producto in productos:
                items.append({
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'categoria': producto.categoria.nombre if producto.categoria else None,
                    'precio_venta': float(producto.precio_venta),
                    'stock_total': producto.stock_total,
                    'is_active': producto.is_active
                })

            return StandardResponse.success(data={
                'marca': {
                    'id': str(marca.id),
                    'codigo': marca.codigo,
                    'nombre': marca.nombre
                },
                'total_productos': len(items),
                'productos': items
            })

        except Exception as e:
            self.logger.error(f"Error al obtener productos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos de la marca",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_marcas')
    def con_productos(self, request):
        """Listar solo marcas que tienen productos asociados"""
        try:
            marcas = self.get_queryset().filter(
                is_active=True,
                total_productos__gt=0
            ).order_by('nombre')

            serializer = MarcaSimpleSerializer(marcas, many=True)

            return StandardResponse.success(data={
                'total': marcas.count(),
                'marcas': serializer.data
            })

        except Exception as e:
            self.logger.error(f"Error al listar marcas: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener marcas",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )