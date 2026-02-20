# apis/inventario/bodega/bodega_viewset.py
import logging
from django.db import transaction
from django.db.models import Count, Sum, F, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ErrorDetail, ValidationError

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import Bodega, Stock, Producto
from .bodega_serializer import (
    BodegaSerializer,
    BodegaListSerializer,
    BodegaSimpleSerializer
)

class BodegaViewSet(TenantViewSet):
    """
    ViewSet para gestión de Bodegas/Almacenes

    Endpoints:
        GET    /api/inventario/bodegas/              - Listar bodegas
        POST   /api/inventario/bodegas/              - Crear bodega
        GET    /api/inventario/bodegas/{id}/         - Detalle bodega
        PUT    /api/inventario/bodegas/{id}/         - Actualizar bodega
        PATCH  /api/inventario/bodegas/{id}/         - Actualizar parcial
        DELETE /api/inventario/bodegas/{id}/         - Desactivar bodega
        GET    /api/inventario/bodegas/{id}/inventario/ - Ver inventario
        GET    /api/inventario/bodegas/resumen/      - Resumen todas bodegas

    Permisos:
        - ver_bodegas: GET (list, retrieve)
        - crear_bodegas: POST
        - editar_bodegas: PUT, PATCH
        - eliminar_bodegas: DELETE
    """

    # ==================== CONFIGURACIÓN ====================
    logger = logging.getLogger('apps.inventario')
    serializer_class = BodegaSerializer
    queryset = Bodega.objects.all()

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return BodegaListSerializer
        elif self.action in ['inventario', 'resumen']:
            return BodegaSimpleSerializer
        return BodegaSerializer

    filterset_fields = ['es_principal', 'permite_ventas', 'is_active']
    search_fields = ['codigo', 'nombre', 'ciudad__name']
    ordering_fields = ['codigo', 'nombre', 'created_at']
    ordering = ['codigo']

    # ==================== QUERYSET OPTIMIZADO ====================
    def get_queryset(self):
        """Queryset con joins optimizados"""
        return super().get_queryset().select_related(
            'responsable',
            'responsable__persona',
            'ciudad',
            'ciudad__region',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'stocks'
        )

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_bodegas')
    def list(self, request, *args, **kwargs):
        """Listar bodegas con filtros"""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Filtro adicional por ciudad
            ciudad_id = request.query_params.get('ciudad_id')
            if ciudad_id:
                queryset = queryset.filter(ciudad_id=ciudad_id)

            # Solo activas por defecto
            if request.query_params.get('incluir_inactivas') != 'true':
                queryset = queryset.filter(is_active=True)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar bodegas: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener bodegas",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_bodegas')
    def create(self, request, *args, **kwargs):
        """
        Crear nueva bodega

        IMPORTANTE: Crea automáticamente registros de Stock
        para TODOS los productos existentes con cantidad=0
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                # 1. Crear bodega
                bodega = serializer.save()

                # 2. Inicializar stock para todos los productos existentes
                productos_creados = self._inicializar_stock_productos(bodega)

                self.logger.info(
                    f"Bodega creada | ID={bodega.id} | "
                    f"Codigo={bodega.codigo} | Productos inicializados={productos_creados} | "
                    f"Usuario={request.user.id}"
                )

            return StandardResponse.success(
                data=BodegaSerializer(bodega).data,
                mensaje=f"Bodega creada exitosamente. {productos_creados} productos inicializados.",
                status_code=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            self.logger.warning(f"Validación fallida: {e.detail}")
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al crear bodega: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear bodega",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_bodegas')
    def update(self, request, *args, **kwargs):
        """Actualizar bodega completa"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            bodega = serializer.save()

            self.logger.info(
                f"Bodega actualizada | ID={bodega.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=BodegaSerializer(bodega).data,
                mensaje="Bodega actualizada exitosamente"
            )

        except ValidationError as e:
            return StandardResponse.validation_error(e.detail)
        except Exception as e:
            self.logger.error(f"Error al actualizar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar bodega",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('eliminar_bodegas')
    def destroy(self, request, *args, **kwargs):
        """Desactivar bodega (soft delete)"""
        try:
            instance = self.get_object()

            # Validar que no tenga stock
            if instance.stocks.filter(cantidad__gt=0).exists():
                return StandardResponse.error(
                    mensaje="No se puede desactivar una bodega con inventario",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validar que no sea bodega principal
            if instance.es_principal:
                return StandardResponse.error(
                    mensaje="No se puede desactivar la bodega principal",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Soft delete
            self.perform_destroy(instance)

            self.logger.info(
                f"Bodega desactivada | ID={instance.id} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                mensaje="Bodega desactivada exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            self.logger.error(f"Error al desactivar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al desactivar bodega",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_bodegas')
    def inventario(self, request, pk=None):
        """Ver inventario completo de la bodega"""
        try:
            bodega = self.get_object()

            stocks = Stock.objects.filter(
                bodega=bodega
            ).select_related(
                'producto',
                'producto__categoria',
                'producto__marca'
            ).order_by('producto__nombre')

            # Filtro opcional: solo productos con stock
            solo_con_stock = request.query_params.get('solo_con_stock', 'false')
            if solo_con_stock.lower() == 'true':
                stocks = stocks.filter(cantidad__gt=0)

            # Filtro por categoría
            categoria_id = request.query_params.get('categoria_id')
            if categoria_id:
                stocks = stocks.filter(producto__categoria_id=categoria_id)

            items = []
            valor_total = 0

            for stock in stocks:
                valor_item = stock.costo_promedio_bodega * stock.cantidad
                valor_total += valor_item

                items.append({
                    'producto_id': stock.producto.id,
                    'producto_codigo': stock.producto.codigo,
                    'producto_nombre': stock.producto.nombre,
                    'categoria': stock.producto.categoria.nombre if stock.producto.categoria else None,
                    'marca': stock.producto.marca.nombre if stock.producto.marca else None,
                    'cantidad': stock.cantidad,
                    'stock_reservado': stock.stock_reservado,
                    'disponible': stock.cantidad_disponible,
                    'costo_promedio': float(stock.costo_promedio_bodega),
                    'precio_venta': float(stock.precio_venta_efectivo),
                    'valor_inventario': float(valor_item),
                    'ubicacion': stock.ubicacion.nombre if stock.ubicacion else None
                })

            return StandardResponse.success(data={
                'bodega': {
                    'id': bodega.id,
                    'codigo': bodega.codigo,
                    'nombre': bodega.nombre
                },
                'resumen': {
                    'total_productos': len(items),
                    'productos_con_stock': len([i for i in items if i['cantidad'] > 0]),
                    'valor_total_inventario': float(valor_total)
                },
                'inventario': items
            })

        except Exception as e:
            self.logger.error(f"Error al obtener inventario: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener inventario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_bodegas')
    def resumen(self, request):
        """Resumen de todas las bodegas activas"""
        try:
            bodegas = self.get_queryset().filter(is_active=True).annotate(
                total_productos=Count('stocks'),
                total_unidades=Sum('stocks__cantidad'),
                valor_total=Sum(F('stocks__cantidad') * F('stocks__costo_promedio_bodega'))
            )

            data = []
            for bodega in bodegas:
                data.append({
                    'id': bodega.id,
                    'codigo': bodega.codigo,
                    'nombre': bodega.nombre,
                    'ciudad': bodega.ciudad.name if bodega.ciudad else None,
                    'es_principal': bodega.es_principal,
                    'permite_ventas': bodega.permite_ventas,
                    'total_productos': bodega.total_productos,
                    'total_unidades': bodega.total_unidades or 0,
                    'valor_inventario': float(bodega.valor_total or 0),
                    'responsable': bodega.responsable.persona.full_name if bodega.responsable else None
                })

            return StandardResponse.success(data={
                'total_bodegas': len(data),
                'bodegas': data
            })

        except Exception as e:
            self.logger.error(f"Error en resumen: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al generar resumen",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # apis/inventario/bodega/bodega_viewset.py

    @action(detail=False, methods=['post'])
    @requiere_permiso('crear_bodegas')
    def bulk_create(self, request):
        """
        Crear múltiples bodegas en una sola operación

        Body: Array de objetos bodega
        [
            {"nombre": "...", "direccion": "...", ...},
            {"nombre": "...", "direccion": "...", ...}
        ]
        """
        try:
            if not isinstance(request.data, list):
                return StandardResponse.error(
                    mensaje="Se esperaba un array de bodegas",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) == 0:
                return StandardResponse.error(
                    mensaje="El array no puede estar vacío",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if len(request.data) > 100:
                return StandardResponse.error(
                    mensaje="No se pueden crear más de 100 bodegas a la vez",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            bodegas_creadas = []
            errores = []

            for idx, bodega_data in enumerate(request.data):
                try:
                    serializer = self.get_serializer(data=bodega_data)
                    serializer.is_valid(raise_exception=True)

                    with transaction.atomic():
                        bodega = serializer.save()
                        productos_creados = self._inicializar_stock_productos(bodega)

                    bodegas_creadas.append({
                        'id': str(bodega.id),
                        'codigo': bodega.codigo,
                        'nombre': bodega.nombre,
                        'productos_inicializados': productos_creados
                    })

                except ValidationError as e:
                    # Extraer errores limpios
                    errores.append({
                        'index': idx,
                        'nombre': bodega_data.get('nombre', 'Sin nombre'),
                        'errores': e.detail  # ← Ya viene como dict, no como string
                    })
                except Exception as e:
                    # Errores críticos → detener
                    self.logger.error(
                        f"Error crítico en bulk create | Index={idx} | Error={str(e)}",
                        exc_info=True
                    )
                    raise

            self.logger.info(
                f"Bulk create bodegas | Creadas={len(bodegas_creadas)} | "
                f"Errores={len(errores)} | Usuario={request.user.id}"
            )

            # Usar StandardResponse.bulk_result()
            return StandardResponse.bulk_result(
                creados=bodegas_creadas,
                errores=errores,
                recurso="bodega",
                recurso_genero="f"
            )

        except Exception as e:
            self.logger.error(f"Error en bulk create: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear bodegas en lote",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== MÉTODOS AUXILIARES ====================

    def _inicializar_stock_productos(self, bodega):
        """
        Crea registros de Stock en la nueva bodega
        para TODOS los productos existentes con cantidad=0

        CRÍTICO: Esta es la funcionalidad espejo de crear producto.
        Cuando creas producto → inicializa en todas las bodegas
        Cuando creas bodega → inicializa todos los productos

        Returns:
            int: Cantidad de productos inicializados
        """
        productos = Producto.objects.filter(
            empresa=self.request.tenant,
            is_active=True
        )

        stocks_crear = []
        for producto in productos:
            stocks_crear.append(
                Stock(
                    empresa=self.request.tenant,
                    bodega=bodega,
                    producto=producto,
                    cantidad=0,
                    stock_reservado=0,
                    costo_promedio_bodega=producto.precio_compra,  # Inicializar con precio de compra del producto
                    precio_venta_bodega=None,  # NULL = usa precio sugerido del producto
                    created_by=self.request.user
                )
            )

        # Bulk create para eficiencia
        if stocks_crear:
            Stock.objects.bulk_create(stocks_crear)

            self.logger.info(
                f"Stock inicializado | Bodega={bodega.codigo} | "
                f"Productos={len(stocks_crear)}"
            )

        return len(stocks_crear)