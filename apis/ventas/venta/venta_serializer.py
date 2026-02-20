# apis/ventas/venta/venta_serializer.py
import logging
from decimal import Decimal
from datetime import date

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apis.ventas.cliente.cliente_serializer import ClienteSerializer
from apis.ventas.pago.pago_serializer import PagoSerializer
from apps.core.models import Empresa, ConfiguracionCorreo
from apps.inventario.models import Producto, Bodega, MovimientoInventario, Stock
from apis.inventario.movimiento.movimiento_serializer import MovimientoInventarioSerializer
from apps.seguridad.models import Empleado
from apps.ventas.models import Venta, DetalleVenta, Cliente, Pago
from utils.validators import BusinessValidators
from apis.core.SerializerBase import TenantSerializer
from apps.facturacion.services.open_factura_service import facturar_venta_con_open_factura
from apis.inventario.bodega.bodega_serializer import BodegaSimpleSerializer, BodegaSerializer

logger = logging.getLogger('facturacion')

class DetalleVentaSerializer(TenantSerializer):
    """
    Serializer para DetalleVenta.
    Representa cada línea de producto en una venta.
    """

    # READ-ONLY - Información enriquecida
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_stock = serializers.IntegerField(source='producto.stock', read_only=True)

    # WRITE - UUID para creación
    producto = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.filter(is_active=True),
        write_only=True
    )

    class Meta:
        model = DetalleVenta
        fields = [
            'id', 'producto', 'producto_nombre', 'producto_codigo', 'producto_stock',
            'cantidad', 'descuento', 'precio_unitario',
            'subtotal', 'iva_valor', 'total'
        ]
        read_only_fields = ['id', 'subtotal', 'iva_valor', 'total']

    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva"""
        return BusinessValidators.validate_positive_integer(value, "cantidad")

    def validate_precio_unitario(self, value):
        """Valida que el precio sea positivo"""
        return BusinessValidators.validate_positive_amount(value, "precio unitario")

    def validate_descuento(self, value):
        """Valida que el descuento no sea negativo"""
        if value < 0:
            raise ValidationError("El descuento no puede ser negativo")
        return value

    def validate_producto(self, value):
        """Valida la existencia del producto en la bodega"""
        if not Stock.objects.filter(producto=value, empresa=self.get_empresa_from_context()).exists():
            raise ValidationError("El producto no existe en la bodega")
        return value

    def validate(self, attrs):
        """
        Validación completa de detalle de venta.
        Asigna precio automáticamente si no viene.
        """
        producto = attrs.get('producto')
        cantidad = attrs.get('cantidad')

        # 1. Auto-asignar precio si no viene
        if 'precio_unitario' not in attrs or attrs['precio_unitario'] is None:
            attrs['precio_unitario'] = producto.precio_venta

        # 2. Validar que precio sea positivo
        if attrs['precio_unitario'] <= 0:
            raise ValidationError({
                'precio_unitario': 'El precio unitario debe ser mayor a 0'
            })

        # 3. Validar descuento no mayor al subtotal
        descuento = attrs.get('descuento', Decimal('0.00'))
        subtotal = attrs['precio_unitario'] * cantidad

        if descuento > subtotal:
            raise ValidationError({
                'descuento': f'El descuento (${descuento}) no puede ser mayor al subtotal (${subtotal})'
            })

        return attrs

class VentaSerializer(TenantSerializer):
    """
    Serializer para Venta con integración completa a facturación electrónica.

    Flujo de estados:
    1. BORRADOR: Venta creada, sin afectar inventario
    2. CONFIRMADA: Venta confirmada, genera MovimientoInventario (salida)
    3. FACTURADA: Factura generada, XML creado, PDF generado, email enviado
    4. ANULADA: Venta anulada

    Funcionalidades:
    - Creación de venta en borrador
    - Confirmación con generación de MovimientoInventario
    - Facturación electrónica (preparado para SRI)
    - Envío automático de email con factura
    - Validación de stock disponible
    - Cálculo automático de totales
    - Gestión de pagos
    """

    # READ-ONLY - Información enriquecida
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    cliente_detalle = ClienteSerializer(source='cliente', read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    bodega_nombre = serializers.CharField(source='bodega.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_pago_display = serializers.CharField(source='get_tipo_pago_display', read_only=True)
    estado_sri_display = serializers.CharField(source='get_estado_sri_display', read_only=True)
    pagos = PagoSerializer(many=True, read_only=True)
    fecha_local = serializers.SerializerMethodField()

    # WRITE-ONLY - Para creación
    detalles_data = DetalleVentaSerializer(many=True, write_only=True)
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.filter(is_active=True),
        write_only=True,
        required=False,
        allow_null=True,
        help_text="Cliente de la venta. Si no se especifica, se usa Consumidor Final automáticamente"
    )
    bodega = serializers.PrimaryKeyRelatedField(
        queryset=Bodega.objects.filter(is_active=True, permite_ventas=True),
        write_only=True,
        required=False,
        help_text="Bodega desde donde se despacha la venta"
    )
    workflow = serializers.ChoiceField(
        choices=[('normal', 'Normal'), ('rapido', 'Rápido')],
        write_only=True,
        required=False,
        default='normal',
        help_text="Tipo de workflow: 'normal' (paso a paso) o 'rapido' (todo en uno)"
    )
    metodo_pago = serializers.ChoiceField(
        choices=Venta.METODO_PAGO_CHOICES,
        write_only=True,
        required=False,
        help_text="Método de pago (requerido para workflow rápido con contado)"
    )

    class Meta:
        model = Venta
        fields = [
            # Identificación
            'id', 'numero', 'fecha', 'fecha_local',

            # Relaciones
            'cliente', 'cliente_detalle', 'vendedor', 'vendedor_nombre',
            'bodega', 'bodega_nombre',

            # Tipo y montos
            'tipo_pago', 'tipo_pago_display',
            'subtotal', 'descuento', 'iva_valor', 'total', 'metodo_pago', 'workflow',

            # Estado
            'estado', 'estado_display', 'observaciones',

            # Facturación
            'numero_factura', 'fecha_factura',
            'clave_acceso', 'numero_autorizacion', 'fecha_autorizacion',
            'estado_sri', 'estado_sri_display', 'mensaje_sri',
            'xml_factura', 'xml_autorizado', 'pdf_factura',
            'correo_enviado', 'fecha_envio_correo',

            # Pagos
            'saldo_pendiente', 'pagos',

            # Detalles
            'detalles', 'detalles_data',

            # Auditoría
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'numero', 'fecha', 'vendedor',
            'subtotal', 'iva_valor', 'total',
            'numero_factura', 'fecha_factura',
            'clave_acceso', 'numero_autorizacion', 'fecha_autorizacion',
            'estado_sri', 'mensaje_sri',
            'xml_factura', 'xml_autorizado', 'pdf_factura',
            'correo_enviado', 'fecha_envio_correo',
            'saldo_pendiente',
            'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('venta_serializer')

    # ==================== GETS ====================
    def get_fecha_local(self, obj):
        # Convertir a zona local para mostrar

        return timezone.localtime(obj.fecha).strftime('%Y-%m-%d %H:%M:%S')

    # ==================== VALIDATIONS ====================

    def validate_detalles_data(self, value):
        """
        Valida que haya productos, no haya duplicados y haya stock disponible.
        """
        if not value or len(value) == 0:
            raise ValidationError("Debe incluir al menos un producto en la venta")

        # 1. Validar productos duplicados
        productos_ids = [d['producto'].id for d in value]
        if len(productos_ids) != len(set(productos_ids)):
            raise ValidationError("No se permiten productos duplicados en la venta")

        # 2. Validar stock disponible
        for detalle in value:
            producto = detalle['producto']
            cantidad = detalle['cantidad']

            if producto.stock < cantidad:
                raise ValidationError(
                    f'Stock insuficiente para {producto.nombre}. '
                    f'Disponible: {producto.stock}, Requerido: {cantidad}'
                )

        return value

    def validate_descuento(self, value):
        """Valida que el descuento no sea negativo"""
        if value < 0:
            raise ValidationError("El descuento no puede ser negativo")
        return value

    def validate_bodega(self, value):
        """Valida que exista dicho producto en la bodega especificada"""
        if not Stock.objects.filter(bodega=value, empresa=self.get_empresa_from_context()).exists():
            raise ValidationError("Esta bodega no registra productos.")
        return value

    def validate(self, attrs):
        """
        Validaciones cruzadas con protección contra race conditions.
        """
        tipo_pago = attrs.get('tipo_pago', 'contado')
        detalles_data = attrs.get('detalles_data', [])
        workflow = attrs.get('workflow', 'normal')
        empresa = self.get_empresa_from_context()

        # 1. Si no hay cliente, usar Consumidor Final (solo en CREATE)
        if 'cliente' not in attrs or attrs['cliente'] is None:
            if not self.instance:
                consumidor_final = Cliente.get_consumidor_final(empresa)
                attrs['cliente'] = consumidor_final
                self.logger.info("Cliente no especificado. Usando Consumidor Final.")

        cliente = attrs.get('cliente', self.instance.cliente if self.instance else None)

        # 2. Asignar bodega principal si no viene
        if 'bodega' not in attrs or attrs['bodega'] is None:
            try:
                bodega_principal = Bodega.objects.get(es_principal=True, is_active=True, empresa=empresa)
                attrs['bodega'] = bodega_principal
                self.logger.info(f"Bodega no especificada. Usando: {bodega_principal.nombre}")
            except Bodega.DoesNotExist:
                raise ValidationError({
                    'bodega': 'No hay bodega principal configurada. Debe especificar una bodega.'
                })

        # 3. Validar crédito si es venta a crédito CON SELECT FOR UPDATE
        if tipo_pago == 'credito':
            # Validar que no sea consumidor final
            if cliente and cliente.es_consumidor_final():
                raise ValidationError({
                    'tipo_pago': 'Consumidor Final no puede comprar a crédito'
                })

            # CRÍTICO: Bloquear cliente para evitar race conditions
            from django.db import transaction

            # Solo bloquear si NO estamos ya en el create() (evitar doble lock)
            if not getattr(self.context.get('request'), '_en_create_venta', False):
                with transaction.atomic():
                    # SELECT FOR UPDATE: Bloquea la fila hasta commit
                    cliente_bloqueado = Cliente.objects.select_for_update().get(pk=cliente.pk)

                    # Calcular total (precios ya asignados en DetalleVentaSerializer)
                    total_venta = Decimal('0.00')
                    for detalle in detalles_data:
                        precio = detalle.get('precio_unitario', detalle['producto'].precio_venta)
                        subtotal = Decimal(str(precio)) * detalle['cantidad']
                        descuento = Decimal(str(detalle.get('descuento', 0)))
                        total_venta += (subtotal - descuento)

                    # Validar crédito con datos bloqueados
                    if not cliente_bloqueado.puede_comprar_a_credito(monto=total_venta):
                        raise ValidationError({
                            'tipo_pago': (
                                f'Crédito insuficiente. '
                                f'Disponible: ${cliente_bloqueado.credito_disponible}, '
                                f'Requerido: ${total_venta}'
                            )
                        })
            else:
                # Si ya estamos en create(), calcular total para otras validaciones
                total_venta = Decimal('0.00')
                for detalle in detalles_data:
                    precio = detalle.get('precio_unitario', detalle['producto'].precio_venta)
                    subtotal = Decimal(str(precio)) * detalle['cantidad']
                    descuento = Decimal(str(detalle.get('descuento', 0)))
                    total_venta += (subtotal - descuento)

        # 4. Validaciones de workflow rápido
        if workflow == 'rapido':
            if tipo_pago != 'contado':
                raise ValidationError({
                    'workflow': 'El workflow rápido solo soporta ventas de contado'
                })
            if not attrs.get('metodo_pago'):
                raise ValidationError({
                    'metodo_pago': 'Debe especificar método de pago para workflow rápido'
                })

        return attrs

    # ==================== HELPER METHODS ====================

    def _generar_numero_venta(self):
        """Genera número único de venta"""
        fecha = date.today().strftime('%Y%m%d')

        # Buscar último número del día
        ultimo = Venta.objects.filter(
            numero__startswith=f"VEN-{fecha}"
        ).order_by('-numero').first()

        if ultimo:
            try:
                ultimo_numero = int(ultimo.numero.split('-')[-1])
                nuevo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                nuevo_numero = 1
        else:
            nuevo_numero = 1

        return f"VEN-{fecha}-{nuevo_numero:04d}"

    def _calcular_totales(self, detalles_data):
        """
        Calcula subtotal, IVA y total de la venta.
        Usa la tasa de IVA específica de cada producto.
        """
        subtotal = Decimal('0.00')
        iva_valor = Decimal('0.00')

        for detalle in detalles_data:
            producto = detalle['producto']
            cantidad = detalle['cantidad']
            precio_unitario = detalle.get('precio_unitario', producto.precio_venta)
            descuento = detalle.get('descuento', Decimal('0.00'))

            detalle_subtotal = (precio_unitario * cantidad) - descuento
            subtotal += detalle_subtotal

            # Calcular IVA usando la tasa específica del producto
            if producto.iva:
                # Usar tasa del producto o 15% por defecto (Ecuador)
                tasa_iva = getattr(producto, 'tasa_iva', Decimal('0.15'))
                detalle_iva = detalle_subtotal * tasa_iva
                iva_valor += detalle_iva

        return subtotal, iva_valor

    def _generar_movimiento_inventario(self, venta, bodega):
        """
        Genera MovimientoInventario de tipo SALIDA cuando se confirma la venta.

        Args:
            venta: Instancia de Venta
            bodega: Bodega desde donde se despacha

        Returns:
            MovimientoInventario: Movimiento generado
        """

        # Preparar detalles del movimiento
        detalles_movimiento = []
        for detalle in venta.detalles.all():
            detalles_movimiento.append({
                'producto': str(detalle.producto.id),
                'cantidad': detalle.cantidad,
                'costo_unitario': detalle.producto.precio_compra,
                'observaciones': f'Venta {venta.numero}'
            })

        # Datos del movimiento
        movimiento_data = {
            'tipo': 'salida',
            'bodega_origen': bodega.id,  # ← Ahora recibe bodega como parámetro
            'referencia': venta.numero,
            'observaciones': f'Salida por venta {venta.numero} - Cliente: {venta.cliente.get_nombre_facturacion()}',
            'detalles_data': detalles_movimiento
        }

        # Crear movimiento usando el serializer de inventario
        movimiento_serializer = MovimientoInventarioSerializer(
            data=movimiento_data,
            context=self.context
        )

        movimiento_serializer.is_valid(raise_exception=True)
        movimiento = movimiento_serializer.save()

        self.logger.info(
            f"Movimiento de salida generado para venta {venta.numero}: {movimiento.numero}",
            extra={
                'venta_id': str(venta.id),
                'movimiento_id': str(movimiento.id),
                'bodega': bodega.nombre  # ← Ahora usa bodega del parámetro
            }
        )

        return movimiento

    def _generar_factura_electronica(self, venta):
        """
        Genera factura electrónica: número, XML, PDF y envía email.
        Centraliza la generación de PDF aquí.
        """
        try:
            # 1. Obtener configuración de empresa
            empresa = venta.empresa

            # 2. Generar número de factura
            numero_factura = empresa.generar_numero_factura()

            # 3. Actualizar venta con datos de facturación
            venta.numero_factura = numero_factura
            venta.fecha_factura = self.get_fecha_empresa()
            venta.estado = 'facturada'
            venta.estado_sri = 'pendiente'

            # 4. Generar clave de acceso
            venta.clave_acceso = self._generar_clave_acceso(venta, empresa)

            # 5. Generar XML de la factura
            xml_factura = self._generar_xml_factura(venta, empresa)
            venta.xml_factura = xml_factura

            # 6. Guardar cambios antes de generar PDF
            venta.save()

            # 7. Generar PDF (CENTRALIZADO AQUÍ)
            # from utils.pdf_generator import generar_factura_completa
            # factura_info = generar_factura_completa(venta)

            # if factura_info['success']:
            #     venta.pdf_factura = factura_info['pdf_url']
            #     self.logger.info(
            #         f"PDF generado: {factura_info['pdf_url']}",
            #         extra={'venta_id': str(venta.id)}
            #     )
            # else:
            #     self.logger.warning(
            #         f"PDF no generado: {factura_info.get('error')}",
            #         extra={'venta_id': str(venta.id)}
            #     )

            # 8. Enviar email (solo si NO es consumidor final)
            if not venta.cliente.es_consumidor_final():
                self._enviar_email_factura(venta, empresa)

            venta.save()

            self.logger.info(
                f"Factura generada: {numero_factura}",
                extra={
                    'venta_id': str(venta.id),
                    'numero_factura': numero_factura,
                    'cliente_id': str(venta.cliente.id)
                }
            )

            return {
                'numero_factura': numero_factura,
                'clave_acceso': venta.clave_acceso,
                'estado_sri': venta.estado_sri,
                'correo_enviado': venta.correo_enviado,
                # 'pdf_generado': factura_info['success']
            }

        except Exception as e:
            self.logger.exception(f"Error generando factura para venta {venta.numero}: {str(e)}")
            venta.estado_sri = 'rechazada'
            venta.mensaje_sri = f"Error en generación: {str(e)}"
            venta.save()
            raise ValidationError(f"Error al generar factura: {str(e)}")

    def _generar_clave_acceso(self, venta, empresa):
        """
        Genera clave de acceso de 49 dígitos según algoritmo SRI.

        TODO: Implementar algoritmo completo del SRI
        Formato: DDMMAAAATDDRRRRRRRRRPPPSSSSSSSSC
        - DD: día
        - MM: mes
        - AAAA: año
        - T: tipo comprobante (01=factura)
        - DD: RUC emisor (13 dígitos)
        - RRR: tipo ambiente
        - SSSSSSSSS: número secuencial
        - C: dígito verificador (módulo 11)
        """
        fecha = venta.fecha_factura or timezone.now()

        # Formato simplificado por ahora
        fecha_str = fecha.strftime('%d%m%Y')
        tipo_comprobante = '01'  # Factura
        ruc = empresa.ruc
        ambiente = empresa.ambiente_sri
        tipo_emision = empresa.tipo_emision
        secuencial = venta.numero_factura.replace('-', '')[-9:]

        # TODO: Calcular dígito verificador módulo 11
        digito_verificador = '0'  # Placeholder

        clave = f"{fecha_str}{tipo_comprobante}{ruc}{ambiente}{tipo_emision}{secuencial}{digito_verificador}"

        return clave[:49].zfill(49)  # Asegurar 49 dígitos

    def _generar_xml_factura(self, venta, empresa):
        """
        Genera XML de factura según XSD del SRI.

        TODO: Implementar generación completa según esquema XSD del SRI
        """
        # Placeholder - retornar estructura básica
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <factura id="comprobante" version="1.0.0">
            <infoTributaria>
                <ambiente>{empresa.ambiente_sri}</ambiente>
                <tipoEmision>{empresa.tipo_emision}</tipoEmision>
                <razonSocial>{empresa.razon_social}</razonSocial>
                <nombreComercial>{empresa.nombre_comercial}</nombreComercial>
                <ruc>{empresa.ruc}</ruc>
                <claveAcceso>{venta.clave_acceso}</claveAcceso>
                <codDoc>01</codDoc>
                <estab>{empresa.establecimiento}</estab>
                <ptoEmi>{empresa.punto_emision}</ptoEmi>
                <secuencial>{venta.numero_factura.split('-')[-1]}</secuencial>
                <dirMatriz>{empresa.direccion_matriz}</dirMatriz>
            </infoTributaria>
            <!-- TODO: Agregar infoFactura, detalles, infoAdicional -->
        </factura>"""

        return xml

    def _generar_pdf_factura(self, venta, empresa):
        """
        Genera PDF (RIDE) de la factura desde template HTML.

        TODO: Implementar generación de PDF usando librería como WeasyPrint o ReportLab
        """
        # Placeholder - retornar path ficticio
        # En producción, esto debería:
        # 1. Renderizar template HTML con datos de venta
        # 2. Convertir HTML a PDF
        # 3. Guardar en storage (local o S3)
        # 4. Retornar path del archivo

        self.logger.info(f"Generando PDF para factura {venta.numero_factura}")
        return f"facturas/pdf/{venta.numero_factura}.pdf"

    def _enviar_email_factura(self, venta, empresa):
        """
        Envía factura por email al cliente.

        TODO: Implementar envío real de email con adjuntos
        """
        try:
            email_cliente = venta.cliente.get_email_facturacion()

            if not email_cliente:
                self.logger.warning(
                    f"Cliente {venta.cliente} no tiene email registrado. No se envió factura."
                )
                return

            # TODO: Implementar envío usando ConfiguracionCorreo
            # config_correo = ConfiguracionCorreo.objects.get(empresa=empresa)
            #
            # subject = config_correo.asunto_factura.format(numero=venta.numero_factura)
            # message = config_correo.mensaje_factura.format(
            #     cliente=venta.cliente.get_nombre_facturacion(),
            #     numero=venta.numero_factura,
            #     total=venta.total,
            #     empresa=empresa.razon_social
            # )
            #
            # send_mail(
            #     subject=subject,
            #     message=message,
            #     from_email=config_correo.email_remitente,
            #     recipient_list=[email_cliente],
            #     fail_silently=False,
            #     html_message=render_to_string('emails/factura.html', context)
            # )

            venta.correo_enviado = True
            venta.fecha_envio_correo = timezone.now()

            self.logger.info(
                f"Email enviado a {email_cliente} con factura {venta.numero_factura}"
            )

        except Exception as e:
            self.logger.error(f"Error enviando email factura: {str(e)}")
            # No lanzar excepción, solo log - el email no debe bloquear el proceso

    def _ejecutar_workflow_rapido(self, venta, metodo_pago, bodega):
        """
        Ejecuta flujo completo: confirmar → pagar → facturar.
        ACTUALIZADO para usar open-factura
        """
        try:
            with transaction.atomic():
                self.logger.info(f"Iniciando workflow rápido para venta {venta.numero}")

                self.context['es_workflow_rapido'] = True

                # PASO 1: Confirmar
                self.logger.info(f"[1/4] Confirmando venta {venta.numero}")
                resultado_confirmar = self.confirmar_venta(venta, bodega)

                # PASO 2: Registrar pago
                self.logger.info(f"[2/4] Registrando pago para venta {venta.numero}")

                if venta.tipo_pago != 'contado':
                    raise ValidationError(
                        f"Inconsistencia: workflow rápido solo permite contado. "
                        f"Tipo actual: {venta.tipo_pago}"
                    )

                pago = Pago.objects.create(
                    empresa=venta.empresa,
                    venta=venta,
                    monto=Decimal(str(venta.total)).quantize(Decimal('0.01')),
                    metodo=metodo_pago,
                    referencia=f'PAGO-{venta.numero}',
                    observaciones='Pago automático - Workflow rápido'
                )

                venta.refresh_from_db()

                if venta.saldo_pendiente != Decimal('0.00'):
                    raise ValidationError(
                        f"Error: El saldo pendiente no quedó en 0 después del pago. "
                        f"Saldo actual: ${venta.saldo_pendiente}"
                    )

                # PASO 3: Facturación electrónica con open-factura
                # self.logger.info(
                #     f"[3/4] Facturando electrónicamente venta {venta.numero} "
                #     f"usando open-factura"
                # )
                #
                # try:
                #     resultado_factura = facturar_venta_con_open_factura(venta)
                #
                #     if not resultado_factura.get('success'):
                #         raise ValidationError(
                #             f"Error en facturación electrónica: "
                #             f"{resultado_factura.get('mensaje', 'Error desconocido')}"
                #         )
                #
                # except Exception as e:
                #     logger.exception(f"Error en facturación electrónica: {str(e)}")
                #     raise ValidationError(
                #         f"Error en facturación electrónica: {str(e)}"
                #     )

                # venta.refresh_from_db()

                self.logger.info(
                    f"Workflow rápido completado para venta {venta.numero}",
                    extra={
                        'venta_id': str(venta.id),
                        'numero_factura': venta.numero_factura,
                        # 'clave_acceso': resultado_factura.get('claveAcceso'),
                        # 'numero_autorizacion': resultado_factura.get('numero_autorizacion'),
                        'total': float(venta.total),
                        'saldo_final': float(venta.saldo_pendiente)
                    }
                )

                # Agregar info al contexto
                self.context['workflow_rapido_ejecutado'] = True
                self.context['pago_id'] = str(pago.id)
                self.context['movimiento_numero'] = resultado_confirmar['movimiento_numero']
                self.context['numero_factura'] = venta.numero_factura
                # self.context['clave_acceso'] = resultado_factura.get('claveAcceso')
                # self.context['numero_autorizacion'] = resultado_factura.get('numero_autorizacion')
                # self.context['fecha_autorizacion'] = resultado_factura.get('fechaAutorizacion')

                return venta

        except Exception as e:
            self.logger.exception(
                f"Error en workflow rápido para venta {venta.numero}: {str(e)}"
            )
            raise ValidationError(
                f"Error en workflow rápido: {str(e)}. "
                f"La operación ha sido revertida completamente."
            )
        finally:
            self.context.pop('es_workflow_rapido', None)

    def _registrar_pago_automatico(self, venta, metodo_pago):
        """
        Registra pago automático para ventas al contado.

        Args:
            venta: Instancia de Venta
            metodo_pago: Método de pago (efectivo, transferencia, etc.)

        Returns:
            Pago: Instancia del pago creado
        """
        pago = Pago.objects.create(
            empresa=venta.empresa,
            venta=venta,
            monto=venta.total,
            metodo=metodo_pago,
            referencia=f'PAGO-{venta.numero}',
            observaciones='Pago automático - Workflow rápido'
        )

        venta.refresh_from_db()

        self.logger.info(
            f"Pago automático registrado: {venta.numero} - ${venta.total}",
            extra={'pago_id': str(pago.id), 'venta_id': str(venta.id)}
        )

        return pago

    # ==================== CREATE ====================

    def create(self, validated_data):
        """
        Crea venta con SELECT FOR UPDATE en crédito.
        """
        workflow = validated_data.pop('workflow', 'normal')
        metodo_pago = validated_data.pop('metodo_pago', 'efectivo')
        bodega = validated_data.pop('bodega')

        detalles_data = validated_data.pop('detalles_data')
        cliente = validated_data.pop('cliente')
        descuento_global = validated_data.pop('descuento', Decimal('0.00'))

        request = self.context.get('request')
        vendedor = Empleado.objects.get(usuario=request.user)

        # Flag para evitar doble SELECT FOR UPDATE
        request._en_create_venta = True

        try:
            with transaction.atomic():
                # CRÍTICO: Bloquear cliente si es crédito
                if validated_data.get('tipo_pago') == 'credito':
                    cliente = Cliente.objects.select_for_update().get(pk=cliente.pk)

                # 1. Calcular totales
                subtotal, iva_valor = self._calcular_totales(detalles_data)
                total = subtotal + iva_valor - descuento_global

                # 2. Validar crédito NUEVAMENTE con lock activo
                if validated_data.get('tipo_pago') == 'credito':
                    if not cliente.puede_comprar_a_credito(monto=total):
                        raise ValidationError(
                            f"Crédito insuficiente. Disponible: ${cliente.credito_disponible}, "
                            f"Requerido: ${total}"
                        )

                # 3. Generar número de venta
                numero = self._generar_numero_venta()

                # 4. Crear venta en BORRADOR
                validated_data['numero'] = numero
                validated_data['cliente'] = cliente
                validated_data['vendedor'] = vendedor
                validated_data['subtotal'] = subtotal
                validated_data['descuento'] = descuento_global
                validated_data['iva_valor'] = iva_valor
                validated_data['total'] = total
                validated_data['saldo_pendiente'] = total
                validated_data['estado'] = 'borrador'

                # Usar super() para asignar empresa automáticamente
                venta = super().create(validated_data)

                # 5. Crear detalles
                # 5. Crear detalles
                for detalle_data in detalles_data:

                    producto = detalle_data.pop('producto')

                    detalle_data.pop('cliente', None)
                    detalle_data.pop('bodega', None)

                    detalle_dict = {
                        'venta': venta.id,
                        'producto': str(producto.id),
                        'cantidad': detalle_data['cantidad'],
                        'precio_unitario': detalle_data.get('precio_unitario'),
                        'descuento': detalle_data.get('descuento', 0)
                    }

                    detalle_serializer = DetalleVentaSerializer(
                        data=detalle_dict,
                        context=self.context
                    )
                    detalle_serializer.is_valid(raise_exception=True)
                    detalle_serializer.save(venta=venta)

                self.logger.info(
                    f"Venta creada: {venta.numero}",
                    extra={
                        'venta_id': str(venta.id),
                        'workflow': workflow,
                        'cliente_id': str(cliente.id),
                        'total': float(total)
                    }
                )

                # 6. WORKFLOW RÁPIDO
                if workflow == 'rapido':
                    venta = self._ejecutar_workflow_rapido(venta, metodo_pago, bodega)

                return venta

        except ValidationError:
            raise
        except Exception as e:
            self.logger.exception(f"Error creando venta: {str(e)}")
            raise ValidationError(f"Error al crear venta: {str(e)}")
        finally:
            # Limpiar flag
            request._en_create_venta = False

    # ==================== UPDATE ====================

    def update(self, instance, validated_data):
        """
        Actualiza venta SOLO si está en borrador.
        """
        if instance.estado != 'borrador':
            raise ValidationError(
                "Solo se pueden editar ventas en estado borrador. "
                "Para modificar una venta confirmada o facturada, debe anularla y crear una nueva."
            )

        detalles_data = validated_data.pop('detalles_data', None)
        descuento_global = validated_data.pop('descuento', instance.descuento)

        # Limpiar campos de solo escritura
        validated_data.pop('bodega', None)
        validated_data.pop('workflow', None)
        validated_data.pop('metodo_pago', None)
        validated_data.pop('cliente', None)  # No permitir cambio de cliente

        try:
            with transaction.atomic():
                # Actualizar campos simples
                for field, value in validated_data.items():
                    setattr(instance, field, value)

                # Si hay nuevos detalles, reemplazar
                if detalles_data is not None:
                    # Eliminar detalles existentes
                    instance.detalles.all().delete()

                    # Crear nuevos detalles
                    for detalle_data in detalles_data:
                        detalle_data['venta'] = instance.id
                        detalle_data['producto'] = detalle_data['producto'].id

                        detalle_data.pop('cliente', None)
                        detalle_data.pop('bodega', None)

                        detalle_serializer = DetalleVentaSerializer(
                            data=detalle_data,
                            context=self.context
                        )
                        detalle_serializer.is_valid(raise_exception=True)
                        detalle_serializer.save()

                    # Recalcular totales
                    subtotal, iva_valor = self._calcular_totales(detalles_data)
                    instance.subtotal = subtotal
                    instance.iva_valor = iva_valor
                    instance.descuento = descuento_global
                    instance.total = subtotal + iva_valor - descuento_global
                    instance.saldo_pendiente = instance.total

                instance.save()

                self.logger.info(
                    f"Venta actualizada: {instance.numero}",
                    extra={'venta_id': str(instance.id)}
                )

                return instance

        except Exception as e:
            self.logger.exception(f"Error actualizando venta: {str(e)}")
            raise ValidationError(f"Error al actualizar venta: {str(e)}")

    # ==================== CUSTOM ACTIONS ====================

    def confirmar_venta(self, venta, bodega):
        """
        Confirma venta: genera salida de inventario.

        IMPORTANTE: Solo reduce crédito si NO habrá pago inmediato.
        Para workflow rápido (con pago inmediato), el crédito se maneja en los pagos.
        """
        # Validar estado
        if venta.estado != 'borrador':
            raise ValidationError(
                f'Solo se pueden confirmar ventas en borrador. '
                f'Estado actual: {venta.get_estado_display()}'
            )

        # Preparar detalles del movimiento
        detalles_movimiento = []
        for detalle in venta.detalles.all():
            detalles_movimiento.append({
                'producto': str(detalle.producto.id),
                'cantidad': detalle.cantidad,
                'costo_unitario': detalle.producto.precio_compra,
                'observaciones': f'Venta {venta.numero}'
            })

        # Crear movimiento de inventario
        movimiento_data = {
            'tipo': 'salida',
            'bodega_origen': str(bodega.id),
            'referencia': venta.numero,
            'observaciones': (
                f'Salida por venta {venta.numero} - '
                f'Cliente: {venta.cliente.get_nombre_facturacion()}'
            ),
            'detalles_data': detalles_movimiento
        }

        movimiento_serializer = MovimientoInventarioSerializer(
            data=movimiento_data,
            context=self.context
        )

        movimiento_serializer.is_valid(raise_exception=True)
        movimiento = movimiento_serializer.save()

        # CRÍTICO: Solo reducir crédito si es venta a crédito SIN pago inmediato
        # El contexto indica si es workflow rápido (con pago inmediato)
        es_workflow_rapido = self.context.get('es_workflow_rapido', False)

        if venta.tipo_pago == 'credito' and not es_workflow_rapido:
            venta.cliente.reducir_credito(venta.total)
            self.logger.info(
                f"Crédito reducido para cliente {venta.cliente}",
                extra={
                    'cliente_id': str(venta.cliente.id),
                    'monto_reducido': float(venta.total),
                    'credito_disponible': float(venta.cliente.credito_disponible)
                }
            )

        # Actualizar estado
        venta.estado = 'confirmada'
        venta.save(update_fields=['estado', 'updated_at'])

        self.logger.info(
            f"Venta confirmada: {venta.numero} → Movimiento: {movimiento.numero}",
            extra={
                'venta_id': str(venta.id),
                'movimiento_id': str(movimiento.id),
                'bodega': bodega.nombre
            }
        )

        return {
            'movimiento_numero': movimiento.numero,
            'bodega': bodega.nombre
        }

    def facturar_venta(self, venta):
        """
        Genera factura electrónica para la venta.

        REQUISITO: La venta debe estar en estado 'confirmada'
        (inventario ya salió, crédito ya se redujo).

        Cambia estado: confirmada → facturada
        Genera: Número de factura, XML, PDF, envía email

        Args:
            venta: Instancia de Venta en estado 'confirmada'

        Returns:
            dict: Información de la facturación
        """
        # Validar estado
        if venta.estado != 'confirmada':
            raise ValidationError(
                f"Solo se pueden facturar ventas confirmadas. "
                f"Estado actual: {venta.get_estado_display()}"
            )

        # Validar que no esté ya facturada
        if venta.esta_facturada():
            raise ValidationError(
                f"Esta venta ya tiene factura: {venta.numero_factura}"
            )

        try:
            # Generar factura electrónica
            info_factura = self._generar_factura_electronica(venta)

            self.logger.info(
                f"Venta facturada: {venta.numero} → Factura: {info_factura['numero_factura']}",
                extra={
                    'venta_id': str(venta.id),
                    'numero_factura': info_factura['numero_factura'],
                    'estado_sri': info_factura['estado_sri'],
                }
            )

            return {
                'venta_id': str(venta.id),
                'numero_venta': venta.numero,
                'numero_factura': info_factura['numero_factura'],
                'clave_acceso': info_factura['clave_acceso'],
                'estado': venta.estado,
                'estado_sri': info_factura['estado_sri'],
                'correo_enviado': info_factura['correo_enviado'],
                'mensaje': f'Factura {info_factura["numero_factura"]} generada exitosamente'
            }

        except Exception as e:
            self.logger.exception(f"Error facturando venta {venta.numero}: {str(e)}")
            raise ValidationError(f"Error al facturar venta: {str(e)}")

    def anular_venta(self, venta, motivo=None):
        """
        Anula una venta siguiendo el flujo de 4 estados.

        - Si está en BORRADOR: Solo cambia estado.
        - Si está CONFIRMADA: Reversa inventario y libera crédito.
        - Si está FACTURADA y AUTORIZADA: Bloquea la anulación (exige Nota de Crédito).
        - Si está FACTURADA NO AUTORIZADA: Reversa inventario y libera crédito.
        """
        # 1. Validaciones de estado
        if venta.estado == 'anulada':
            raise ValidationError("La venta ya se encuentra anulada.")

        if venta.estado == 'facturada' and venta.esta_autorizada_sri():
            raise ValidationError(
                "No se puede anular una factura autorizada por el SRI. "
                "Debe generar una Nota de Crédito legal para reversar esta operación."
            )

        try:
            with transaction.atomic():
                movimiento_reversa = None
                credito_liberado = Decimal('0.00')

                # 2. Reversa de procesos (Solo si la venta salió de borrador)
                if venta.estado in ['confirmada', 'facturada']:

                    # A. REVERSA DE INVENTARIO
                    try:
                        movimiento_original = MovimientoInventario.objects.get(
                            referencia=venta.numero,
                            tipo='salida'
                        )
                        bodega = movimiento_original.bodega_origen
                    except MovimientoInventario.DoesNotExist:
                        self.logger.warning(
                            f"No se encontró movimiento de salida para {venta.numero}. "
                            "Continuando sin reversa de inventario."
                        )
                        bodega = None

                    if bodega:
                        detalles_reversa = [{
                            'producto': str(d.producto.id),
                            'cantidad': d.cantidad,
                            'costo_unitario': d.producto.precio_compra,
                            'observaciones': f'Anulación venta {venta.numero}'
                        } for d in venta.detalles.all()]

                        movimiento_data = {
                            'tipo': 'entrada',
                            'bodega_destino': str(bodega.id),
                            'referencia': f'ANULACIÓN-{venta.numero}',
                            'observaciones': f'Reversa por anulación. Motivo: {motivo or "No especificado"}',
                            'detalles_data': detalles_reversa
                        }

                        mov_serializer = MovimientoInventarioSerializer(
                            data=movimiento_data,
                            context=self.context
                        )
                        mov_serializer.is_valid(raise_exception=True)
                        movimiento_reversa = mov_serializer.save()

                        self.logger.info(
                            f"Inventario reversado: {movimiento_reversa.numero}",
                            extra={
                                'venta_id': str(venta.id),
                                'movimiento_reversa_id': str(movimiento_reversa.id)
                            }
                        )

                    # B. REVERSA DE CRÉDITO - SOLO SALDO PENDIENTE
                    # Los pagos ya liberaron crédito automáticamente vía signal
                    if venta.tipo_pago == 'credito' and venta.saldo_pendiente > 0:
                        credito_antes = venta.cliente.credito_disponible
                        credito_liberado = venta.saldo_pendiente

                        venta.cliente.liberar_credito(credito_liberado)
                        venta.cliente.save(update_fields=['credito_disponible'])

                        self.logger.info(
                            f"Crédito liberado por anulación para {venta.cliente.get_nombre_facturacion()}",
                            extra={
                                'cliente_id': str(venta.cliente.id),
                                'monto_liberado': float(credito_liberado),
                                'credito_antes': float(credito_antes),
                                'credito_despues': float(venta.cliente.credito_disponible),
                                'nota': 'Solo saldo pendiente - Los pagos ya liberaron su parte'
                            }
                        )

                # 3. Cambio de estado final
                venta.estado = 'anulada'
                anulacion_msg = f"ANULADA: {motivo}" if motivo else "ANULADA"

                if venta.observaciones:
                    venta.observaciones = f"{venta.observaciones}\n\n{anulacion_msg}"
                else:
                    venta.observaciones = anulacion_msg

                # El saldo pendiente se vuelve 0 al anular
                venta.saldo_pendiente = Decimal('0.00')
                venta.save(update_fields=['estado', 'observaciones', 'saldo_pendiente', 'updated_at'])

                self.logger.info(
                    f"Venta {venta.numero} anulada exitosamente",
                    extra={
                        'venta_id': str(venta.id),
                        'motivo': motivo,
                        'estado_anterior': venta.estado,
                        'reversa_inventario': movimiento_reversa.numero if movimiento_reversa else None,
                        'credito_liberado': float(credito_liberado)
                    }
                )

                return {
                    'venta_id': str(venta.id),
                    'numero': venta.numero,
                    'estado': venta.estado,
                    'estado_display': venta.get_estado_display(),
                    'movimiento_reversa': movimiento_reversa.numero if movimiento_reversa else None,
                    'credito_liberado': float(credito_liberado) if credito_liberado > 0 else None,
                    'mensaje': f'Venta {venta.numero} anulada correctamente.'
                }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.exception(f"Error crítico anulando venta {venta.numero}: {str(e)}")
            raise ValidationError(f"No se pudo completar la anulación: {str(e)}")

    # ==================== REPRESENTATION ====================

    def to_representation(self, instance):
        """Enriquece la respuesta con información adicional"""
        data = super().to_representation(instance)

        # Total de productos
        detalles = instance.detalles.all()
        data['total_productos'] = detalles.count()
        data['cantidad_total'] = sum(d.cantidad for d in detalles)

        # Información de pagos si es a crédito
        if instance.tipo_pago == 'credito':
            total_pagado = instance.pagos.aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')

            data['total_pagado'] = float(total_pagado)
            data['saldo_pendiente'] = float(instance.total - total_pagado)

        # Estado de facturación
        data['facturada'] = instance.esta_facturada()
        data['puede_facturarse'] = instance.puede_facturarse()
        data['autorizada_sri'] = instance.esta_autorizada_sri()

        # Estado de la venta
        data['estado'] = instance.get_estado_display()

        # Cliente info adicional
        data['es_consumidor_final'] = instance.cliente.es_consumidor_final()

        # data['saldo_pendiente'] = float(instance.saldo_pendiente)

        # Warnings si los hay
        if 'warnings' in self.context:
            data['warnings'] = self.context['warnings']

        # NUEVO: Info de workflow rápido si aplica
        if self.context.get('workflow_rapido_ejecutado'):
            data['workflow_info'] = {
                'tipo': 'rapido',
                'completado': True,
                'pago_id': self.context.get('pago_id'),
                'movimiento_numero': self.context.get('movimiento_numero'),
                'numero_factura': self.context.get('numero_factura'),
                'mensaje': 'Venta procesada completamente en un solo paso'
            }

        return data


# ==================== SERIALIZERS ADICIONALES ====================

class VentaSimpleSerializer(TenantSerializer):
    """Serializer simplificado para listados rápidos"""

    cliente_nombre = serializers.SerializerMethodField()
    vendedor_nombre = serializers.CharField(source='vendedor.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    es_consumidor_final = serializers.SerializerMethodField()
    fecha_local = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            'id', 'numero', 'fecha', 'cliente_nombre', 'vendedor_nombre',
            'total', 'estado', 'estado_display', 'tipo_pago',
            'numero_factura', 'estado_sri', 'es_consumidor_final', 'saldo_pendiente', 'fecha_local'
        ]

    def get_cliente_nombre(self, obj):
        return obj.cliente.get_nombre_facturacion()

    def get_es_consumidor_final(self, obj):
        return obj.cliente.es_consumidor_final()

    def get_fecha_local(self, obj):
        """Usa zona horaria del usuario si está disponible"""
        import pytz

        request = self.context.get('request')

        if request and hasattr(request.user, 'timezone'):
            # Si el usuario tiene zona horaria configurada
            user_tz = pytz.timezone(request.user.timezone)
        else:
            # Zona horaria por defecto (Ecuador)
            user_tz = pytz.timezone('America/Guayaquil')

        return obj.fecha.astimezone(user_tz).strftime('%Y-%m-%dT%H:%M:%S')


class EmpresaSerializer(TenantSerializer):
    """Serializer para configuración de Empresa"""

    puede_facturar = serializers.SerializerMethodField()
    certificado_vigente = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = [
            'id', 'ruc', 'razon_social', 'nombre_comercial',
            'direccion_matriz', 'ciudad', 'provincia', 'pais',
            'telefono', 'celular', 'email', 'sitio_web',
            'obligado_contabilidad', 'contribuyente_especial', 'agente_retencion',
            'ambiente_sri', 'tipo_emision',
            'establecimiento', 'punto_emision',
            'secuencial_factura', 'secuencial_nota_credito',
            'logo', 'color_primario', 'slogan',
            'fecha_expiracion_certificado',
            'puede_facturar', 'certificado_vigente',
            'is_active'
        ]
        read_only_fields = ['id', 'puede_facturar', 'certificado_vigente']

    def get_puede_facturar(self, obj):
        return obj.puede_facturar_electronicamente()

    def get_certificado_vigente(self, obj):
        return obj.esta_certificado_vigente()


class ConfiguracionCorreoSerializer(TenantSerializer):
    """Serializer para configuración de envío de correos"""

    class Meta:
        model = ConfiguracionCorreo
        fields = [
            'id', 'empresa',
            'servidor_smtp', 'puerto_smtp', 'usar_tls',
            'email_remitente', 'nombre_remitente',
            'asunto_factura', 'mensaje_factura'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'password_email': {'write_only': True}  # No exponer password en GET
        }
