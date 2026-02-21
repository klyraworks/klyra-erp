# apis/inventario/movimiento/movimiento_viewset.py
import logging

from django.db import transaction
from django.db.models import Q, Sum, Count
from rest_framework import status
from rest_framework.decorators import action

from apis.core.ViewSetBase import TenantViewSet
from apis.core.response_handler import StandardResponse
from apps.core.decorators import requiere_permiso
from apps.inventario.models import (
    MovimientoInventario,
    DetalleMovimiento,
    Stock,
    Producto,
    Bodega,
)
from apis.inventario.movimiento.movimiento_serializer import MovimientoInventarioSerializer


class MovimientoInventarioViewSet(TenantViewSet):
    """
    ViewSet para gestión de movimientos de inventario.

    Endpoints:
        GET    /api/movimientos-inventario/                  - Listar
        POST   /api/movimientos-inventario/                  - Crear
        GET    /api/movimientos-inventario/{id}/             - Detalle
        POST   /api/movimientos-inventario/crear-entrada/    - Atajo entrada
        POST   /api/movimientos-inventario/crear-salida/     - Atajo salida
        POST   /api/movimientos-inventario/crear-transferencia/ - Atajo transferencia
        POST   /api/movimientos-inventario/{id}/anular/      - Anular movimiento
        GET    /api/movimientos-inventario/kardex/           - Kardex de producto
        GET    /api/movimientos-inventario/resumen/          - Resumen por período

    Permisos:
        - ver_movimiento_inventario:    GET (list, retrieve, kardex, resumen)
        - crear_movimiento_inventario:  POST (create, crear-entrada, crear-salida, crear-transferencia)
        - autorizar_movimiento:         POST (anular)
    """

    # ==================== CONFIGURACIÓN ====================
    logger            = logging.getLogger('apps.inventario')
    queryset          = MovimientoInventario.objects.all()
    serializer_class  = MovimientoInventarioSerializer
    http_method_names = ['get', 'post']

    ordering        = ['-fecha']
    ordering_fields = ['fecha', 'numero', 'tipo']
    search_fields   = ['numero', 'referencia', 'observaciones']

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'bodega_origen', 'bodega_destino',
            'responsable__persona', 'autorizado_por',
            'created_by', 'updated_by',
        ).prefetch_related(
            'detalles__producto__unidad_medida',
        )

        # Filtros via query params
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        bodega_id = self.request.query_params.get('bodega_id')
        if bodega_id:
            queryset = queryset.filter(
                Q(bodega_origen_id=bodega_id) | Q(bodega_destino_id=bodega_id)
            )

        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        producto_id = self.request.query_params.get('producto_id')
        if producto_id:
            queryset = queryset.filter(detalles__producto_id=producto_id).distinct()

        return queryset

    # ==================== CRUD OPERATIONS ====================

    @requiere_permiso('ver_movimiento_inventario')
    def list(self, request, *args, **kwargs):
        """Listar movimientos con filtros avanzados."""
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al listar movimientos: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener movimientos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('crear_movimiento_inventario')
    def create(self, request, *args, **kwargs):
        """Crear nuevo movimiento de inventario."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                movimiento = serializer.save()

            self.logger.info(
                f"Movimiento creado | Numero={movimiento.numero} | Tipo={movimiento.tipo} | "
                f"Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MovimientoInventarioSerializer(movimiento, context={'request': request}).data,
                mensaje="Movimiento registrado exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear movimiento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al crear movimiento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @requiere_permiso('ver_movimiento_inventario')
    def retrieve(self, request, *args, **kwargs):
        """Detalle de un movimiento."""
        try:
            instancia  = self.get_object()
            serializer = self.get_serializer(instancia)
            return StandardResponse.success(data=serializer.data)

        except Exception as e:
            self.logger.error(f"Error al obtener movimiento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al obtener el movimiento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=False, methods=['post'], url_path='crear-entrada')
    @requiere_permiso('crear_movimiento_inventario')
    def crear_entrada(self, request):
        """
        Atajo para crear entrada de inventario.
        POST /api/movimientos-inventario/crear-entrada/
        """
        try:
            data         = request.data.copy()
            data['tipo'] = 'entrada'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                movimiento = serializer.save()

            self.logger.info(
                f"Entrada creada | Numero={movimiento.numero} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MovimientoInventarioSerializer(movimiento, context={'request': request}).data,
                mensaje="Entrada de inventario registrada exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear entrada: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al registrar entrada de inventario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], url_path='crear-salida')
    @requiere_permiso('crear_movimiento_inventario')
    def crear_salida(self, request):
        """
        Atajo para crear salida de inventario.
        POST /api/movimientos-inventario/crear-salida/
        """
        try:
            data         = request.data.copy()
            data['tipo'] = 'salida'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                movimiento = serializer.save()

            self.logger.info(
                f"Salida creada | Numero={movimiento.numero} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MovimientoInventarioSerializer(movimiento, context={'request': request}).data,
                mensaje="Salida de inventario registrada exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear salida: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al registrar salida de inventario",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], url_path='crear-transferencia')
    @requiere_permiso('crear_movimiento_inventario')
    def crear_transferencia(self, request):
        """
        Atajo para crear transferencia entre bodegas.
        POST /api/movimientos-inventario/crear-transferencia/
        """
        try:
            data         = request.data.copy()
            data['tipo'] = 'transferencia'

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                movimiento = serializer.save()

            self.logger.info(
                f"Transferencia creada | Numero={movimiento.numero} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data=MovimientoInventarioSerializer(movimiento, context={'request': request}).data,
                mensaje="Transferencia registrada exitosamente",
                status_code=status.HTTP_201_CREATED,
            )

        except Exception as e:
            self.logger.error(f"Error al crear transferencia: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al registrar transferencia",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'], url_path='anular')
    @requiere_permiso('autorizar_movimiento')
    def anular(self, request, pk=None):
        """
        Anula un movimiento creando uno inverso.
        POST /api/movimientos-inventario/{id}/anular/
        Body: {"motivo": "Razón de anulación"}
        """
        try:
            movimiento = self.get_object()
            motivo     = request.data.get('motivo', '').strip()

            if not motivo:
                return StandardResponse.validation_error(
                    {'motivo': ['El motivo de anulación es obligatorio.']}
                )

            tipo_inverso_map = {
                'entrada': 'salida',
                'salida': 'entrada',
                'transferencia': 'transferencia',
            }
            tipo_inverso = tipo_inverso_map.get(movimiento.tipo)

            if not tipo_inverso:
                return StandardResponse.error(
                    mensaje=f"No se puede anular un movimiento de tipo '{movimiento.tipo}'.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            data_anulacion = {
                'tipo':          tipo_inverso,
                'referencia':    f'ANULACIÓN: {movimiento.numero}',
                'observaciones': f'Anulación: {motivo}',
                'detalles_data': [],
            }

            if tipo_inverso == 'transferencia':
                data_anulacion['bodega_origen']  = str(movimiento.bodega_destino_id)
                data_anulacion['bodega_destino'] = str(movimiento.bodega_origen_id)
            elif tipo_inverso == 'salida':
                data_anulacion['bodega_origen'] = str(movimiento.bodega_destino_id)
            else:
                data_anulacion['bodega_destino'] = str(movimiento.bodega_origen_id)

            for detalle in movimiento.detalles.all():
                data_anulacion['detalles_data'].append({
                    'producto':      str(detalle.producto_id),
                    'cantidad':      detalle.cantidad,
                    'costo_unitario': str(detalle.costo_unitario) if detalle.costo_unitario else None,
                    'lote':          detalle.lote,
                    'observaciones': f'Anulación de {movimiento.numero}',
                })

            serializer = self.get_serializer(data=data_anulacion)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                movimiento_anulacion = serializer.save()

            self.logger.info(
                f"Movimiento anulado | Original={movimiento.numero} | "
                f"Anulacion={movimiento_anulacion.numero} | Usuario={request.user.id}"
            )

            return StandardResponse.success(
                data={
                    'movimiento_original': movimiento.numero,
                    'movimiento_anulacion': movimiento_anulacion.numero,
                },
                mensaje="Movimiento anulado exitosamente",
            )

        except Exception as e:
            self.logger.error(f"Error al anular movimiento: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al anular el movimiento",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], url_path='kardex')
    @requiere_permiso('ver_movimiento_inventario')
    def kardex(self, request):
        """
        Historial de movimientos de un producto.
        GET /api/movimientos-inventario/kardex/?producto_id=uuid&bodega_id=uuid
        """
        try:
            producto_id = request.query_params.get('producto_id')
            bodega_id   = request.query_params.get('bodega_id')

            if not producto_id:
                return StandardResponse.validation_error(
                    {'producto_id': ['Este parámetro es requerido.']}
                )

            try:
                producto = Producto.objects.get(
                    id=producto_id, empresa=request.empresa, deleted_at__isnull=True
                )
            except Producto.DoesNotExist:
                return StandardResponse.error(
                    mensaje="Producto no encontrado",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            detalles = DetalleMovimiento.objects.filter(
                producto_id=producto_id,
                empresa=request.empresa,
            ).select_related(
                'movimiento', 'movimiento__bodega_origen', 'movimiento__bodega_destino'
            )

            if bodega_id:
                detalles = detalles.filter(
                    Q(movimiento__bodega_origen_id=bodega_id) |
                    Q(movimiento__bodega_destino_id=bodega_id)
                )

            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')
            if fecha_desde:
                detalles = detalles.filter(movimiento__fecha__gte=fecha_desde)
            if fecha_hasta:
                detalles = detalles.filter(movimiento__fecha__lte=fecha_hasta)

            detalles = detalles.order_by('movimiento__fecha')

            kardex = [
                {
                    'fecha':          mov.fecha,
                    'numero':         mov.numero,
                    'tipo':           mov.tipo,
                    'tipo_display':   mov.get_tipo_display(),
                    'bodega_origen':  mov.bodega_origen.nombre if mov.bodega_origen else None,
                    'bodega_destino': mov.bodega_destino.nombre if mov.bodega_destino else None,
                    'cantidad':       d.cantidad,
                    'stock_anterior': d.stock_anterior,
                    'stock_posterior': d.stock_posterior,
                    'costo_unitario': float(d.costo_unitario) if d.costo_unitario else None,
                    'lote':           d.lote,
                    'referencia':     mov.referencia,
                    'observaciones':  d.observaciones or mov.observaciones,
                }
                for d in detalles
                for mov in [d.movimiento]
            ]

            stock_qs = Stock.objects.filter(producto_id=producto_id, empresa=request.empresa)
            if bodega_id:
                stock_qs = stock_qs.filter(bodega_id=bodega_id)

            stock_info = stock_qs.aggregate(total=Sum('cantidad'), reservado=Sum('stock_reservado'))
            total      = stock_info['total'] or 0
            reservado  = stock_info['reservado'] or 0

            return StandardResponse.success(data={
                'producto': {
                    'id':               str(producto.id),
                    'codigo':           producto.codigo,
                    'nombre':           producto.nombre,
                    'stock_actual':     total,
                    'stock_reservado':  reservado,
                    'stock_disponible': total - reservado,
                },
                'kardex':            kardex,
                'total_movimientos': len(kardex),
            })

        except Exception as e:
            self.logger.error(f"Error al generar kardex: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al generar el kardex",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], url_path='resumen')
    @requiere_permiso('ver_movimiento_inventario')
    def resumen(self, request):
        """
        Resumen de movimientos por período.
        GET /api/movimientos-inventario/resumen/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31
        """
        try:
            queryset = self.get_queryset()

            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')
            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)

            resumen_tipo = queryset.values('tipo').annotate(
                total=Count('id'),
                productos=Sum('detalles__cantidad'),
            ).order_by('tipo')

            return StandardResponse.success(data={
                'periodo': {'desde': fecha_desde, 'hasta': fecha_hasta},
                'total_movimientos': queryset.count(),
                'por_tipo': list(resumen_tipo),
            })

        except Exception as e:
            self.logger.error(f"Error al generar resumen: {str(e)}", exc_info=True)
            return StandardResponse.error(
                mensaje="Error al generar el resumen",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )