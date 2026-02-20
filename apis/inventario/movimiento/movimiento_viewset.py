# apis/inventario/movimiento/movimiento_viewset.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum, Count, F
from apis.core.ViewSetBase import TenantViewSet
from django.utils import timezone
from datetime import timedelta, date

from apps.inventario.models import (
    MovimientoInventario,
    DetalleMovimiento,
    Stock,
    Producto,
    Bodega
)
from apps.seguridad.models import Empleado
from apis.inventario.movimiento.movimiento_serializer import MovimientoInventarioSerializer
from utils.mixins.permissions import PermissionCheckMixin

import logging


class MovimientoInventarioViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet para gestionar Movimientos de Inventario.

    Soporta:
    - Entradas (compras, devoluciones, ajustes positivos)
    - Salidas (ventas, devoluciones a proveedor, ajustes negativos)
    - Transferencias (entre bodegas)
    - Mermas y pérdidas

    Permisos:
    - view_movimientoinventario: Ver movimientos
    - add_movimientoinventario: Crear movimientos
    - autorizar_movimiento: Autorizar movimientos (Supervisor+)
    - ver_todos_movimientos: Ver movimientos de todas las bodegas (Gerente)
    """
    queryset = MovimientoInventario.objects.select_related(
        'bodega_origen', 'bodega_destino', 'responsable', 'autorizado_por'
    ).prefetch_related('detalles', 'detalles__producto').all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']  # NO permitir PUT/PATCH/DELETE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('movimiento_inventario_viewset')

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        """
        Filtrar movimientos por empresa y según permisos del usuario.
        Los usuarios solo ven movimientos de sus bodegas asignadas,
        excepto gerentes que ven todo.
        """
        # Aplicar filtro de tenant
        queryset = super().get_queryset()

        # Si el usuario no puede ver todos los movimientos, filtrar por bodegas
        if not self.request.user.has_perm('inventario.ver_todos_movimientos'):
            try:
                # Obtener empleado asociado al usuario
                empleado = Empleado.objects.get(usuario=self.request.user)
                # Obtener bodegas donde el usuario es responsable
                bodegas_usuario = Bodega.objects.filter(
                    Q(responsable=self.request.user)
                ).values_list('id', flat=True)

                queryset = queryset.filter(
                    Q(bodega_origen_id__in=bodegas_usuario) |
                    Q(bodega_destino_id__in=bodegas_usuario)
                )
            except Empleado.DoesNotExist:
                # Usuario sin empleado asociado
                queryset = queryset.none()

        return queryset

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        """
        Listar movimientos con filtros avanzados.
        Permiso: view_movimientoinventario
        """
        try:
            self.verificar_permiso('view_movimientoinventario')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por tipo
            tipo = request.query_params.get('tipo', None)
            if tipo:
                queryset = queryset.filter(tipo=tipo)

            # Filtro por bodega
            bodega_id = request.query_params.get('bodega_id', None)
            if bodega_id:
                queryset = queryset.filter(
                    Q(bodega_origen_id=bodega_id) |
                    Q(bodega_destino_id=bodega_id)
                )

            # Filtro por rango de fechas
            fecha_desde = request.query_params.get('fecha_desde', None)
            fecha_hasta = request.query_params.get('fecha_hasta', None)

            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)

            # Filtro por producto
            producto_id = request.query_params.get('producto_id', None)
            if producto_id:
                queryset = queryset.filter(detalles__producto_id=producto_id).distinct()

            # Filtro por número de movimiento o referencia
            search = request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(numero__icontains=search) |
                    Q(referencia__icontains=search) |
                    Q(observaciones__icontains=search)
                )

            # Ordenar por fecha descendente
            queryset = queryset.order_by('-fecha')

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
            self.logger.error(f"Error listando movimientos: {str(e)}")
            return Response(
                {'error': 'Error al obtener movimientos'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crear nuevo movimiento de inventario.
        Permiso: add_movimientoinventario
        """
        try:
            self.verificar_permiso('add_movimientoinventario')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            movimiento = serializer.save()

            self.logger.info(
                f"Movimiento creado por {request.user.username}: {movimiento.numero}",
                extra={
                    'movimiento_id': movimiento.id,
                    'numero': movimiento.numero,
                    'tipo': movimiento.tipo,
                    'creado_por': request.user.username
                }
            )

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error creando movimiento: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalle completo de un movimiento.
        Permiso: view_movimientoinventario
        """
        try:
            self.verificar_permiso('view_movimientoinventario')

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except MovimientoInventario.DoesNotExist:
            return Response(
                {'error': 'Movimiento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo movimiento: {str(e)}")
            return Response(
                {'error': 'Error al obtener el movimiento'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['post'], url_path='crear-entrada')
    def crear_entrada(self, request):
        """
        Atajo para crear entrada de inventario.
        POST /api/movimientos-inventario/crear-entrada/

        Body:
        {
            "bodega_destino_id": 1,
            "observaciones": "Compra a proveedor X",
            "detalles_data": [
                {
                    "producto_id": 1,
                    "cantidad": 100
                }
            ]
        }
        """
        try:
            self.verificar_permiso('add_movimientoinventario')

            data = request.data.copy()
            data['tipo'] = 'entrada'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            movimiento = serializer.save()

            return Response({
                'message': 'Entrada de inventario registrada exitosamente',
                'movimiento': serializer.data
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando entrada: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='crear-salida')
    def crear_salida(self, request):
        """
        Atajo para crear salida de inventario.
        POST /api/movimientos-inventario/crear-salida/
        """
        try:
            self.verificar_permiso('add_movimientoinventario')

            data = request.data.copy()
            data['tipo'] = 'salida'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            movimiento = serializer.save()

            return Response({
                'message': 'Salida de inventario registrada exitosamente',
                'movimiento': serializer.data
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando salida: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='crear-transferencia')
    def crear_transferencia(self, request):
        """
        Atajo para crear transferencia entre bodegas.
        POST /api/movimientos-inventario/crear-transferencia/
        """
        try:
            self.verificar_permiso('add_movimientoinventario')

            data = request.data.copy()
            data['tipo'] = 'transferencia'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            movimiento = serializer.save()

            return Response({
                'message': 'Transferencia registrada exitosamente',
                'movimiento': serializer.data
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando transferencia: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='anular')
    def anular(self, request, pk=None):
        """
        Anular un movimiento y revertir cambios en inventario.
        POST /api/movimientos-inventario/{id}/anular/

        Body: {"motivo": "Razón de anulación"}

        Permiso: autorizar_movimiento
        """
        try:
            self.verificar_permiso(
                'autorizar_movimiento',
                'Solo supervisores pueden anular movimientos'
            )

            movimiento = self.get_object()
            motivo = request.data.get('motivo', '').strip()

            if not motivo:
                return Response(
                    {'error': 'Debe proporcionar un motivo para anular'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Crear movimiento inverso para revertir
            from django.db import transaction

            with transaction.atomic():
                # Determinar tipo inverso
                tipo_inverso_map = {
                    'entrada': 'salida',
                    'salida': 'entrada',
                    'transferencia': 'transferencia'
                }

                tipo_inverso = tipo_inverso_map.get(movimiento.tipo)
                if not tipo_inverso:
                    return Response(
                        {'error': f'No se puede anular movimiento de tipo {movimiento.tipo}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Preparar datos para movimiento de anulación
                data_anulacion = {
                    'tipo': tipo_inverso,
                    'referencia': f'ANULACIÓN: {movimiento.numero}',
                    'observaciones': f'Anulación: {motivo}',
                    'detalles_data': []
                }

                # Invertir bodegas si es necesario
                if tipo_inverso == 'transferencia':
                    data_anulacion['bodega_origen_id'] = movimiento.bodega_destino_id
                    data_anulacion['bodega_destino_id'] = movimiento.bodega_origen_id
                elif tipo_inverso == 'entrada':
                    data_anulacion['bodega_destino_id'] = movimiento.bodega_origen_id
                else:  # salida
                    data_anulacion['bodega_origen_id'] = movimiento.bodega_destino_id

                # Copiar detalles
                for detalle in movimiento.detalles.all():
                    data_anulacion['detalles_data'].append({
                        'producto_id': detalle.producto_id,
                        'cantidad': detalle.cantidad,
                        'costo_unitario': detalle.costo_unitario,
                        'lote': detalle.lote,
                        'observaciones': f'Anulación de {movimiento.numero}'
                    })

                # Crear movimiento de anulación
                serializer = self.get_serializer(data=data_anulacion)
                serializer.is_valid(raise_exception=True)
                movimiento_anulacion = serializer.save()

                self.logger.info(
                    f"Movimiento anulado: {movimiento.numero} por {request.user.username}",
                    extra={
                        'movimiento_original': movimiento.id,
                        'movimiento_anulacion': movimiento_anulacion.id,
                        'motivo': motivo,
                        'anulado_por': request.user.username
                    }
                )

                return Response({
                    'message': 'Movimiento anulado exitosamente',
                    'movimiento_original': movimiento.numero,
                    'movimiento_anulacion': movimiento_anulacion.numero
                })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            self.logger.error(f"[Descripción del error para el developer...]: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error anulando movimiento: {str(e)}")
            return Response(
                {'error': f'Error al anular movimiento: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='kardex')
    def kardex(self, request):
        """
        Obtener kardex (historial de movimientos) de un producto en una bodega.
        GET /api/movimientos-inventario/kardex/?producto_id=1&bodega_id=1&fecha_desde=2024-01-01

        Permiso: view_movimientoinventario
        """
        try:
            self.verificar_permiso('view_movimientoinventario')

            producto_id = request.query_params.get('producto_id')
            bodega_id = request.query_params.get('bodega_id')

            if not producto_id:
                return Response(
                    {'error': 'Parámetro producto_id es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener producto
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                return Response(
                    {'error': 'Producto no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Construir query
            detalles = DetalleMovimiento.objects.filter(
                producto_id=producto_id
            ).select_related('movimiento', 'movimiento__bodega_origen', 'movimiento__bodega_destino')

            # Filtrar por bodega si se especifica
            if bodega_id:
                detalles = detalles.filter(
                    Q(movimiento__bodega_origen_id=bodega_id) |
                    Q(movimiento__bodega_destino_id=bodega_id)
                )

            # Filtrar por fecha
            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')

            if fecha_desde:
                detalles = detalles.filter(movimiento__fecha__gte=fecha_desde)
            if fecha_hasta:
                detalles = detalles.filter(movimiento__fecha__lte=fecha_hasta)

            detalles = detalles.order_by('movimiento__fecha')

            # Construir kardex
            kardex = []
            for detalle in detalles:
                mov = detalle.movimiento
                kardex.append({
                    'fecha': mov.fecha,
                    'numero': mov.numero,
                    'tipo': mov.tipo,
                    'tipo_display': mov.get_tipo_display(),
                    'bodega_origen': mov.bodega_origen.nombre if mov.bodega_origen else None,
                    'bodega_destino': mov.bodega_destino.nombre if mov.bodega_destino else None,
                    'cantidad': detalle.cantidad,
                    'stock_anterior': detalle.stock_anterior,
                    'stock_posterior': detalle.stock_posterior,
                    'costo_unitario': float(detalle.costo_unitario) if detalle.costo_unitario else None,
                    'lote': detalle.lote,
                    'referencia': mov.referencia,
                    'observaciones': detalle.observaciones or mov.observaciones
                })

            # Stock actual
            stock_actual = Stock.objects.filter(
                producto_id=producto_id
            )

            if bodega_id:
                stock_actual = stock_actual.filter(bodega_id=bodega_id)

            stock_info = stock_actual.aggregate(
                total=Sum('cantidad'),
                reservado=Sum('stock_reservado')
            )

            return Response({
                'producto': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'stock_actual': stock_info['total'] or 0,
                    'stock_reservado': stock_info['reservado'] or 0,
                    'stock_disponible': (stock_info['total'] or 0) - (stock_info['reservado'] or 0)
                },
                'kardex': kardex,
                'total_movimientos': len(kardex)
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error generando kardex: {str(e)}")
            return Response(
                {'error': 'Error al generar kardex'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        Obtener resumen de movimientos por período.
        GET /api/movimientos-inventario/resumen/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31

        Permiso: view_movimientoinventario
        """
        try:
            self.verificar_permiso('view_movimientoinventario')

            queryset = self.get_queryset()

            # Filtrar por fechas
            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')

            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)

            # Estadísticas por tipo
            resumen_tipo = queryset.values('tipo').annotate(
                total=Count('id'),
                productos=Sum('detalles__cantidad')
            ).order_by('tipo')

            # Total de movimientos
            total_movimientos = queryset.count()

            return Response({
                'periodo': {
                    'desde': fecha_desde,
                    'hasta': fecha_hasta
                },
                'total_movimientos': total_movimientos,
                'por_tipo': list(resumen_tipo)
            })

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error generando resumen: {str(e)}")
            return Response(
                {'error': 'Error al generar resumen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )