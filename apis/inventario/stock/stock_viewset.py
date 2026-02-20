# apis/inventario/stock/inventario_bodega_viewset.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Sum, F, Count
from django.db.models.functions import Coalesce

from apps.inventario.models import Stock, Bodega, Producto
from apis.inventario.stock.stock_serializer import (
    StockSerializer,
    InventarioBodegaListSerializer
)
from utils.mixins.permissions import PermissionCheckMixin
from apis.core.ViewSetBase import TenantViewSet

import logging


class StockViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet READ-ONLY para consultar inventario actual.

    IMPORTANTE: Este modelo NO se edita directamente.
    Las actualizaciones se hacen únicamente via MovimientoInventario.

    Permisos:
    - view_stock_todas_bodegas: Ver inventario (Todos)
    - view_stock_todas_bodegas: Ver todas las bodegas (Gerente)
    - view_stock_valorizado: Ver valores monetarios (Supervisor+)
    """
    queryset = Stock.objects.select_related(
        'producto', 'bodega', 'ubicacion',
        'producto__categoria', 'producto__marca'
    ).all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('inventario_bodega_viewset')

    # ==================== SERIALIZER ====================

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return InventarioBodegaListSerializer
        return StockSerializer

    # ==================== QUERYSET ====================

    def get_queryset(self):
        """Filtrar inventario según permisos del usuario"""
        queryset = super().get_queryset()

        # Si no puede ver todas las bodegas, filtrar por sus bodegas asignadas
        if not self.request.user.has_perm('inventario.view_stock_todas_bodegas'):
            bodegas_usuario = Bodega.objects.filter(
                responsable__usuario=self.request.user
            ).values_list('id', flat=True)

            queryset = queryset.filter(bodega_id__in=bodegas_usuario)

        return queryset

    # ==================== CRUD (Solo GET) ====================

    def list(self, request, *args, **kwargs):
        """
        Listar inventario con filtros.
        Permiso: view_stock_todas_bodegas
        """
        try:
            self.verificar_permiso('view_stock_todas_bodegas')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por bodega
            bodega_id = request.query_params.get('bodega_id')
            if bodega_id:
                queryset = queryset.filter(bodega_id=bodega_id)

            # Filtro por producto
            producto_id = request.query_params.get('producto_id')
            if producto_id:
                queryset = queryset.filter(producto_id=producto_id)

            # Filtro por categoría
            categoria_id = request.query_params.get('categoria_id')
            if categoria_id:
                queryset = queryset.filter(producto__categoria_id=categoria_id)

            # Filtro stock > 0
            solo_con_stock = request.query_params.get('solo_con_stock', 'false')
            if solo_con_stock.lower() == 'true':
                queryset = queryset.filter(cantidad__gt=0)

            # Búsqueda
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(producto__codigo__icontains=search) |
                    Q(producto__nombre__icontains=search) |
                    Q(bodega__nombre__icontains=search)
                )

            queryset = queryset.order_by('bodega__nombre', 'producto__nombre')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error listando inventario: {str(e)}")
            return Response(
                {'error': 'Error al obtener inventario'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalle de inventario específico.
        Permiso: view_stock_todas_bodegas
        """
        try:
            self.verificar_permiso('view_stock_todas_bodegas')
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Inventario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['get'], url_path='stock-bajo')
    def stock_bajo(self, request):
        """
        Productos con stock bajo o crítico.
        GET /api/stock/stock-bajo/
        """
        try:
            self.verificar_permiso('view_stock_todas_bodegas')

            queryset = self.get_queryset().filter(
                cantidad__gt=0,
                cantidad__lte=F('producto__stock_minimo')
            ).select_related('producto', 'bodega')

            serializer = self.get_serializer(queryset, many=True)

            return Response({
                'total': queryset.count(),
                'productos': serializer.data
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error obteniendo stock bajo: {str(e)}")
            return Response(
                {'error': 'Error al obtener stock bajo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='por-bodega')
    def por_bodega(self, request):
        """
        Inventario agrupado por bodega.
        GET /api/stock/por-bodega/
        """
        try:
            self.verificar_permiso('view_stock_todas_bodegas')

            bodegas = Bodega.objects.filter(is_active=True)

            # Filtrar por bodegas del usuario si no es gerente
            if not request.user.has_perm('inventario.view_stock_todas_bodegas'):
                bodegas = bodegas.filter(responsable__usuario=request.user)

            resultado = []
            for bodega in bodegas:
                inventario = self.get_queryset().filter(bodega=bodega)

                stats = inventario.aggregate(
                    total_productos=Count('id'),
                    total_stock=Sum('cantidad'),
                    stock_disponible=Sum(F('cantidad') - F('stock_reservado'))
                )

                resultado.append({
                    'bodega_id': bodega.id,
                    'bodega_nombre': bodega.nombre,
                    'bodega_codigo': bodega.codigo,
                    'total_productos': stats['total_productos'] or 0,
                    'total_stock': stats['total_stock'] or 0,
                    'stock_disponible': stats['stock_disponible'] or 0
                })

            return Response({
                'total_bodegas': len(resultado),
                'bodegas': resultado
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error agrupando por bodega: {str(e)}")
            return Response(
                {'error': 'Error al agrupar inventario'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='valorizado')
    def valorizado(self, request):
        """
        Valor total del inventario.
        GET /api/stock/valorizado/
        Permiso: view_stock_valorizado
        """
        try:
            self.verificar_permiso(
                'view_stock_valorizado',
                'No tiene permisos para ver valores monetarios'
            )

            queryset = self.get_queryset()

            # Filtro por bodega
            bodega_id = request.query_params.get('bodega_id')
            if bodega_id:
                queryset = queryset.filter(bodega_id=bodega_id)

            # Calcular valores
            valorizado = queryset.annotate(
                valor_compra=F('cantidad') * F('producto__precio_compra'),
                valor_venta=F('cantidad') * F('producto__precio_venta')
            ).aggregate(
                total_productos=Count('id'),
                total_unidades=Sum('cantidad'),
                valor_total_compra=Sum('valor_compra'),
                valor_total_venta=Sum('valor_venta')
            )

            return Response({
                'total_productos': valorizado['total_productos'] or 0,
                'total_unidades': valorizado['total_unidades'] or 0,
                'valor_compra': float(valorizado['valor_total_compra'] or 0),
                'valor_venta': float(valorizado['valor_total_venta'] or 0),
                'utilidad_potencial': float(
                    (valorizado['valor_total_venta'] or 0) -
                    (valorizado['valor_total_compra'] or 0)
                )
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error calculando valorizado: {str(e)}")
            return Response(
                {'error': 'Error al calcular valor del inventario'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='alertas')
    def alertas(self, request):
        """
        Alertas de inventario (stock crítico, sin stock, etc).
        GET /api/stock/alertas/
        """
        try:
            self.verificar_permiso('view_stock_todas_bodegas')

            queryset = self.get_queryset()

            alertas = {
                'sin_stock': queryset.filter(cantidad=0).count(),
                'stock_critico': queryset.filter(
                    cantidad__gt=0,
                    cantidad__lte=F('producto__stock_minimo') / 2
                ).count(),
                'stock_bajo': queryset.filter(
                    cantidad__gt=F('producto__stock_minimo') / 2,
                    cantidad__lte=F('producto__stock_minimo')
                ).count(),
                'con_reservas': queryset.filter(stock_reservado__gt=0).count()
            }

            return Response(alertas)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error obteniendo alertas: {str(e)}")
            return Response(
                {'error': 'Error al obtener alertas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='ajustar-stock')
    def ajustar_stock(self, request, pk=None):
        """
        Ajustar stock manualmente en una bodega específica.
        POST /api/stock/{id}/ajustar-stock/

        Body: {
            "cantidad": 10,
            "tipo": "incremento|decremento|establecer",
            "motivo": "Ajuste por inventario físico",
            "referencia": "INV-2024-001" (opcional)
        }

        Permiso: add_movimientoinventario

        IMPORTANTE: Este método crea un MovimientoInventario automáticamente.
        """
        try:
            self.verificar_permiso(
                'add_movimientoinventario',
                'No tienes permiso para ajustar stock'
            )

            inventario = self.get_object()

            # Validar datos
            cantidad = request.data.get('cantidad')
            tipo = request.data.get('tipo', 'establecer')
            motivo = request.data.get('motivo', '').strip()
            referencia = request.data.get('referencia', '').strip()

            if not cantidad:
                return Response(
                    {'error': 'Se requiere el campo "cantidad"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not motivo:
                return Response(
                    {'error': 'Se requiere el campo "motivo"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                cantidad = int(cantidad)
                if cantidad < 0:
                    raise ValueError("La cantidad no puede ser negativa")
            except ValueError as e:
                return Response(
                    {'error': f'Cantidad inválida: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if tipo not in ['incremento', 'decremento', 'establecer']:
                return Response(
                    {'error': 'Tipo debe ser "incremento", "decremento" o "establecer"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calcular cantidad de movimiento según tipo
            stock_anterior = inventario.cantidad

            if tipo == 'establecer':
                # Establecer cantidad exacta
                if cantidad == stock_anterior:
                    return Response({
                        'message': 'El stock ya tiene ese valor',
                        'stock_actual': stock_anterior
                    })

                # Determinar si es entrada o salida
                if cantidad > stock_anterior:
                    tipo_movimiento = 'entrada'
                    cantidad_movimiento = cantidad - stock_anterior
                else:
                    tipo_movimiento = 'salida'
                    cantidad_movimiento = stock_anterior - cantidad

            elif tipo == 'incremento':
                tipo_movimiento = 'entrada'
                cantidad_movimiento = cantidad

            else:  # decremento
                if stock_anterior < cantidad:
                    return Response(
                        {'error': f'Stock insuficiente. Stock actual: {stock_anterior}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                tipo_movimiento = 'salida'
                cantidad_movimiento = cantidad

            # Crear movimiento de inventario
            from apps.inventario.models import MovimientoInventario, DetalleMovimiento
            from django.db import transaction

            with transaction.atomic():
                # Determinar bodega origen/destino según tipo
                if tipo_movimiento == 'entrada':
                    bodega_destino = inventario.bodega
                    bodega_origen = None
                else:
                    bodega_origen = inventario.bodega
                    bodega_destino = None

                # Crear movimiento
                movimiento = MovimientoInventario.objects.create(
                    tipo=tipo_movimiento,
                    bodega_origen=bodega_origen,
                    bodega_destino=bodega_destino,
                    referencia=referencia or f'AJUSTE-{inventario.producto.codigo}',
                    observaciones=f'Ajuste manual: {motivo}',
                    responsable=request.user,
                    empresa=inventario.empresa
                )

                # Crear detalle
                detalle = DetalleMovimiento.objects.create(
                    movimiento=movimiento,
                    producto=inventario.producto,
                    cantidad=cantidad_movimiento,
                    costo_unitario=inventario.producto.precio_compra,
                    stock_anterior=stock_anterior,
                    observaciones=motivo,
                    empresa=inventario.empresa
                )

                # Actualizar stock en Stock
                if tipo_movimiento == 'entrada':
                    inventario.cantidad += cantidad_movimiento
                else:
                    inventario.cantidad -= cantidad_movimiento

                inventario.save()

                # Actualizar stock_posterior en detalle
                detalle.stock_posterior = inventario.cantidad
                detalle.save()

                # Actualizar stock total del producto
                from django.db.models import Sum
                stock_total = Stock.objects.filter(
                    producto=inventario.producto
                ).aggregate(total=Sum('cantidad'))['total'] or 0

                inventario.producto.stock = stock_total
                inventario.producto.save()

            self.logger.info(
                f"Stock ajustado por {request.user.username}",
                extra={
                    'inventario_id': inventario.id,
                    'producto_codigo': inventario.producto.codigo,
                    'bodega_codigo': inventario.bodega.codigo,
                    'stock_anterior': stock_anterior,
                    'stock_nuevo': inventario.cantidad,
                    'tipo': tipo,
                    'tipo_movimiento': tipo_movimiento,
                    'cantidad_movimiento': cantidad_movimiento,
                    'motivo': motivo,
                    'movimiento_id': movimiento.id,
                    'ajustado_por': request.user.username,
                    'action': 'ajustar_stock_bodega'
                }
            )

            return Response({
                'message': f'Stock ajustado exitosamente',
                'ajuste': {
                    'tipo': tipo,
                    'tipo_movimiento': tipo_movimiento,
                    'cantidad_movimiento': cantidad_movimiento,
                    'stock_anterior': stock_anterior,
                    'stock_actual': inventario.cantidad,
                    'motivo': motivo
                },
                'movimiento': {
                    'id': str(movimiento.id),
                    'numero': movimiento.numero,
                    'tipo': movimiento.tipo
                }
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error ajustando stock: {str(e)}", extra={
                'action': 'ajustar_stock_bodega',
                'error': str(e)
            })
            return Response(
                {'error': f'Error al ajustar stock: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='cambiar-ubicacion')
    def cambiar_ubicacion(self, request, pk=None):
        """
        Cambiar ubicación del producto dentro de la bodega.
        POST /api/stock/{id}/cambiar-ubicacion/

        Body: {
            "ubicacion_id": "uuid-de-ubicacion",
            "motivo": "Reubicación por reorganización" (opcional)
        }

        Permiso: change_inventariobodega
        """
        try:
            self.verificar_permiso(
                'change_inventariobodega',
                'No tienes permiso para cambiar ubicaciones'
            )

            inventario = self.get_object()
            ubicacion_id = request.data.get('ubicacion_id')
            motivo = request.data.get('motivo', 'Cambio de ubicación')

            if not ubicacion_id:
                return Response(
                    {'error': 'Se requiere el campo "ubicacion_id"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar que la ubicación existe y pertenece a la misma bodega
            from apps.inventario.models import Ubicacion
            try:
                nueva_ubicacion = Ubicacion.objects.get(id=ubicacion_id)
            except Ubicacion.DoesNotExist:
                return Response(
                    {'error': 'Ubicación no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validar que pertenece a la misma bodega
            if nueva_ubicacion.bodega_id != inventario.bodega_id:
                return Response(
                    {'error': 'La ubicación no pertenece a esta bodega'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar que no es la misma ubicación
            if inventario.ubicacion_id == nueva_ubicacion.id:
                return Response(
                    {'error': 'El producto ya está en esa ubicación'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guardar ubicación anterior
            ubicacion_anterior = inventario.ubicacion
            ubicacion_anterior_nombre = f"{ubicacion_anterior.pasillo}-{ubicacion_anterior.estante}-{ubicacion_anterior.nivel}" if ubicacion_anterior else 'Sin ubicación'

            # Cambiar ubicación
            inventario.ubicacion = nueva_ubicacion
            inventario.save()

            self.logger.info(
                f"Ubicación cambiada por {request.user.username}",
                extra={
                    'inventario_id': inventario.id,
                    'producto_codigo': inventario.producto.codigo,
                    'bodega_codigo': inventario.bodega.codigo,
                    'ubicacion_anterior_id': str(ubicacion_anterior.id) if ubicacion_anterior else None,
                    'ubicacion_anterior': ubicacion_anterior_nombre,
                    'ubicacion_nueva_id': str(nueva_ubicacion.id),
                    'ubicacion_nueva': f"{nueva_ubicacion.pasillo}-{nueva_ubicacion.estante}-{nueva_ubicacion.nivel}",
                    'motivo': motivo,
                    'cambiado_por': request.user.username,
                    'action': 'cambiar_ubicacion'
                }
            )

            return Response({
                'message': 'Ubicación actualizada exitosamente',
                'producto': {
                    'codigo': inventario.producto.codigo,
                    'nombre': inventario.producto.nombre
                },
                'bodega': inventario.bodega.nombre,
                'ubicacion_anterior': ubicacion_anterior_nombre,
                'ubicacion_nueva': f"{nueva_ubicacion.pasillo}-{nueva_ubicacion.estante}-{nueva_ubicacion.nivel}",
                'motivo': motivo
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error cambiando ubicación: {str(e)}", extra={
                'action': 'cambiar_ubicacion',
                'error': str(e)
            })
            return Response(
                {'error': f'Error al cambiar ubicación: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='reservar-stock')
    def reservar_stock(self, request, pk=None):
        """
        Reservar stock para un pedido o venta pendiente.
        POST /api/stock/{id}/reservar-stock/

        Body: {
            "cantidad": 10,
            "tipo": "reservar|liberar",
            "referencia": "PEDIDO-001 o VENTA-123" (opcional - se genera automáticamente),
            "motivo": "Reserva para pedido cliente X" (opcional)
        }

        Permiso: add_movimientoinventario
        """
        try:
            self.verificar_permiso(
                'add_movimientoinventario',
                'No tienes permiso para reservar stock'
            )

            inventario = self.get_object()

            # Validar datos
            cantidad = request.data.get('cantidad')
            tipo = request.data.get('tipo', 'reservar')
            referencia = request.data.get('referencia', '').strip()
            motivo = request.data.get('motivo', '').strip()

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

            if tipo not in ['reservar', 'liberar']:
                return Response(
                    {'error': 'Tipo debe ser "reservar" o "liberar"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generar referencia automática si no se proporciona usando el método del modelo
            referencia_autogenerada = False
            if not referencia:
                referencia = Stock._generar_referencia_reserva(tipo)
                referencia_autogenerada = True

            # Validaciones según tipo
            reservado_anterior = inventario.stock_reservado

            if tipo == 'reservar':
                # Validar que hay stock disponible suficiente
                stock_disponible = inventario.stock_disponible

                if stock_disponible < cantidad:
                    return Response(
                        {
                            'error': f'Stock disponible insuficiente. Disponible: {stock_disponible}, Solicitado: {cantidad}',
                            'stock_total': inventario.cantidad,
                            'stock_reservado': inventario.stock_reservado,
                            'stock_disponible': stock_disponible
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Reservar
                inventario.stock_reservado += cantidad

            else:  # liberar
                # Validar que hay suficiente stock reservado para liberar
                if inventario.stock_reservado < cantidad:
                    return Response(
                        {
                            'error': f'No hay suficiente stock reservado para liberar. Reservado: {inventario.stock_reservado}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Liberar
                inventario.stock_reservado -= cantidad

            inventario.save()

            self.logger.info(
                f"Stock {'reservado' if tipo == 'reservar' else 'liberado'} por {request.user.username}",
                extra={
                    'inventario_id': inventario.id,
                    'producto_codigo': inventario.producto.codigo,
                    'bodega_codigo': inventario.bodega.codigo,
                    'tipo': tipo,
                    'cantidad': cantidad,
                    'reservado_anterior': reservado_anterior,
                    'reservado_actual': inventario.stock_reservado,
                    'stock_total': inventario.cantidad,
                    'stock_disponible': inventario.stock_disponible,
                    'referencia': referencia,
                    'referencia_autogenerada': referencia_autogenerada,
                    'motivo': motivo or None,
                    'gestionado_por': request.user.username,
                    'action': 'reservar_stock'
                }
            )

            return Response({
                'message': f'Stock {"reservado" if tipo == "reservar" else "liberado"} exitosamente',
                'producto': {
                    'codigo': inventario.producto.codigo,
                    'nombre': inventario.producto.nombre
                },
                'bodega': inventario.bodega.nombre,
                'reserva': {
                    'tipo': tipo,
                    'cantidad': cantidad,
                    'referencia': referencia,
                    'referencia_autogenerada': referencia_autogenerada,
                    'motivo': motivo or None
                },
                'stock': {
                    'total': inventario.cantidad,
                    'reservado_anterior': reservado_anterior,
                    'reservado_actual': inventario.stock_reservado,
                    'disponible': inventario.stock_disponible
                }
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error gestionando reserva de stock: {str(e)}", extra={
                'action': 'reservar_stock',
                'error': str(e)
            })
            return Response(
                {'error': f'Error al gestionar reserva: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )