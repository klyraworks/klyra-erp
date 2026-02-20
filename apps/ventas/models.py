# MODELOS - VENTAS
import logging
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, Persona
from apps.inventario.models import Producto, Bodega, MovimientoInventario, Stock
from apps.seguridad.models import Empleado
from apps.personas.models import Cliente


class Venta(BaseModel):
    """Ventas con soporte para facturación electrónica"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('facturada', 'Facturada'),
        ('anulada', 'Anulada')
    ]
    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito')
    ]
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('cheque', 'Cheque'),
        ('deposito', 'Depósito Bancario')
    ]
    ESTADO_SRI_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
        ('devuelta', 'Devuelta')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Venta", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas', verbose_name="Cliente")
    vendedor = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas', verbose_name="Vendedor")
    tipo_pago = models.CharField(max_length=10, choices=TIPO_PAGO_CHOICES, default='contado', verbose_name="Tipo de Pago")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo', verbose_name="Método de Pago")
    plazo_credito_dias = models.IntegerField(blank=True, null=True, verbose_name="Plazo de Crédito (días)")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Descuento")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total")
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Pendiente")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    numero_factura = models.CharField(max_length=17, blank=True, null=True, verbose_name="Número de Factura")
    fecha_factura = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Facturación")
    guia_remision = models.CharField(max_length=17, blank=True, null=True, verbose_name="Guía de Remisión")
    clave_acceso = models.CharField(max_length=49, blank=True, null=True, verbose_name="Clave de Acceso")
    numero_autorizacion = models.CharField(max_length=49, blank=True, null=True, verbose_name="Número de Autorización SRI")
    fecha_autorizacion = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Autorización SRI")
    estado_sri = models.CharField(max_length=20, blank=True, null=True, choices=ESTADO_SRI_CHOICES, verbose_name="Estado en SRI")
    mensaje_sri = models.TextField(blank=True, null=True, verbose_name="Mensaje del SRI")
    xml_factura = models.TextField(blank=True, null=True, verbose_name="XML de la Factura")
    xml_autorizado = models.TextField(blank=True, null=True, verbose_name="XML Autorizado por SRI")
    pdf_factura = models.FileField(upload_to='facturas/pdf/%Y/%m/', blank=True, null=True, verbose_name="PDF de la Factura (RIDE)")
    correo_enviado = models.BooleanField(default=False, verbose_name="Correo Enviado al Cliente")
    fecha_envio_correo = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Envío de Correo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['empresa', 'fecha', 'estado']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['numero_factura']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_venta_empresa'),
            models.UniqueConstraint(fields=['numero_factura', 'empresa'], name='unique_numero_factura_empresa', condition=models.Q(numero_factura__isnull=False)),
        ]
        permissions = [
            ("anular_venta", "Puede anular ventas"),
            ("confirmar_venta", "Puede confirmar ventas"),
            ("facturar_venta", "Puede facturar ventas"),
            ("ver_todas_ventas", "Puede ver ventas de todos los vendedores"),
            ("ver_comisiones", "Puede ver comisiones"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Venta {self.numero} - {self.cliente}"

    # ==================== PROPERTIES ====================
    @property
    def estado_pago(self):
        """Estado del pago de la venta"""
        if self.saldo_pendiente == 0:
            return "PAGADO"
        if self.saldo_pendiente < self.total:
            return "PAGO PARCIAL"
        return "PENDIENTE"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_totales(self):
        """Recalcula subtotal, IVA y total"""
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        self.iva_valor = sum(d.iva_valor for d in detalles)
        self.total = self.subtotal + self.iva_valor - self.descuento
        self.saldo_pendiente = self.total

    def esta_facturada(self):
        """Verifica si la venta ya tiene factura"""
        return bool(self.numero_factura)

    def puede_facturarse(self):
        """Verifica si puede facturarse"""
        return self.estado == 'confirmada' and not self.numero_factura

    def esta_autorizada_sri(self):
        """Verifica si la factura está autorizada por el SRI"""
        return self.estado_sri == 'autorizada'

    def esta_pagada(self):
        """Verifica si la venta está completamente pagada"""
        return self.saldo_pendiente == 0

    def tiene_saldo_pendiente(self):
        """Verifica si tiene saldo pendiente"""
        return self.saldo_pendiente > 0

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: VEN-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"VEN-{fecha_str}-"

        ultimo = Venta.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

        if ultimo:
            try:
                correlativo = int(ultimo.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.tipo_pago == 'credito':
            if not self.cliente.puede_comprar_a_credito():
                raise ValidationError(
                    f"El cliente {self.cliente} no tiene límite de crédito configurado"
                )

            if not self.plazo_credito_dias:
                raise ValidationError({
                    'plazo_credito_dias': 'Debe especificar el plazo de crédito en días'
                })

    def save(self, *args, **kwargs):
        """Genera número automático"""
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)


class DetalleVenta(BaseModel):
    """Detalle de productos en una venta"""

    # ==================== CAMPOS ====================
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', verbose_name="Venta")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_ventas', verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Descuento")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Subtotal")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Total")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
        ordering = ['venta', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_totales(self):
        """Calcula subtotal, IVA y total"""
        self.subtotal = (self.cantidad * self.precio_unitario) - self.descuento

        if self.producto.iva:
            self.iva_valor = self.subtotal * Decimal('0.15')
        else:
            self.iva_valor = 0

        self.total = self.subtotal + self.iva_valor

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")

    def save(self, *args, **kwargs):
        """Calcula totales automáticamente"""
        self.calcular_totales()
        super().save(*args, **kwargs)


class Pago(BaseModel):
    """Registro de pagos para ventas"""

    # ==================== CHOICES ====================
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('cheque', 'Cheque'),
        ('deposito', 'Depósito Bancario')
    ]

    # ==================== CAMPOS ====================
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT, related_name='pagos', verbose_name="Venta")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, verbose_name="Método de Pago")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Referencia/Número")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['venta', 'fecha']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Pago ${self.monto} - Venta {self.venta.numero}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_referencia(self):
        """Genera referencia única: PAG-VEN-YYYYMMDD-####-###"""
        numero_secuencial = self.venta.pagos.count() + 1
        return f"PAG-{self.venta.numero}-{numero_secuencial:03d}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        total_pagado = self.venta.pagos.exclude(id=self.id).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')

        saldo_restante = self.venta.total - total_pagado

        if self.monto > saldo_restante:
            raise ValidationError(
                f"El monto (${self.monto:.2f}) excede el saldo pendiente "
                f"(${saldo_restante:.2f}) de la venta {self.venta.numero}"
            )

        if self.monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0")

    def save(self, *args, **kwargs):
        """Genera referencia automática y guarda el pago"""
        logger = logging.getLogger('pago_model')

        self.full_clean()

        if not self.referencia:
            self.referencia = self._generar_referencia()

        super().save(*args, **kwargs)

        logger.info(
            f"Pago registrado para venta {self.venta.numero}",
            extra={
                'pago_id': str(self.id),
                'venta_id': str(self.venta.id),
                'monto': float(self.monto)
            }
        )


