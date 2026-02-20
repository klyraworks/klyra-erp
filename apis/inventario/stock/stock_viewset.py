import logging
from urllib import request

from django.db import transaction
from django.db.models import Q, F, Sum, Count
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import Stock, Bodega, Producto, MovimientoInventario, DetalleMovimiento, Ubicacion
from apis.inventario.stock.stock_serializer import InventarioBodegaListSerializer, StockSerializer
from apps.seguridad.models import Empleado


class StockViewSet(TenantViewSet):
    """
    ViewSet para consulta y gestión de stock por bodega.

    Endpoints:
        GET  /api/stock/                        - Listar todo el stock
        GET  /api/stock/{id}/                   - Detalle de un registro
        GET  /api/stock/alertas/                - Conteo de alertas
        GET  /api/stock/por_bodega/             - Stock agrupado por bodega
        GET  /api/stock/valorizado/             - Valor monetario del inventario
        POST /api/stock/{id}/ajustar_stock/     - Ajuste manual con movimiento
        POST /api/stock/{id}/cambiar_ubicacion/ - Cambiar ubicación en bodega
        POST /api/stock/{id}/reservar_stock/    - Reservar/liberar stock

    Permisos:
        - ver_stock:              GET (list, retrieve, alertas, por_bodega)
        - view_stock_valorizado:  GET valorizado
        - add_movimientoinventario: ajustar_stock, reservar_stock
        - editar_stock:           cambiar_ubicacion
    """

    # ==================== CONFIGURACIÓN ====================
    logger           = logging.getLogger('apps.inventario')
    queryset         = Stock.objects.all()
    serializer_class = InventarioBodegaListSerializer
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StockSerializer
        return InventarioBodegaListSerializer

    ordering        = ['bodega__nombre', 'producto__nombre']
    search_fields   = ['producto__codigo', 'producto__nombre', 'bodega__nombre']

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'producto', 'producto__categoria', 'producto__marca', 'producto__unidad_medida',
            'bodega', 'bodega__responsable__persona',
            'ubicacion',
        )

        if not self.request.user.has_perm('inventario.view_stock_todas_bodegas'):
            queryset = queryset.filter(bodega__responsable__usuario=self.request.user)

        return queryset

    # ==================== CRUD ====================

    @requiere_permiso('ver_stock')
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            bodega_id    = request.query_params.get('bodega_id')
            producto_id  = request.query_params.get('producto_id')
            categoria_id = request.query_params.get('categoria_id')
            search       = request.query_params.get('search')
            solo_con_stock = request.query_params.get('solo_con_stock', 'false')

            if bodega_id:
                queryset = queryset.filter(bodega_id=bodega_id)
            if producto_id:
                queryset = queryset.filter(producto_id=producto_id)
            if categoria_id:
                queryset = queryset.filter(producto__categoria_id=categoria_id)
            if solo_con_stock.lower() == 'true':
                queryset = queryset.filter(cantidad__gt=0)
            if search:
                queryset = queryset.filter(
                    Q(producto__codigo__icontains=search) |
                    Q(producto__nombre__icontains=search) |
                    Q(bodega__nombre__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)
        except Exception as e:
            self.logger.error(f"Error al listar stock: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener stock",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @requiere_permiso('ver_stock')
    def retrieve(self, request, *args, **kwargs):
        try:
            instancia = self.get_object()
            return StandardResponse.success(
                data=StockSerializer(instancia, context={'request': request}).data
            )
        except Exception as e:
            self.logger.error(f"Error al obtener stock: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener stock",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_stock')
    def alertas(self, request):
        """GET /api/stock/alertas/"""
        try:
            queryset = self.get_queryset()
            return StandardResponse.success(data={
                'sin_stock': queryset.filter(cantidad=0).count(),
                'critico': queryset.filter(
                    cantidad__gt=0,
                    cantidad__lte=F('producto__stock_minimo') / 2
                ).count(),
                'bajo': queryset.filter(
                    cantidad__gt=F('producto__stock_minimo') / 2,
                    cantidad__lte=F('producto__stock_minimo')
                ).count(),
                'con_reservas': queryset.filter(stock_reservado__gt=0).count(),
            })
        except Exception as e:
            self.logger.error(f"Error en alertas: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener alertas",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('ver_stock')
    def por_bodega(self, request):
        """GET /api/stock/por_bodega/"""
        try:
            bodegas = Bodega.objects.filter(
                empresa=request.empresa, is_active=True, deleted_at__isnull=True
            )
            if not request.user.has_perm('inventario.view_stock_todas_bodegas'):
                bodegas = bodegas.filter(responsable__usuario=request.user)

            resultado = []
            for bodega in bodegas:
                stats = self.get_queryset().filter(bodega=bodega).aggregate(
                    total_productos=Count('id'),
                    total_stock=Sum('cantidad'),
                    stock_disponible=Sum(F('cantidad') - F('stock_reservado')),
                )
                resultado.append({
                    'bodega_id': str(bodega.id),
                    'bodega_nombre': bodega.nombre,
                    'bodega_codigo': bodega.codigo,
                    'es_principal': bodega.es_principal,
                    'total_productos': stats['total_productos'] or 0,
                    'total_stock': stats['total_stock'] or 0,
                    'stock_disponible': stats['stock_disponible'] or 0,
                })

            return StandardResponse.success(data={
                'total_bodegas': len(resultado),
                'bodegas': resultado,
            })
        except Exception as e:
            self.logger.error(f"Error en por_bodega: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al agrupar stock por bodega",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @requiere_permiso('view_stock_valorizado')
    def valorizado(self, request):
        """GET /api/stock/valorizado/"""
        try:
            queryset = self.get_queryset()
            bodega_id = request.query_params.get('bodega_id')
            if bodega_id:
                queryset = queryset.filter(bodega_id=bodega_id)

            resultado = queryset.annotate(
                valor_compra=F('cantidad') * F('producto__precio_compra'),
                valor_venta=F('cantidad') * F('producto__precio_venta'),
            ).aggregate(
                total_productos=Count('id'),
                total_unidades=Sum('cantidad'),
                valor_total_compra=Sum('valor_compra'),
                valor_total_venta=Sum('valor_venta'),
            )

            valor_compra = float(resultado['valor_total_compra'] or 0)
            valor_venta  = float(resultado['valor_total_venta'] or 0)

            return StandardResponse.success(data={
                'total_productos': resultado['total_productos'] or 0,
                'total_unidades': resultado['total_unidades'] or 0,
                'valor_compra': valor_compra,
                'valor_venta': valor_venta,
                'utilidad_potencial': valor_venta - valor_compra,
            })
        except Exception as e:
            self.logger.error(f"Error en valorizado: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al calcular inventario valorizado",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('add_movimientoinventario')
    def ajustar_stock(self, request, pk=None):
        """
        POST /api/stock/{id}/ajustar_stock/
        Body: {cantidad, tipo: incremento|decremento|establecer, motivo, referencia?}
        """
        try:
            inventario = self.get_object()
            cantidad   = request.data.get('cantidad')
            tipo       = request.data.get('tipo', 'establecer')
            motivo     = request.data.get('motivo', '').strip()
            referencia = request.data.get('referencia', '').strip()

            if cantidad is None:
                return StandardResponse.validation_error({'cantidad': ['Este campo es requerido.']})
            if not motivo:
                return StandardResponse.validation_error({'motivo': ['Este campo es requerido.']})
            if tipo not in ['incremento', 'decremento', 'establecer']:
                return StandardResponse.validation_error({'tipo': ['Debe ser incremento, decremento o establecer.']})

            try:
                cantidad = int(cantidad)
                if cantidad < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return StandardResponse.validation_error({'cantidad': ['Debe ser un número entero no negativo.']})

            stock_anterior = inventario.cantidad

            if tipo == 'establecer':
                if cantidad == stock_anterior:
                    return StandardResponse.info(mensaje="El stock ya tiene ese valor.")
                tipo_movimiento   = 'entrada' if cantidad > stock_anterior else 'salida'
                cantidad_movimiento = abs(cantidad - stock_anterior)
            elif tipo == 'incremento':
                tipo_movimiento     = 'entrada'
                cantidad_movimiento = cantidad
            else:  # decremento
                if stock_anterior < cantidad:
                    return StandardResponse.error(
                        mensaje=f"Stock insuficiente. Stock actual: {stock_anterior}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                tipo_movimiento     = 'salida'
                cantidad_movimiento = cantidad

            with transaction.atomic():
                movimiento = MovimientoInventario.objects.create(
                    tipo=tipo_movimiento,
                    bodega_origen=inventario.bodega if tipo_movimiento == 'salida' else None,
                    bodega_destino=inventario.bodega if tipo_movimiento == 'entrada' else None,
                    referencia=referencia or f'AJUSTE-{inventario.producto.codigo}',
                    observaciones=f'Ajuste manual: {motivo}',
                    responsable=request.empleado,
                    empresa=request.empresa,
                )
                detalle = DetalleMovimiento.objects.create(
                    movimiento=movimiento,
                    producto=inventario.producto,
                    cantidad=cantidad_movimiento,
                    costo_unitario=inventario.producto.precio_compra,
                    stock_anterior=stock_anterior,
                    observaciones=motivo,
                    empresa=request.empresa,
                )

                if tipo_movimiento == 'entrada':
                    inventario.cantidad += cantidad_movimiento
                else:
                    inventario.cantidad -= cantidad_movimiento
                inventario.save()

                detalle.stock_posterior = inventario.cantidad
                detalle.save()

            self.logger.info(
                f"Stock ajustado | Stock={inventario.id} | Anterior={stock_anterior} | Nuevo={inventario.cantidad} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data={
                    'stock_anterior': stock_anterior,
                    'stock_actual': inventario.cantidad,
                    'cantidad_movimiento': cantidad_movimiento,
                    'tipo_movimiento': tipo_movimiento,
                    'movimiento': {'id': str(movimiento.id), 'numero': movimiento.numero},
                },
                mensaje="Stock ajustado exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error en ajustar_stock: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al ajustar stock",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('editar_stock')
    def cambiar_ubicacion(self, request, pk=None):
        """
        POST /api/stock/{id}/cambiar_ubicacion/
        Body: {ubicacion_id, motivo?}
        """
        try:
            inventario   = self.get_object()
            ubicacion_id = request.data.get('ubicacion_id')

            if not ubicacion_id:
                return StandardResponse.validation_error({'ubicacion_id': ['Este campo es requerido.']})

            try:
                nueva_ubicacion = Ubicacion.objects.get(id=ubicacion_id, empresa=request.empresa)
            except Ubicacion.DoesNotExist:
                return StandardResponse.error(
                    mensaje="Ubicación no encontrada",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            if nueva_ubicacion.bodega_id != inventario.bodega_id:
                return StandardResponse.error(
                    mensaje="La ubicación no pertenece a esta bodega",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if inventario.ubicacion_id == nueva_ubicacion.id:
                return StandardResponse.error(
                    mensaje="El producto ya está en esa ubicación",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            ubicacion_anterior = (
                f"{inventario.ubicacion.pasillo}-{inventario.ubicacion.estante}-{inventario.ubicacion.nivel}"
                if inventario.ubicacion else 'Sin ubicación'
            )
            inventario.ubicacion = nueva_ubicacion
            inventario.save()

            self.logger.info(
                f"Ubicación cambiada | Stock={inventario.id} | Anterior={ubicacion_anterior} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data={
                    'ubicacion_anterior': ubicacion_anterior,
                    'ubicacion_nueva': f"{nueva_ubicacion.pasillo}-{nueva_ubicacion.estante}-{nueva_ubicacion.nivel}",
                },
                mensaje="Ubicación actualizada exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error en cambiar_ubicacion: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al cambiar ubicación",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @requiere_permiso('add_movimientoinventario')
    def reservar_stock(self, request, pk=None):
        """
        POST /api/stock/{id}/reservar_stock/
        Body: {cantidad, tipo: reservar|liberar, referencia?, motivo?}
        """
        try:
            inventario = self.get_object()
            cantidad   = request.data.get('cantidad')
            tipo       = request.data.get('tipo', 'reservar')
            referencia = request.data.get('referencia', '').strip()
            motivo     = request.data.get('motivo', '').strip()

            if cantidad is None:
                return StandardResponse.validation_error({'cantidad': ['Este campo es requerido.']})
            if tipo not in ['reservar', 'liberar']:
                return StandardResponse.validation_error({'tipo': ['Debe ser reservar o liberar.']})

            try:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return StandardResponse.validation_error({'cantidad': ['Debe ser un número entero mayor a 0.']})

            if not referencia:
                referencia = Stock._generar_referencia_reserva(tipo)

            reservado_anterior = inventario.stock_reservado

            if tipo == 'reservar':
                disponible = inventario.cantidad - inventario.stock_reservado
                if disponible < cantidad:
                    return StandardResponse.error(
                        mensaje=f"Stock disponible insuficiente. Disponible: {disponible}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                inventario.stock_reservado += cantidad
            else:
                if inventario.stock_reservado < cantidad:
                    return StandardResponse.error(
                        mensaje=f"Stock reservado insuficiente. Reservado: {inventario.stock_reservado}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                inventario.stock_reservado -= cantidad

            inventario.save()

            self.logger.info(
                f"Stock {'reservado' if tipo == 'reservar' else 'liberado'} | Stock={inventario.id} | Cantidad={cantidad} | Usuario={request.user.id}"
            )
            return StandardResponse.success(
                data={
                    'tipo': tipo,
                    'cantidad': cantidad,
                    'referencia': referencia,
                    'stock_total': inventario.cantidad,
                    'reservado_anterior': reservado_anterior,
                    'reservado_actual': inventario.stock_reservado,
                    'disponible': inventario.cantidad - inventario.stock_reservado,
                },
                mensaje=f"Stock {'reservado' if tipo == 'reservar' else 'liberado'} exitosamente"
            )
        except Exception as e:
            self.logger.error(f"Error en reservar_stock: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al gestionar reserva de stock",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )