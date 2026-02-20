# apis/inventario/producto/producto_viewset.py
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, F, Sum, Count, Case, When, Value, CharField, DecimalField, ExpressionWrapper
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import Producto, Categoria, Stock
from apis.inventario.producto.producto_serializer import (
    ProductoListSerializer,
    ProductoDetailSerializer,
    ProductoCreateSerializer,
    ProductoUpdateSerializer,
    _crear_componentes,
    _crear_conversiones,
)


class ProductoViewSet(TenantViewSet):
    """
    ViewSet para gestión de productos.

    Endpoints:
        GET    /api/productos/                          - Listar
        POST   /api/productos/                          - Crear
        GET    /api/productos/{id}/                     - Detalle
        PUT    /api/productos/{id}/                     - Actualizar
        PATCH  /api/productos/{id}/                     - Actualizar parcial
        DELETE /api/productos/{id}/                     - Eliminar
        GET    /api/productos/buscar/                   - Búsqueda para selects
        GET    /api/productos/bajo_stock/               - Bajo stock mínimo
        GET    /api/productos/mas_vendidos/             - Top más vendidos
        GET    /api/productos/por_categoria/{id}/       - Por categoría e hijos
        GET    /api/productos/{id}/detalle_kit/         - Componentes del kit
        GET    /api/productos/{id}/inventario_total/    - Stock por bodega
        GET    /api/productos/{id}/imprimir_etiqueta/   - Datos para etiqueta
        POST   /api/productos/{id}/ajustar_precio/      - Ajustar precio de venta
        POST   /api/productos/{id}/duplicar/            - Duplicar producto
        POST   /api/productos/{id}/agregar_imagen/      - Subir/actualizar imagen

    Permisos:
        - ver_producto:      GET (list, retrieve, buscar, bajo_stock, detalle_kit, inventario_total, imprimir_etiqueta, por_categoria, mas_vendidos)
        - crear_producto:    POST (create, duplicar)
        - editar_producto:   PUT, PATCH (update, partial_update, agregar_imagen)
        - eliminar_producto: DELETE
        - ajustar_precios:   ajustar_precio
        - ver_reportes_producto: mas_vendidos
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apps.inventario')
    queryset         = Producto.objects.all()
    serializer_class = ProductoListSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListSerializer
        elif self.action == 'retrieve':
            return ProductoDetailSerializer
        elif self.action in ('update', 'partial_update'):
            return ProductoUpdateSerializer
        elif self.action == 'create':
            return ProductoCreateSerializer
        return ProductoListSerializer

    filterset_fields = ['tipo', 'es_kit', 'es_perecedero', 'categoria', 'marca', 'is_active']
    search_fields    = ['nombre', 'codigo', 'codigo_aux', 'codigo_barras']
    ordering_fields  = ['nombre', 'codigo', 'precio_venta', 'created_at']
    ordering         = ['-created_at']

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'categoria', 'marca', 'unidad_medida',
            'created_by', 'updated_by',
        ).prefetch_related(
            'componentes__componente',
            'conversiones__unidad_origen',
            'conversiones__unidad_destino',
            'stocks__bodega',
        ).annotate(
            stock_total_anotado=Sum('stocks__cantidad', distinct=True),
            stock_estado_calc=Case(
                When(stock_total_anotado__lte=0, then=Value('agotado')),
                When(stock_total_anotado__lte=F('stock_minimo'), then=Value('bajo')),
                When(stock_total_anotado__lte=F('stock_minimo') * 1.5, then=Value('medio')),
                default=Value('normal'),
                output_field=CharField(),
            ),
        )

        incluir_inactivos = self.request.query_params.get('incluir_inactivos', 'false')
        if incluir_inactivos.lower() not in ['true', '1']:
            queryset = queryset.filter(is_active=True)

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_producto')
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)
        except Exception as e:
            self.logger.error(f"Error al listar productos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('crear_producto')
    def create(self, request, *args, **kwargs):
        serializer = ProductoCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            self.logger.warning(
                f"Validación fallida al crear producto | Errores={serializer.errors} | Usuario={request.user.id}"
            )
            return StandardResponse.validation_error(serializer.errors)

        try:
            with transaction.atomic():
                producto = self._crear_producto(serializer.validated_data, request)

            self.logger.info(
                f"Producto creado | ID={producto.id} | Codigo={producto.codigo} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data=ProductoDetailSerializer(producto, context={'request': request}).data,
                mensaje="Producto creado exitosamente",
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            self.logger.error(f"Error al crear producto | Error={str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear producto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_producto')
    def retrieve(self, request, *args, **kwargs):
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=ProductoDetailSerializer(instancia, context={'request': request}).data
            )
        except Exception as e:
            self.logger.error(f"Error al obtener producto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener producto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_producto')
    def update(self, request, *args, **kwargs):
        try:
            partial   = kwargs.pop('partial', False)
            instancia = self.get_object()
            serializer = ProductoUpdateSerializer(
                instancia, data=request.data,
                partial=partial, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            instancia = serializer.save()

            self.logger.info(
                f"Producto actualizado | ID={instancia.id} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data=ProductoDetailSerializer(instancia, context={'request': request}).data,
                mensaje="Producto actualizado exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error al actualizar producto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar producto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('editar_producto')
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @requiere_permiso('eliminar_producto')
    def destroy(self, request, *args, **kwargs):
        try:
            instancia = self.get_object()

            if instancia.detalleventa_set.filter(venta__estado__in=['confirmada', 'facturada']).exists():
                return StandardResponse.error(
                    mensaje="No se puede eliminar un producto con ventas confirmadas o facturadas",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if instancia.detalleordencompra_set.filter(orden_compra__estado__in=['enviada', 'confirmada']).exists():
                return StandardResponse.error(
                    mensaje="No se puede eliminar un producto con órdenes de compra activas",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            self.perform_destroy(instancia)
            self.logger.info(f"Producto eliminado | ID={instancia.id} | Usuario={request.user.id}")
            return StandardResponse.success(
                mensaje="Producto eliminado exitosamente",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            self.logger.error(f"Error al eliminar producto: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al eliminar producto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_producto')
    def buscar(self, request):
        """GET /api/productos/buscar/?q=texto"""
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return StandardResponse.success(data={'results': [], 'total': 0})

            resultados = self.get_queryset().filter(
                Q(nombre__icontains=query) |
                Q(codigo__icontains=query) |
                Q(codigo_aux__icontains=query) |
                Q(codigo_barras__icontains=query)
            )[:20]

            serializer = ProductoListSerializer(resultados, many=True, context={'request': request})
            return StandardResponse.success(data={'results': serializer.data, 'total': len(serializer.data)})
        except Exception as e:
            self.logger.error(f"Error en búsqueda de productos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al buscar productos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_producto')
    def bajo_stock(self, request):
        """GET /api/productos/bajo_stock/"""
        try:
            productos = self.get_queryset().filter(
                stock_total_anotado__lte=F('stock_minimo')
            ).distinct()

            page = self.paginate_queryset(productos)
            if page is not None:
                serializer = ProductoListSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)

            serializer = ProductoListSerializer(productos, many=True, context={'request': request})
            return StandardResponse.success(data=serializer.data)
        except Exception as e:
            self.logger.error(f"Error al obtener bajo stock: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos con bajo stock",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_reportes_producto')
    def mas_vendidos(self, request):
        """
        GET /api/productos/mas_vendidos/?limit=10
        2 queries: 1 aggregate + 1 bulk fetch
        """
        try:
            from apps.ventas.models import DetalleVenta

            limit = int(request.query_params.get('limit', 10))

            productos_vendidos = DetalleVenta.objects.filter(
                venta__empresa=request.empresa
            ).values('producto_id').annotate(
                total_vendido=Sum('cantidad'),
                total_ingresos=Sum(
                    ExpressionWrapper(F('cantidad') * F('precio_unitario'), output_field=DecimalField())
                )
            ).order_by('-total_vendido')[:limit]

            producto_ids = [p['producto_id'] for p in productos_vendidos]
            productos = Producto.objects.filter(id__in=producto_ids).only('id', 'codigo', 'nombre')
            productos_dict = {p.id: p for p in productos}

            resultados = [
                {
                    'producto': {
                        'id': str(item['producto_id']),
                        'codigo': productos_dict[item['producto_id']].codigo,
                        'nombre': productos_dict[item['producto_id']].nombre,
                    },
                    'cantidad_vendida': item['total_vendido'],
                    'ingresos_generados': float(item['total_ingresos'] or 0),
                }
                for item in productos_vendidos
                if item['producto_id'] in productos_dict
            ]

            return StandardResponse.success(data={
                'total_productos': len(resultados),
                'productos': resultados,
            })
        except Exception as e:
            self.logger.error(f"Error en más vendidos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos más vendidos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='por_categoria/(?P<categoria_id>[^/.]+)')
    @requiere_permiso('ver_producto')
    def por_categoria(self, request, categoria_id=None):
        """GET /api/productos/por_categoria/{id}/"""
        try:
            try:
                categoria = Categoria.objects.get(id=categoria_id, empresa=request.empresa)
            except Categoria.DoesNotExist:
                return StandardResponse.error(
                    mensaje="Categoría no encontrada",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            categorias_ids = list(
                Categoria.objects.filter(
                    Q(id=categoria.id) | Q(categoria_padre=categoria),
                    empresa=request.empresa
                ).values_list('id', flat=True)
            )

            productos = self.get_queryset().filter(categoria_id__in=categorias_ids)

            page = self.paginate_queryset(productos)
            if page is not None:
                serializer = ProductoListSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)

            serializer = ProductoListSerializer(productos, many=True, context={'request': request})
            return StandardResponse.success(data={
                'categoria': {'id': str(categoria.id), 'nombre': categoria.nombre, 'codigo': categoria.codigo},
                'total_productos': productos.count(),
                'productos': serializer.data,
            })
        except Exception as e:
            self.logger.error(f"Error en por_categoria: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener productos por categoría",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_producto')
    def detalle_kit(self, request, pk=None):
        """GET /api/productos/{id}/detalle_kit/"""
        try:
            producto = self.get_object()
            if not producto.es_kit:
                return StandardResponse.error(
                    mensaje="Este producto no es un kit",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            componentes = producto.componentes.all()
            costo_total = sum(
                comp.componente.precio_compra * comp.cantidad
                for comp in componentes
            )

            componentes_data = [
                {
                    'id': str(comp.id),
                    'componente': {
                        'id': str(comp.componente.id),
                        'codigo': comp.componente.codigo,
                        'nombre': comp.componente.nombre,
                        'precio_unitario': float(comp.componente.precio_compra),
                    },
                    'cantidad': float(comp.cantidad),
                    'subtotal': float(comp.componente.precio_compra * comp.cantidad),
                    'es_opcional': comp.es_opcional,
                    'observaciones': comp.observaciones,
                }
                for comp in componentes
            ]

            return StandardResponse.success(data={
                'kit': {
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio_venta_actual': float(producto.precio_venta),
                },
                'componentes': componentes_data,
                'resumen': {
                    'total_componentes': len(componentes_data),
                    'costo_total': float(costo_total),
                    'margen_actual': float(producto.precio_venta - costo_total),
                },
            })
        except Exception as e:
            self.logger.error(f"Error en detalle_kit: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener detalle del kit",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_producto')
    def inventario_total(self, request, pk=None):
        """GET /api/productos/{id}/inventario_total/"""
        try:
            producto = self.get_object()

            stocks = Stock.objects.filter(
                producto=producto
            ).select_related('bodega', 'ubicacion')

            if not request.user.has_perm('inventario.view_stock_todas_bodegas'):
                stocks = stocks.filter(bodega__responsable__usuario=request.user)

            bodegas_data = [
                {
                    'bodega': {
                        'id': str(s.bodega.id),
                        'codigo': s.bodega.codigo,
                        'nombre': s.bodega.nombre,
                        'es_principal': s.bodega.es_principal,
                        'permite_ventas': s.bodega.permite_ventas,
                    },
                    'ubicacion': (
                        f"{s.ubicacion.pasillo}-{s.ubicacion.estante}-{s.ubicacion.nivel}"
                        if s.ubicacion else None
                    ),
                    'cantidad': float(s.cantidad),
                    'stock_reservado': float(s.stock_reservado),
                    'stock_disponible': float(s.cantidad_disponible),
                }
                for s in stocks
            ]

            stock_total     = sum(b['cantidad'] for b in bodegas_data)
            stock_reservado = sum(b['stock_reservado'] for b in bodegas_data)

            valorizacion = None
            if request.user.has_perm('inventario.view_stock_valorizado'):
                valorizacion = {
                    'valor_compra': float(stock_total * producto.precio_compra),
                    'valor_venta': float(stock_total * producto.precio_venta),
                    'utilidad_potencial': float(stock_total * (producto.precio_venta - producto.precio_compra)),
                }

            return StandardResponse.success(data={
                'producto': {
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'stock_minimo': float(producto.stock_minimo),
                },
                'resumen': {
                    'total_bodegas': len(bodegas_data),
                    'stock_total': stock_total,
                    'stock_reservado': stock_reservado,
                    'stock_disponible': stock_total - stock_reservado,
                    'necesita_reposicion': stock_total <= float(producto.stock_minimo),
                },
                'valorizacion': valorizacion,
                'por_bodega': bodegas_data,
            })
        except Exception as e:
            self.logger.error(f"Error en inventario_total: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener inventario total",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    @requiere_permiso('ver_producto')
    def imprimir_etiqueta(self, request, pk=None):
        """GET /api/productos/{id}/imprimir_etiqueta/"""
        try:
            producto = self.get_object()
            return StandardResponse.success(data={
                'producto': {
                    'codigo': producto.codigo,
                    'codigo_barras': producto.codigo_barras or producto.codigo,
                    'nombre': producto.nombre,
                    'descripcion': (producto.descripcion or '')[:100],
                    'precio_venta': float(producto.precio_venta),
                    'unidad_medida': producto.unidad_medida.abreviatura if producto.unidad_medida else 'UN',
                },
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'marca': producto.marca.nombre if producto.marca else '',
                'iva': 'SÍ' if producto.iva else 'NO',
                'empresa': {
                    'nombre': request.empresa.nombre_comercial,
                    'ruc': request.empresa.ruc,
                },
            })
        except Exception as e:
            self.logger.error(f"Error en imprimir_etiqueta: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al generar etiqueta",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('ajustar_precios')
    def ajustar_precio(self, request, pk=None):
        """POST /api/productos/{id}/ajustar_precio/ — Body: {precio_venta: 150.00}"""
        try:
            producto = self.get_object()
            nuevo_precio = request.data.get('precio_venta')

            if nuevo_precio is None:
                return StandardResponse.validation_error({'precio_venta': ['Este campo es requerido.']})

            try:
                nuevo_precio = Decimal(str(nuevo_precio))
                if nuevo_precio <= 0:
                    raise ValueError
            except (ValueError, Exception):
                return StandardResponse.validation_error({'precio_venta': ['El precio debe ser mayor a 0.']})

            precio_anterior = producto.precio_venta
            producto.precio_venta = nuevo_precio
            producto.save(update_fields=['precio_venta', 'updated_by'])

            self.logger.info(
                f"Precio ajustado | ID={producto.id} | Anterior={precio_anterior} | Nuevo={nuevo_precio} | Usuario={request.user.id}"
            )

            margen = nuevo_precio - producto.precio_compra
            return StandardResponse.success(
                data={
                    'precio_anterior': float(precio_anterior),
                    'precio_nuevo': float(nuevo_precio),
                    'margen': {
                        'monto': float(margen),
                        'porcentaje': round(float((margen / producto.precio_compra) * 100), 2) if producto.precio_compra else 0,
                    },
                },
                mensaje="Precio actualizado exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error en ajustar_precio: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al ajustar precio",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('crear_producto')
    def duplicar(self, request, pk=None):
        """POST /api/productos/{id}/duplicar/ — Body opcional: {nombre, codigo_aux}"""
        try:
            original = self.get_object()

            with transaction.atomic():
                producto_nuevo = Producto.objects.create(
                    empresa=request.empresa,
                    created_by=request.user,
                    nombre=request.data.get('nombre', f"{original.nombre} (Copia)"),
                    codigo_aux=request.data.get('codigo_aux', None),
                    descripcion=original.descripcion,
                    categoria=original.categoria,
                    marca=original.marca,
                    unidad_medida=original.unidad_medida,
                    tipo=original.tipo,
                    es_kit=original.es_kit,
                    precio_compra=original.precio_compra,
                    precio_venta=original.precio_venta,
                    stock_minimo=original.stock_minimo,
                    iva=original.iva,
                    codigo_barras='',
                    es_perecedero=original.es_perecedero,
                    dias_vida_util=original.dias_vida_util,
                    peso=original.peso,
                    costo_promedio=original.costo_promedio,
                    ultimo_costo=original.ultimo_costo,
                )

                if original.es_kit:
                    _crear_componentes(
                        producto_nuevo,
                        [
                            {
                                'componente': comp.componente,
                                'cantidad': comp.cantidad,
                                'es_opcional': comp.es_opcional,
                                'observaciones': comp.observaciones,
                            }
                            for comp in original.componentes.all()
                        ]
                    )

                conversiones = original.conversiones.all()
                if conversiones.exists():
                    _crear_conversiones(
                        producto_nuevo,
                        [
                            {
                                'unidad_origen': c.unidad_origen,
                                'unidad_destino': c.unidad_destino,
                                'factor_conversion': c.factor_conversion,
                            }
                            for c in conversiones
                        ]
                    )

            self.logger.info(
                f"Producto duplicado | Original={original.id} | Nuevo={producto_nuevo.id} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data=ProductoDetailSerializer(producto_nuevo, context={'request': request}).data,
                mensaje="Producto duplicado exitosamente",
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            self.logger.error(f"Error en duplicar: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al duplicar producto",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_producto')
    def agregar_imagen(self, request, pk=None):
        """POST /api/productos/{id}/agregar_imagen/ — FormData con campo 'imagen'"""
        try:
            producto = self.get_object()

            if 'imagen' not in request.FILES:
                return StandardResponse.validation_error({'imagen': ['Este campo es requerido.']})

            producto.imagen = request.FILES['imagen']
            producto.save(update_fields=['imagen', 'updated_by'])

            self.logger.info(f"Imagen actualizada | ID={producto.id} | Usuario={request.user.id}")
            return StandardResponse.success(
                data={'imagen_url': producto.imagen.url if producto.imagen else None},
                mensaje="Imagen actualizada exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error en agregar_imagen: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al actualizar imagen",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== MÉTODOS AUXILIARES ====================

    def _crear_producto(self, validated_data, request):
        categoria_id      = validated_data.pop('categoria_id')
        marca_id          = validated_data.pop('marca_id', None)
        unidad_medida_id  = validated_data.pop('unidad_medida_id')
        componentes_data  = validated_data.pop('componentes_data', [])
        conversiones_data = validated_data.pop('conversiones_data', [])

        producto = Producto.objects.create(
            empresa=request.empresa,
            created_by=request.user,
            categoria_id=categoria_id,
            marca_id=marca_id,
            unidad_medida_id=unidad_medida_id,
            **validated_data
        )
        self.logger.info(f"Llamando _inicializar_stock_bodegas | Producto={producto.id} | Empresa={producto.empresa_id}")
        producto._inicializar_stock_bodegas()
        self.logger.info(f"_inicializar_stock_bodegas completado")

        if producto.es_kit and componentes_data:
            _crear_componentes(producto, componentes_data)

        if conversiones_data:
            _crear_conversiones(producto, conversiones_data)

        return producto