class Cotizacion(BaseModel):
    """Cotizaciones para clientes"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Cotización", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones', verbose_name="Cliente")
    vendedor = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones', verbose_name="Vendedor")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Descuento")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    venta = models.ForeignKey(Venta, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizacion_origen', verbose_name="Venta Generada")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['cliente', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_cotizacion_empresa'),
        ]
        permissions = [
            ("convertir_cotizacion", "Puede convertir cotización a venta"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Cotización {self.numero} - {self.cliente}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_totales(self):
        """Recalcula subtotal, IVA y total"""
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        self.iva_valor = sum(d.iva_valor for d in detalles)
        self.total = self.subtotal + self.iva_valor - self.descuento

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: COT-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"COT-{fecha_str}-"

        ultimo = Cotizacion.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

        if ultimo:
            try:
                correlativo = int(ultimo.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera número automático"""
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)


class DetalleCotizacion(BaseModel):
    """Detalle de productos en una cotización"""

    # ==================== CAMPOS ====================
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles', verbose_name="Cotización")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_cotizaciones', verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Descuento")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Subtotal")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Total")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Cotización"
        verbose_name_plural = "Detalles de Cotización"
        ordering = ['cotizacion', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_totales(self):
        """Calcula subtotal, IVA y total"""
        self.subtotal = (self.cantidad * self.precio_unitario) - self.descuento

        if self.producto.iva:
            self.iva_valor = self.subtotal * Decimal('0.15')
        else:
            self.iva_valor = 0

        self.total = self.subtotal + self.iva_valor

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Calcula totales automáticamente"""
        self.calcular_totales()
        super().save(*args, **kwargs)