# apis/ventas/venta/venta_viewset.py
import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apis.ventas.venta.venta_serializer import (
    VentaSerializer,
    VentaSimpleSerializer,
    PagoSerializer
)
from apis.core.ViewSetBase import TenantViewSet
from apps.inventario.models import Bodega
from apps.ventas.models import Venta, Pago
from utils.mixins.permissions import PermissionCheckMixin


class VentaViewSet(PermissionCheckMixin, TenantViewSet):
    """
    ViewSet para gestionar Ventas del ERP.

    Flujo de trabajo:
    1. Crear venta en BORRADOR
    2. Confirmar venta → Genera MovimientoInventario (salida)
    3. Registrar pagos
    4. Facturar (opcional)
    5. Anular si es necesario

    Permisos:
    - view_venta: Ver ventas (Vendedor+)
    - add_venta: Crear ventas (Vendedor+)
    - change_venta: Editar ventas en borrador (Vendedor+)
    - delete_venta: Anular ventas (Supervisor+)
    - confirmar_venta: Confirmar ventas (Vendedor+)
    - ver_todas_ventas: Ver ventas de todos (Gerente)
    """

    queryset = Venta.objects.select_related(
        'cliente', 'cliente__persona', 'vendedor'
    ).prefetch_related('detalles', 'detalles__producto', 'pagos').filter(is_active=True)

    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch']  # NO delete directo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('venta_viewset')

    # ==================== QUERYSET OPTIMIZADO ====================

    def get_queryset(self):
        """
        Filtrar ventas según permisos del usuario.
        Vendedores solo ven sus propias ventas, supervisores y gerentes ven todas.
        """
        queryset = super().get_queryset()

        # Si no puede ver todas las ventas, filtrar por vendedor
        if not self.request.user.has_perm('ventas.ver_todas_ventas'):
            queryset = queryset.filter(vendedor=self.request.user)

        return queryset

    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return VentaSimpleSerializer
        return VentaSerializer

    # ==================== CRUD OPERATIONS ====================

    def list(self, request, *args, **kwargs):
        """
        Listar ventas con filtros avanzados.
        Permiso: view_venta
        """
        try:
            self.verificar_permiso('view_venta')

            queryset = self.filter_queryset(self.get_queryset())

            # Filtro por estado
            estado = request.query_params.get('estado', None)
            if estado:
                queryset = queryset.filter(estado=estado)

            # Filtro por tipo de pago
            tipo_pago = request.query_params.get('tipo_pago', None)
            if tipo_pago:
                queryset = queryset.filter(tipo_pago=tipo_pago)

            # Filtro por cliente
            cliente_id = request.query_params.get('cliente_id', None)
            if cliente_id:
                queryset = queryset.filter(cliente_id=cliente_id)

            # Filtro por rango de fechas
            fecha_desde = request.query_params.get('fecha_desde', None)
            fecha_hasta = request.query_params.get('fecha_hasta', None)

            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)

            # Filtro por búsqueda
            search = request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(numero__icontains=search) |
                    Q(cliente__ruc__icontains=search) |
                    Q(cliente__razon_social__icontains=search) |
                    Q(cliente__persona__nombre1__icontains=search) |
                    Q(cliente__persona__apellido1__icontains=search)
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
            self.logger.error(f"Error listando ventas: {str(e)}")
            return Response(
                {'error': 'Error al obtener ventas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crear nueva venta según workflow:
        - workflow='normal': Crea en borrador (comportamiento actual)
        - workflow='rapido': Ejecuta proceso completo automáticamente

        Body para workflow rápido:
        {
            "workflow": "rapido",
            "cliente": null,  // Opcional, usa Consumidor Final
            "tipo_pago": "contado",
            "metodo_pago": "efectivo",
            "detalles_data": [
                {
                    "producto": "uuid",
                    "cantidad": 2,
                    "precio_unitario": 10.50  // Opcional
                }
            ]
        }
        """
        try:
            self.verificar_permiso('add_venta')

            workflow = request.data.get('workflow', 'normal')

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            venta = serializer.save()

            # Log diferenciado según workflow
            if workflow == 'rapido':
                self.logger.info(
                    f"Venta RÁPIDA procesada por {request.user.username}: {venta.numero}",
                    extra={
                        'venta_id': str(venta.id),
                        'numero': venta.numero,
                        'estado_final': venta.estado,
                        'total': float(venta.total),
                        'factura': venta.numero_factura,
                        'workflow': 'rapido'
                    }
                )

                response_data = serializer.data
                response_data['message'] = (
                    f'Venta {venta.numero} procesada exitosamente. '
                    f'Factura: {venta.numero_factura}'
                )

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                self.logger.info(
                    f"Venta BORRADOR creada por {request.user.username}: {venta.numero}",
                    extra={
                        'venta_id': str(venta.id),
                        'numero': venta.numero,
                        'total': float(venta.total),
                        'workflow': 'normal'
                    }
                )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error creando venta: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalle completo de una venta.
        Permiso: view_venta
        """
        try:
            self.verificar_permiso('view_venta')

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Venta.DoesNotExist:
            return Response(
                {'error': 'Venta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo venta: {str(e)}")
            return Response(
                {'error': 'Error al obtener la venta'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualizar venta (solo en estado borrador).
        Permiso: change_venta
        """
        try:
            self.verificar_permiso('change_venta')

            partial = kwargs.pop('partial', False)
            instance = self.get_object()

            # Validar que esté en borrador
            if instance.estado != 'borrador':
                return Response(
                    {'error': 'Solo se pueden editar ventas en estado borrador'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            venta = serializer.save()

            self.logger.info(
                f"Venta actualizada: {venta.numero}",
                extra={
                    'venta_id': str(venta.id),
                    'actualizado_por': request.user.username
                }
            )

            return Response(serializer.data)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error actualizando venta: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial de venta"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ==================== CUSTOM ACTIONS ====================

    @action(detail=True, methods=['post'], url_path='despachar')
    def despachar(self, request, pk=None):
        """
        Despachar venta: Confirma inventario + Genera factura.

        CONTADO: Exige método de pago y registra pago automático.
        CRÉDITO: Solo despacha, permite saldo pendiente.
        """
        try:
            self.verificar_permiso('confirmar_venta')
            venta = self.get_object()

            # Validar estado inicial
            if venta.estado != 'borrador':
                raise ValidationError(
                    f'Solo se pueden despachar ventas en borrador. '
                    f'Estado actual: {venta.get_estado_display()}'
                )

            # Obtener bodega
            bodega_id = request.data.get('bodega')
            if bodega_id:
                try:
                    bodega = Bodega.objects.get(
                        id=bodega_id,
                        is_active=True,
                        permite_ventas=True
                    )
                except Bodega.DoesNotExist:
                    raise ValidationError('Bodega no encontrada o no permite ventas')
            else:
                try:
                    bodega = Bodega.objects.get(es_principal=True, is_active=True, empresa=venta.empresa)
                except Bodega.DoesNotExist:
                    raise ValidationError(
                        'No hay bodega principal configurada. '
                        'Debe especificar una bodega.'
                    )

            # ============ VALIDACIÓN POR TIPO DE PAGO ============
            metodo_pago = request.data.get('metodo_pago')

            if venta.tipo_pago == 'contado':
                # CONTADO: Exigir método de pago
                if not metodo_pago:
                    raise ValidationError({
                        'metodo_pago': (
                            'Las ventas al CONTADO requieren método de pago '
                            '(efectivo, transferencia, tarjeta_credito, tarjeta_debito)'
                        )
                    })

                # Validar método válido
                metodos_validos = dict(Venta.METODO_PAGO_CHOICES).keys()
                if metodo_pago not in metodos_validos:
                    raise ValidationError({
                        'metodo_pago': f'Método inválido. Opciones: {", ".join(metodos_validos)}'
                    })

            with transaction.atomic():
                serializer = self.get_serializer(venta)

                # PASO 1: Confirmar (salida de inventario)
                self.logger.info(
                    f"[1/3] Confirmando venta {venta.numero}",
                    extra={'venta_id': str(venta.id)}
                )
                resultado_confirmar = serializer.confirmar_venta(venta, bodega)

                # PASO 2: Facturar
                # self.logger.info(
                #     f"[2/3] Facturando venta {venta.numero}",
                #     extra={'venta_id': str(venta.id)}
                # )
                # resultado_factura = serializer.facturar_venta(venta)

                # PASO 3: Registrar pago si es CONTADO
                pago_info = None
                if venta.tipo_pago == 'contado':
                    self.logger.info(
                        f"[3/3] Registrando pago automático para venta {venta.numero}",
                        extra={'venta_id': str(venta.id)}
                    )

                    pago = Pago.objects.create(
                        venta=venta,
                        monto=Decimal(str(venta.total)).quantize(Decimal('0.01')),
                        metodo=metodo_pago,
                        referencia=f'PAGO-{venta.numero}',
                        observaciones='Pago automático al despachar - Venta al contado',
                        empresa=venta.empresa
                    )

                    venta.refresh_from_db()

                    # Validar que el saldo quedó en 0
                    if venta.saldo_pendiente != Decimal('0.00'):
                        raise ValidationError(
                            f"Error: El saldo pendiente no quedó en 0 después del pago. "
                            f"Saldo actual: ${venta.saldo_pendiente}"
                        )

                    pago_info = {
                        'pago_id': str(pago.id),
                        'metodo': pago.get_metodo_display(),
                        'monto': float(pago.monto),
                        'estado_pago': venta.estado_pago
                    }
                else:
                    # CRÉDITO: Refresh para obtener estado actualizado
                    venta.refresh_from_db()

                self.logger.info(
                    f"Venta {venta.numero} despachada exitosamente",
                    extra={
                        'venta_id': str(venta.id),
                        'tipo_pago': venta.tipo_pago,
                        'numero_factura': resultado_factura['numero_factura'],
                        'bodega': bodega.nombre,
                        'movimiento': resultado_confirmar['movimiento_numero'],
                        'pago_automatico': pago_info is not None,
                        'despachado_por': request.user.username
                    }
                )

                # Construir URL del PDF
                pdf_url = None
                if venta.pdf_factura:
                    pdf_url = request.build_absolute_uri(
                        f'/media/{venta.pdf_factura}'
                    )

                response_data = {
                    'message': 'Venta despachada y facturada exitosamente',
                    'venta': {
                        'id': str(venta.id),
                        'numero': venta.numero,
                        'estado': venta.estado,
                        'estado_display': venta.get_estado_display(),
                        'tipo_pago': venta.tipo_pago,
                        'total': float(venta.total),
                        'saldo_pendiente': float(venta.saldo_pendiente),
                        'estado_pago': venta.estado_pago
                    },
                    'inventario': {
                        'movimiento_numero': resultado_confirmar['movimiento_numero'],
                        'bodega': bodega.nombre
                    },
                    'factura': {
                        'numero_factura': resultado_factura['numero_factura'],
                        'clave_acceso': resultado_factura['clave_acceso'],
                        'estado_sri': resultado_factura['estado_sri'],
                        'correo_enviado': resultado_factura['correo_enviado'],
                        'pdf_url': pdf_url
                    }
                }

                # Agregar info de pago si se registró
                if pago_info:
                    response_data['pago'] = pago_info

                return Response(response_data, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.exception(f"Error al despachar venta: {str(e)}")
            return Response(
                {'error': f'Error al despachar venta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='anular')
    def anular(self, request, pk=None):
        """
        Anula una venta delegando la lógica compleja al Serializer.
        """
        try:
            self.verificar_permiso(
                'delete_venta',
                'Solo personal autorizado puede anular ventas confirmadas o facturadas.'
            )

            venta = self.get_object()
            motivo = request.data.get('motivo', '').strip()

            if not motivo:
                return Response(
                    {'error': 'Debe proporcionar un motivo para anular la operación.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(venta)
            resultado = serializer.anular_venta(venta, motivo=motivo)

            self.logger.info(
                f"Venta {venta.numero} anulada por {request.user.username}",
                extra={'venta_id': str(venta.id), 'motivo': motivo}
            )

            return Response(resultado, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.exception(f"Error en endpoint de anulación: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='registrar-pago')
    def registrar_pago(self, request, pk=None):
        """
        Registrar un pago para la venta.
        """
        try:
            self.verificar_permiso('add_venta')
            venta = self.get_object()

            # Validar que la venta tenga saldo pendiente
            if venta.esta_pagada():
                return Response(
                    {'error': 'Esta venta ya no tiene saldo pendiente'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar que la venta no esté anulada
            if venta.estado == 'anulada':
                return Response(
                    {'error': 'No se pueden registrar pagos en ventas anuladas'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            saldo_anterior = venta.saldo_pendiente

            # Validar monto
            monto = Decimal(str(request.data.get('monto', 0)))

            if monto <= 0:
                raise ValidationError('El monto debe ser mayor a 0')

            if monto > venta.saldo_pendiente:
                raise ValidationError(
                    f'El monto (${monto}) excede el saldo pendiente (${venta.saldo_pendiente})'
                )

            # Crear pago
            pago_data = {
                'venta': venta.id,
                'monto': monto,
                'metodo': request.data.get('metodo'),
                'referencia': request.data.get('referencia', ''),
                'observaciones': request.data.get('observaciones', '')
            }

            # CRÍTICO: Pasar contexto con request
            serializer = PagoSerializer(data=pago_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            pago = serializer.save()  # ← Remover venta=venta, ya está en validated_data

            venta.refresh_from_db()

            self.logger.info(
                f"Pago registrado para venta {venta.numero}",
                extra={
                    'venta_id': str(venta.id),
                    'pago_id': str(pago.id),
                    'monto': float(monto),
                    'metodo': pago.metodo,
                    'saldo_anterior': float(saldo_anterior),
                    'saldo_nuevo': float(venta.saldo_pendiente),
                    'estado_pago': venta.estado_pago,
                    'registrado_por': request.user.username
                }
            )

            return Response({
                'message': 'Pago registrado exitosamente',
                'pago': serializer.data,
                'venta': {
                    'id': str(venta.id),
                    'numero': venta.numero,
                    'saldo_anterior': float(saldo_anterior),
                    'saldo_actual': float(venta.saldo_pendiente),
                    'estado_pago': venta.estado_pago,
                    'esta_pagada': venta.esta_pagada()
                }
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            self.logger.error(f"Error registrando pago: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        Obtener resumen de ventas por período.
        GET /api/ventas/resumen/?fecha_desde=2024-01-01&fecha_hasta=2024-12-31

        Permiso: view_venta
        """
        try:
            self.verificar_permiso('view_venta')

            queryset = self.get_queryset()

            # Filtrar por fechas
            fecha_desde = request.query_params.get('fecha_desde')
            fecha_hasta = request.query_params.get('fecha_hasta')

            if fecha_desde:
                queryset = queryset.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha__lte=fecha_hasta)

            # Estadísticas generales
            stats = queryset.aggregate(
                total_ventas=Count('id'),
                monto_total=Sum('total'),
                ventas_borrador=Count('id', filter=Q(estado='borrador')),
                ventas_confirmadas=Count('id', filter=Q(estado='confirmada')),
                ventas_facturadas=Count('id', filter=Q(estado='facturada')),
                ventas_anuladas=Count('id', filter=Q(estado='anulada'))
            )

            # Por tipo de pago
            por_tipo_pago = queryset.values('tipo_pago').annotate(
                total=Count('id'),
                monto=Sum('total')
            )

            return Response({
                'periodo': {
                    'desde': fecha_desde,
                    'hasta': fecha_hasta
                },
                'estadisticas': stats,
                'por_tipo_pago': list(por_tipo_pago)
            })

        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            self.logger.error(f"Error generando resumen: {str(e)}")
            return Response(
                {'error': 'Error al generar resumen'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
