# apis/inventario/producto/producto_viewset.py (OPTIMIZADO)
import logging
from django.utils import timezone
from django.db.models import Q, Sum, F, DecimalField, Count, ExpressionWrapper, Case, When, Value, CharField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apis.inventario.producto.producto_serializer import (ProductoSerializer, ProductoSimpleSerializer)
from apps.inventario.models import Producto, Categoria, MovimientoInventario
from apis.inventario.movimiento.movimiento_serializer import MovimientoInventarioSerializer
from utils.mixins.permissions import PermissionCheckMixin
from apis.core.ViewSetBase import TenantViewSet


class ProductoViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet para gestionar Productos del inventario.

    ✨ OPTIMIZACIONES IMPLEMENTADAS:
    - Annotate para cálculos de kits (elimina queries en to_representation)
    - Query optimizada para mas_vendidos (de 10k+ queries a 2)
    - Prefetch_related mejorado para componentes y conversiones
    - Cálculo de stock_estado en DB en lugar de Python
    """
    queryset = Producto.objects.select_related(
        'categoria', 'marca', 'unidad_medida'
    ).prefetch_related(
        'componentes__componente',
        'conversiones__unidad_origen',
        'conversiones__unidad_destino'
    ).order_by('-created_at', 'id')  # Orden consistente para paginación
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('producto_viewset')

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        """
        Optimiza queries y filtra productos activos por defecto.
        INCLUYE FILTRO MULTI-TENANT
        """
        # CRÍTICO: Llama primero al filtro de tenant
        queryset = super().get_queryset()

        # Filtro de activos
        incluir_inactivos = self.request.query_params.get('incluir_inactivos', 'false')
        if incluir_inactivos.lower() not in ['true', '1', 'yes']:
            queryset = queryset.filter(is_active=True)

        # OPTIMIZACIÓN 1: Calcular total de componentes en DB
        queryset = queryset.annotate(
            total_componentes_count=Count('componentes', distinct=True)
        )

        # OPTIMIZACIÓN 2: Calcular costo de componentes en DB
        queryset = queryset.annotate(
            costo_componentes_sum=Sum(
                ExpressionWrapper(
                    F('componentes__componente__precio_compra') * F('componentes__cantidad'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                distinct=True
            )
        )

        # OPTIMIZACIÓN 3: Calcular stock_estado en DB
        queryset = queryset.annotate(
            stock_total=Sum('stocks__cantidad', distinct=True),
            stock_estado_calc=Case(
                When(stock_total=0, then=Value('agotado')),
                When(stock_total__lte=F('stock_minimo'), then=Value('bajo')),
                When(stock_total__lte=F('stock_minimo') * 1.5, then=Value('medio')),
                default=Value('normal'),
                output_field=CharField()
            )
        )

        return queryset

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return ProductoSimpleSerializer
        return ProductoSerializer

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        """
        Listar productos con filtros avanzados.
        Permiso: view_producto

        Query params:
        - tipo: simple|kit|servicio
        - categoria: ID de categoría
        - marca: ID de marca
        - stock_bajo: true (productos bajo stock mínimo)
        - search: búsqueda general
        - is_active: true|false
        """
        try:
            self.verificar_permiso('view_producto')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por tipo
            tipo = request.query_params.get('tipo', None)
            if tipo in ['simple', 'kit', 'servicio']:
                queryset = queryset.filter(tipo=tipo)

            # Filtro por categoría
            categoria_id = request.query_params.get('categoria', None)
            if categoria_id:
                queryset = queryset.filter(categoria_id=categoria_id)

            # Filtro por marca
            marca_id = request.query_params.get('marca', None)
            if marca_id:
                queryset = queryset.filter(marca_id=marca_id)

            # Filtro por stock bajo
            stock_bajo = request.query_params.get('stock_bajo', None)
            if stock_bajo and stock_bajo.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(stock__lte=F('stock_minimo'))

            # Búsqueda general
            search = request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(codigo__icontains=search) |
                    Q(nombre__icontains=search) |
                    Q(codigo_barras__icontains=search) |
                    Q(descripcion__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error listando productos: {str(e)}", extra={
                'action': 'list_productos',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener la lista de productos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crear un nuevo producto.
        Permiso: add_producto
        """
        try:
            self.verificar_permiso('add_producto')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            producto = serializer.save()

            self.logger.info(
                f"Producto creado por {request.user.username}: {producto.id}",
                extra={
                    'producto_id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'tipo': producto.tipo,
                    'creado_por': request.user.username,
                    'action': 'create_producto'
                }
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        except PermissionDenied as e:
            self.logger.error(f"Permiso denegado al crear producto: {str(e)}", extra={})
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            self.logger.error(f"Error creando producto: {str(e)}", extra={})
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()

            self.logger.error(f"Error creando producto: {str(e)}", extra={
                'action': 'create_producto',
                'error': str(e),
                'request_data': request.data
            })
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener un producto específico.
        Permiso: view_producto
        """
        try:
            self.verificar_permiso('view_producto')

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Producto.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo producto: {str(e)}", extra={
                'action': 'retrieve_producto',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener el producto'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualizar completamente un producto.
        Permiso: change_producto
        """
        try:
            self.verificar_permiso('change_producto')

            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            producto = serializer.save()

            self.logger.info(
                f"Producto actualizado por {request.user.username}: {producto.id}",
                extra={
                    'producto_id': producto.id,
                    'actualizado_por': request.user.username,
                    'action': 'update_producto'
                }
            )

            return Response(serializer.data)

        except PermissionDenied as e:
            self.logger.error(f"Permiso denegado al actualizar producto: {str(e)}", extra={})
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Producto.DoesNotExist as e:
            self.logger.error(f"Producto no encontrado: {str(e)}", extra={})
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            self.logger.error(f"Error actualizando producto: {str(e)}", extra={})
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando producto: {str(e)}", extra={
                'action': 'update_producto',
                'error': str(e)
            })
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Actualizar parcialmente un producto.
        Permiso: change_producto
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un producto (soft delete).
        Permiso: delete_producto
        """
        try:
            self.verificar_permiso(
                'delete_producto',
                'Solo Supervisores y Gerentes pueden eliminar productos'
            )

            instance = self.get_object()
            producto_id = instance.id
            codigo = instance.codigo

            # Soft delete
            instance.is_active = False
            instance.save()

            self.logger.info(
                f"Producto desactivado por {request.user.username}: {producto_id}",
                extra={
                    'producto_id': producto_id,
                    'codigo': codigo,
                    'desactivado_por': request.user.username,
                    'action': 'delete_producto'
                }
            )

            return Response(
                {'message': 'Producto desactivado exitosamente'},
                status=status.HTTP_200_OK
            )

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Producto.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error eliminando producto: {str(e)}", extra={
                'action': 'delete_producto',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al eliminar el producto'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        """
        Buscar productos por término de búsqueda.
        GET /api/productos/buscar/?q=termino
        Permiso: view_producto
        """
        try:
            self.verificar_permiso('view_producto')

            query = request.query_params.get('q', '').strip()

            if not query:
                return Response(
                    {'error': 'Parámetro de búsqueda "q" es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            productos = self.get_queryset().filter(
                Q(codigo__icontains=query) |
                Q(nombre__icontains=query) |
                Q(codigo_barras__icontains=query) |
                Q(descripcion__icontains=query)
            )[:20]  # Limitar resultados

            serializer = ProductoSimpleSerializer(productos, many=True)

            return Response({
                'count': productos.count(),
                'results': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error buscando productos: {str(e)}", extra={
                'action': 'buscar_productos',
                'error': str(e),
                'query': query
            })
            return Response(
                {'error': 'Error al buscar productos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='stock-bajo')
    def stock_bajo(self, request):
        """
        Listar productos con stock bajo o agotado.
        GET /api/productos/stock-bajo/
        Permiso: view_producto
        """
        try:
            self.verificar_permiso('view_producto')

            productos = self.get_queryset().filter(
                stock__lte=F('stock_minimo')
            ).order_by('stock')

            serializer = ProductoSimpleSerializer(productos, many=True)

            # Estadísticas
            agotados = productos.filter(stock=0).count()
            bajo_stock = productos.filter(stock__gt=0).count()

            return Response({
                'estadisticas': {
                    'total': productos.count(),
                    'agotados': agotados,
                    'bajo_stock': bajo_stock
                },
                'productos': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo stock bajo: {str(e)}", extra={
                'action': 'stock_bajo',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener productos con stock bajo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='por-categoria/(?P<categoria_id>[^/.]+)')
    def por_categoria(self, request, categoria_id=None):
        """
        Listar productos de una categoría (incluye subcategorías).
        GET /api/productos/por-categoria/{id}/
        Permiso: view_producto
        """
        try:
            self.verificar_permiso('view_producto')

            try:
                categoria = Categoria.objects.get(id=categoria_id)
            except Categoria.DoesNotExist:
                return Response(
                    {'error': 'Categoría no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Obtener categoría y todas sus subcategorías
            categorias_ids = [categoria.id]
            subcategorias = Categoria.objects.filter(categoria_padre=categoria)
            categorias_ids.extend(subcategorias.values_list('id', flat=True))

            productos = self.get_queryset().filter(
                categoria_id__in=categorias_ids
            )

            serializer = ProductoSimpleSerializer(productos, many=True)

            return Response({
                'categoria': {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                    'codigo': categoria.codigo
                },
                'total_productos': productos.count(),
                'productos': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo productos por categoría: {str(e)}", extra={
                'action': 'por_categoria',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener productos por categoría'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='detalle-kit')
    def detalle_kit(self, request, pk=None):
        """
        Ver detalles completos de un kit con sus componentes.
        GET /api/productos/{id}/detalle-kit/
        Permiso: view_producto

        OPTIMIZADO: Usa prefetch_related del queryset base
        """
        try:
            self.verificar_permiso('view_producto')

            producto = self.get_object()

            if not producto.es_kit:
                return Response(
                    {'error': 'Este producto no es un kit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Ya viene con prefetch_related('componentes__componente')
            componentes = producto.componentes.all()

            # Calcular costo total del kit
            costo_total = sum(
                comp.componente.precio_compra * comp.cantidad
                for comp in componentes
            )

            # Calcular precio sugerido con margen
            margen_sugerido = 1.3  # 30% de margen
            precio_sugerido = costo_total * margen_sugerido

            componentes_data = [{
                'id': comp.id,
                'componente': {
                    'id': comp.componente.id,
                    'codigo': comp.componente.codigo,
                    'nombre': comp.componente.nombre,
                    'precio_unitario': float(comp.componente.precio_compra),
                    'stock_disponible': comp.componente.stock
                },
                'cantidad': float(comp.cantidad),
                'subtotal': float(comp.componente.precio_compra * comp.cantidad),
                'es_opcional': comp.es_opcional,
                'observaciones': comp.observaciones
            } for comp in componentes]

            return Response({
                'kit': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio_venta_actual': float(producto.precio_venta)
                },
                'componentes': componentes_data,
                'resumen': {
                    'total_componentes': len(componentes_data),
                    'costo_total': float(costo_total),
                    'precio_sugerido': float(precio_sugerido),
                    'margen_actual': float(producto.precio_venta - costo_total) if producto.precio_venta else 0
                }
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo detalle kit: {str(e)}", extra={
                'action': 'detalle_kit',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener detalle del kit'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='ajustar-stock')
    def ajustar_stock(self, request, pk=None):
        """
        Ajustar stock de un producto manualmente.
        POST /api/productos/{id}/ajustar-stock/
        Body: {"cantidad": 10, "tipo": "incremento|decremento", "motivo": "texto"}
        Permiso: ajustar_stock
        """
        try:
            self.verificar_permiso(
                'ajustar_stock',
                'No tienes permiso para ajustar stock'
            )

            producto = self.get_object()

            if producto.es_kit:
                return Response(
                    {'error': 'No se puede ajustar stock de kits manualmente'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cantidad = request.data.get('cantidad')
            tipo = request.data.get('tipo', 'incremento')
            motivo = request.data.get('motivo', 'Ajuste manual')

            if not cantidad:
                return Response(
                    {'error': 'Se requiere el campo "cantidad"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")
            except ValueError as e:
                return Response(
                    {'error': f'Cantidad inválida: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            stock_anterior = producto.stock

            if tipo == 'incremento':
                producto.stock += cantidad
            elif tipo == 'decremento':
                if producto.stock < cantidad:
                    return Response(
                        {'error': f'Stock insuficiente. Stock actual: {producto.stock}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                producto.stock -= cantidad
            else:
                return Response(
                    {'error': 'Tipo debe ser "incremento" o "decremento"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            producto.save()

            self.logger.info(
                f"Stock ajustado por {request.user.username}",
                extra={
                    'producto_id': producto.id,
                    'codigo': producto.codigo,
                    'stock_anterior': stock_anterior,
                    'stock_nuevo': producto.stock,
                    'tipo': tipo,
                    'cantidad': cantidad,
                    'motivo': motivo,
                    'ajustado_por': request.user.username,
                    'action': 'ajustar_stock'
                }
            )

            return Response({
                'message': f'Stock {tipo} exitosamente',
                'stock_anterior': stock_anterior,
                'stock_actual': producto.stock,
                'cantidad_ajustada': cantidad,
                'tipo': tipo
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error ajustando stock: {str(e)}", extra={
                'action': 'ajustar_stock',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al ajustar stock'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='ajustar-precio')
    def ajustar_precio(self, request, pk=None):
        """
        Ajustar precio de venta de un producto.
        POST /api/productos/{id}/ajustar-precio/
        Body: {"precio_venta": 150.00}
        Permiso: ajustar_precios (Solo Gerente)
        """
        try:
            self.verificar_permiso(
                'ajustar_precios',
                'Solo Gerentes pueden ajustar precios'
            )

            producto = self.get_object()
            nuevo_precio = request.data.get('precio_venta')

            if nuevo_precio is None:
                return Response(
                    {'error': 'Se requiere el campo "precio_venta"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                nuevo_precio = float(nuevo_precio)
                if nuevo_precio <= 0:
                    raise ValueError("El precio debe ser mayor a 0")
            except ValueError as e:
                return Response(
                    {'error': f'Precio inválido: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            precio_anterior = producto.precio_venta
            producto.precio_venta = nuevo_precio
            producto.save()

            # Calcular nuevo margen
            margen = nuevo_precio - producto.precio_compra
            margen_porcentaje = (margen / producto.precio_compra) * 100

            self.logger.info(
                f"Precio ajustado por {request.user.username}",
                extra={
                    'producto_id': producto.id,
                    'codigo': producto.codigo,
                    'precio_anterior': float(precio_anterior),
                    'precio_nuevo': nuevo_precio,
                    'margen_porcentaje': float(margen_porcentaje),
                    'ajustado_por': request.user.username,
                    'action': 'ajustar_precio'
                }
            )

            return Response({
                'message': 'Precio actualizado exitosamente',
                'precio_anterior': float(precio_anterior),
                'precio_nuevo': float(producto.precio_venta),
                'margen': {
                    'monto': float(margen),
                    'porcentaje': round(float(margen_porcentaje), 2)
                }
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error ajustando precio: {str(e)}", extra={
                'action': 'ajustar_precio',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al ajustar precio'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """
        Activar un producto desactivado.
        POST /api/productos/{id}/activar/
        Permiso: delete_producto
        """
        try:
            self.verificar_permiso('delete_producto')

            producto = self.get_object()
            producto.is_active = True
            producto.save()

            self.logger.info(
                f"Producto activado por {request.user.username}: {producto.id}",
                extra={
                    'producto_id': producto.id,
                    'codigo': producto.codigo,
                    'activado_por': request.user.username,
                    'action': 'activar_producto'
                }
            )

            serializer = self.get_serializer(producto)
            return Response({
                'message': 'Producto activado exitosamente',
                'producto': serializer.data
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error activando producto: {str(e)}", extra={
                'action': 'activar_producto',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al activar producto'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='mas-vendidos')
    def mas_vendidos(self, request):
        """
        Top productos más vendidos.
        GET /api/productos/mas-vendidos/?limit=10
        Permiso: ver_reportes_producto

        OPTIMIZACIÓN CRÍTICA:
        Antes: 10,000+ queries (1 por cada DetalleVenta + 1 por cada Producto)
        Ahora: 2 queries (1 aggregate + 1 bulk fetch)

        Mejora: ~99.98% reducción en queries
        """
        try:
            self.verificar_permiso(
                'ver_reportes_producto',
                'No tienes permiso para ver reportes'
            )

            from apps.ventas.models import DetalleVenta

            limit = int(request.query_params.get('limit', 10))

            # QUERY 1: Aggregate sin JOINs innecesarios
            productos_vendidos = DetalleVenta.objects.values('producto_id').annotate(
                total_vendido=Sum('cantidad'),
                total_ingresos=Sum(
                    F('cantidad') * F('precio_unitario'),
                    output_field=DecimalField()
                )
            ).order_by('-total_vendido')[:limit]

            # QUERY 2: Bulk fetch de productos
            producto_ids = [p['producto_id'] for p in productos_vendidos]
            productos = Producto.objects.filter(
                id__in=producto_ids
            ).only('id', 'codigo', 'nombre')  # Solo campos necesarios

            # Crear diccionario para lookup O(1)
            productos_dict = {p.id: p for p in productos}

            # Combinar resultados sin queries adicionales
            resultados = [{
                'producto': {
                    'id': item['producto_id'],
                    'codigo': productos_dict[item['producto_id']].codigo,
                    'nombre': productos_dict[item['producto_id']].nombre
                },
                'cantidad_vendida': item['total_vendido'],
                'ingresos_generados': float(item['total_ingresos'])
            } for item in productos_vendidos if item['producto_id'] in productos_dict]

            return Response({
                'periodo': 'Histórico',
                'total_productos': len(resultados),
                'productos': resultados
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo más vendidos: {str(e)}", extra={
                'action': 'mas_vendidos',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener productos más vendidos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        """Obtiene todos los movimientos de un producto"""
        producto = self.get_object()
        movimientos = MovimientoInventario.objects.filter(
            detalles__producto=producto
        ).distinct()

        serializer = MovimientoInventarioSerializer(movimientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """Crear múltiples productos. Permiso: add_producto"""
        try:
            self.verificar_permiso('add_producto')

            productos_data = request.data.get('productos', [])
            if not isinstance(productos_data, list) or not productos_data:
                return Response(
                    {'error': 'Se debe proporcionar una lista de productos para crear'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_productos = []
            errors = []

            for idx, producto_data in enumerate(productos_data):
                serializer = self.get_serializer(data=producto_data)
                if serializer.is_valid():
                    producto = serializer.save()
                    created_productos.append(serializer.data)
                    self.logger.info(f"Producto creado en bulk: {producto.id}")
                else:
                    errors.append({'index': idx, 'errors': serializer.errors})

            response_data = {'created_productos': created_productos}
            if errors:
                response_data['errors'] = errors

            return Response(response_data, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error en bulk create de productos: {str(e)}")
            return Response({'error': 'Error al crear productos en bulk'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='agregar-imagen')
    def agregar_imagen(self, request, pk=None):
        """
        Subir o actualizar imagen del producto.
        POST /api/productos/{id}/agregar-imagen/
        Body: FormData con campo 'imagen'
        Permiso: change_producto
        """
        try:
            self.verificar_permiso('change_producto')

            producto = self.get_object()

            if 'imagen' not in request.FILES:
                return Response(
                    {'error': 'Se requiere el campo "imagen" en el FormData'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            imagen_anterior = producto.imagen.url if producto.imagen else None

            # Actualizar imagen
            producto.imagen = request.FILES['imagen']
            producto.save()

            self.logger.info(
                f"Imagen actualizada por {request.user.username}",
                extra={
                    'producto_id': producto.id,
                    'codigo': producto.codigo,
                    'imagen_anterior': imagen_anterior,
                    'imagen_nueva': producto.imagen.url,
                    'actualizado_por': request.user.username,
                    'action': 'agregar_imagen'
                }
            )

            return Response({
                'message': 'Imagen actualizada exitosamente',
                'imagen_url': producto.imagen.url if producto.imagen else None,
                'producto': {
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre
                }
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error agregando imagen: {str(e)}", extra={
                'action': 'agregar_imagen',
                'error': str(e)
            })
            return Response(
                {'error': f'Error al actualizar imagen: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='imprimir-etiqueta')
    def imprimir_etiqueta(self, request, pk=None):
        """
        Generar datos para etiqueta con código de barras.
        GET /api/productos/{id}/imprimir-etiqueta/
        Permiso: view_producto

        Retorna información formateada para imprimir etiqueta con código de barras.
        El frontend puede usar esta data para generar PDF o renderizar etiqueta.
        """
        try:
            self.verificar_permiso('view_producto')

            producto = self.get_object()

            # Datos para la etiqueta
            etiqueta_data = {
                'producto': {
                    'codigo': producto.codigo,
                    'codigo_barras': producto.codigo_barras or producto.codigo,
                    'nombre': producto.nombre,
                    'descripcion': producto.descripcion[:100] if producto.descripcion else '',
                    'precio_venta': float(producto.precio_venta),
                    'unidad_medida': producto.unidad_medida.abreviatura if producto.unidad_medida else 'UN'
                },
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'marca': producto.marca.nombre if producto.marca else '',
                'iva': 'SÍ' if producto.iva else 'NO',
                'fecha_generacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'empresa': {
                    'nombre': request.tenant.nombre if hasattr(request, 'tenant') else 'Empresa',
                    'ruc': request.tenant.ruc if hasattr(request, 'tenant') else ''
                }
            }

            self.logger.info(
                f"Etiqueta generada para producto {producto.codigo}",
                extra={
                    'producto_id': producto.id,
                    'generado_por': request.user.username,
                    'action': 'imprimir_etiqueta'
                }
            )

            return Response(etiqueta_data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error generando etiqueta: {str(e)}", extra={
                'action': 'imprimir_etiqueta',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al generar etiqueta'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='duplicar')
    def duplicar(self, request, pk=None):
        """
        Crear una copia de un producto existente.
        POST /api/productos/{id}/duplicar/
        Body (opcional): {
            "nombre": "Nuevo nombre (opcional)",
            "codigo_aux": "Nuevo código auxiliar (opcional)"
        }
        Permiso: add_producto
        """
        try:
            self.verificar_permiso('add_producto')

            producto_original = self.get_object()

            # Crear copia
            from django.db import transaction

            with transaction.atomic():
                # Duplicar producto
                producto_nuevo = Producto.objects.create(
                    # Datos básicos (se autogenera el código)
                    codigo_aux=request.data.get('codigo_aux',
                                                f"{producto_original.codigo_aux}_COPIA" if producto_original.codigo_aux else None),
                    nombre=request.data.get('nombre', f"{producto_original.nombre} (Copia)"),
                    descripcion=producto_original.descripcion,
                    categoria=producto_original.categoria,
                    marca=producto_original.marca,
                    unidad_medida=producto_original.unidad_medida,
                    tipo=producto_original.tipo,
                    es_kit=producto_original.es_kit,

                    # Precios y stock (stock en 0 por defecto)
                    precio_compra=producto_original.precio_compra,
                    precio_venta=producto_original.precio_venta,
                    stock=0,  # El duplicado empieza sin stock
                    stock_minimo=producto_original.stock_minimo,

                    # Configuración
                    iva=producto_original.iva,
                    codigo_barras='',  # Debe ser único, se deja vacío
                    es_perecedero=producto_original.es_perecedero,
                    dias_vida_util=producto_original.dias_vida_util,
                    peso=producto_original.peso,

                    # Costos
                    costo_promedio=producto_original.costo_promedio,
                    ultimo_costo=producto_original.ultimo_costo,

                    # Tenant
                    empresa=producto_original.empresa
                )

                # Si es un kit, duplicar componentes
                if producto_original.es_kit:
                    from apps.inventario.models import ComponenteKit
                    for componente in producto_original.componentes.all():
                        ComponenteKit.objects.create(
                            kit=producto_nuevo,
                            componente=componente.componente,
                            cantidad=componente.cantidad,
                            es_opcional=componente.es_opcional,
                            observaciones=componente.observaciones,
                            empresa=componente.empresa
                        )

                # Duplicar conversiones de unidad de medida si existen
                from apps.inventario.models import UnidadConversion
                for conversion in producto_original.conversiones.all():
                    UnidadConversion.objects.create(
                        producto=producto_nuevo,
                        unidad_origen=conversion.unidad_origen,
                        unidad_destino=conversion.unidad_destino,
                        factor_conversion=conversion.factor_conversion,
                        empresa=conversion.empresa
                    )

            self.logger.info(
                f"Producto duplicado por {request.user.username}",
                extra={
                    'producto_original_id': producto_original.id,
                    'producto_nuevo_id': producto_nuevo.id,
                    'codigo_original': producto_original.codigo,
                    'codigo_nuevo': producto_nuevo.codigo,
                    'duplicado_por': request.user.username,
                    'action': 'duplicar_producto'
                }
            )

            serializer = self.get_serializer(producto_nuevo)
            return Response({
                'message': 'Producto duplicado exitosamente',
                'producto_original': {
                    'id': str(producto_original.id),
                    'codigo': producto_original.codigo,
                    'nombre': producto_original.nombre
                },
                'producto_nuevo': serializer.data
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error duplicando producto: {str(e)}", extra={
                'action': 'duplicar_producto',
                'error': str(e)
            })
            return Response(
                {'error': f'Error al duplicar producto: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='inventario-total')
    def inventario_total(self, request, pk=None):
        """
        Ver resumen de inventario del producto en todas las bodegas.
        GET /api/productos/{id}/inventario-total/
        Permiso: view_producto

        Retorna stock por bodega, stock total, reservado, disponible.
        """
        try:
            self.verificar_permiso('view_producto')

            producto = self.get_object()

            # Obtener stock
            from apps.inventario.models import Stock
            from django.db.models import Sum, F

            inventarios = Stock.objects.filter(
                producto=producto
            ).select_related('bodega', 'ubicacion')

            # Si el usuario no puede ver todas las bodegas, filtrar
            if not request.user.has_perm('inventario.view_stock_todas_bodegas'):
                from apps.inventario.models import Bodega
                bodegas_usuario = Bodega.objects.filter(
                    responsable__usuario=request.user
                ).values_list('id', flat=True)
                inventarios = inventarios.filter(bodega_id__in=bodegas_usuario)

            # Construir datos por bodega
            bodegas_data = []
            for inv in inventarios:
                bodegas_data.append({
                    'bodega': {
                        'id': str(inv.bodega.id),
                        'codigo': inv.bodega.codigo,
                        'nombre': inv.bodega.nombre,
                        'es_principal': inv.bodega.es_principal,
                        'permite_ventas': inv.bodega.permite_ventas
                    },
                    'ubicacion': {
                        'id': str(inv.ubicacion.id) if inv.ubicacion else None,
                        'nombre': f"{inv.ubicacion.pasillo}-{inv.ubicacion.estante}-{inv.ubicacion.nivel}" if inv.ubicacion else 'Sin ubicación'
                    } if inv.ubicacion else None,
                    'cantidad': inv.cantidad,
                    'stock_reservado': inv.stock_reservado,
                    'stock_disponible': inv.stock_disponible,
                    'estado': self._get_estado_stock(inv.cantidad, producto.stock_minimo)
                })

            # Calcular totales
            totales = inventarios.aggregate(
                total_stock=Sum('cantidad'),
                total_reservado=Sum('stock_reservado'),
                total_bodegas=Count('id')
            )

            stock_total = totales['total_stock'] or 0
            stock_reservado = totales['total_reservado'] or 0
            stock_disponible = stock_total - stock_reservado

            # Valorización (si tiene permiso)
            valorizacion = None
            if request.user.has_perm('inventario.view_stock_valorizado'):
                valorizacion = {
                    'valor_compra': float(stock_total * producto.precio_compra),
                    'valor_venta': float(stock_total * producto.precio_venta),
                    'utilidad_potencial': float(stock_total * (producto.precio_venta - producto.precio_compra))
                }

            return Response({
                'producto': {
                    'id': str(producto.id),
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'stock_minimo': producto.stock_minimo
                },
                'resumen': {
                    'total_bodegas': totales['total_bodegas'],
                    'stock_total': stock_total,
                    'stock_reservado': stock_reservado,
                    'stock_disponible': stock_disponible,
                    'estado_general': self._get_estado_stock(stock_total, producto.stock_minimo),
                    'necesita_reposicion': stock_total <= producto.stock_minimo
                },
                'valorizacion': valorizacion,
                'por_bodega': bodegas_data
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error obteniendo inventario total: {str(e)}", extra={
                'action': 'inventario_total',
                'error': str(e)
            })
            return Response(
                {'error': 'Error al obtener inventario total'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== FUNCIONES ADICIONALES PARA ProductoViewSet ====================

    def _get_estado_stock(self, cantidad, stock_minimo):
        """Helper para determinar estado del stock"""
        if cantidad == 0:
            return 'sin_stock'
        elif cantidad <= stock_minimo / 2:
            return 'critico'
        elif cantidad <= stock_minimo:
            return 'bajo'
        else:
            return 'normal'