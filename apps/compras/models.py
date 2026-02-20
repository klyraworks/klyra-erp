# MODELOS - COMPRAS
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseModel, Persona
from apps.inventario.models import Producto, Bodega, Lote
from apps.rrhh.models import Departamento
from apps.seguridad.models import Empleado
from apps.personas.models import Proveedor
from datetime import date
import uuid
import os

class SolicitudCompra(BaseModel):
    """Solicitudes de compra internas"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente de Aprobación'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('procesada', 'Procesada'),
        ('anulada', 'Anulada')
    ]
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Solicitud", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    solicitante = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_compra', verbose_name="Solicitante")
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, null=True, blank=True, related_name='solicitudes_compra', verbose_name="Departamento")
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media', verbose_name="Prioridad")
    fecha_necesaria = models.DateField(verbose_name="Fecha Necesaria")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    justificacion = models.TextField(verbose_name="Justificación")
    aprobado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_aprobadas', verbose_name="Aprobado por")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    comentarios_aprobacion = models.TextField(blank=True, verbose_name="Comentarios de Aprobación")
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitud_origen', verbose_name="Orden de Compra Generada")

    # ==================== META ====================
    class Meta:
        verbose_name = "Solicitud de Compra"
        verbose_name_plural = "Solicitudes de Compra"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['solicitante', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_solicitud_compra_empresa'),
        ]
        permissions = [
            ("aprobar_solicitud", "Puede aprobar solicitudes de compra"),
            ("convertir_solicitud_orden", "Puede convertir solicitud a orden de compra"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Solicitud {self.numero} - {self.solicitante.get_full_name() if self.solicitante else 'Sin solicitante'}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: SC-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"SC-{fecha_str}-"

        ultimo = SolicitudCompra.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class DetalleSolicitudCompra(BaseModel):
    """Detalle de productos en solicitud de compra"""

    # ==================== CAMPOS ====================
    solicitud = models.ForeignKey(SolicitudCompra, on_delete=models.CASCADE, related_name='detalles', verbose_name="Solicitud")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_solicitudes_compra', verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad Solicitada")
    justificacion = models.TextField(blank=True, verbose_name="Justificación del Item")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Solicitud de Compra"
        verbose_name_plural = "Detalles de Solicitud de Compra"
        ordering = ['solicitud', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")


class OrdenCompra(BaseModel):
    """Órdenes de compra a proveedores"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('confirmada', 'Confirmada'),
        ('recibida_parcial', 'Recibida Parcial'),
        ('recibida_completa', 'Recibida Completa'),
        ('anulada', 'Anulada')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Orden", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Emisión")
    fecha_esperada = models.DateField(verbose_name="Fecha Esperada de Entrega")
    fecha_recepcion = models.DateField(null=True, blank=True, verbose_name="Fecha de Recepción")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='ordenes_compra', verbose_name="Proveedor")
    comprador = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_compra', verbose_name="Comprador")
    bodega_entrega = models.ForeignKey(Bodega, on_delete=models.PROTECT, null=True, blank=True, related_name='ordenes_compra', verbose_name="Bodega de Entrega")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Descuento")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    direccion_entrega = models.TextField(verbose_name="Dirección de Entrega")
    condiciones_pago = models.TextField(blank=True, verbose_name="Condiciones de Pago")

    # ==================== META ====================
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['fecha', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_orden_compra_empresa'),
        ]
        permissions = [
            ("aprobar_orden_compra", "Puede aprobar órdenes de compra"),
            ("anular_orden_compra", "Puede anular órdenes de compra"),
            ("recibir_orden_compra", "Puede registrar recepción de mercancía"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"OC {self.numero} - {self.proveedor}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_totales(self):
        """Recalcula subtotal, IVA y total"""
        detalles = self.detalles.all()
        self.subtotal = sum(d.subtotal for d in detalles)
        self.iva_valor = sum(d.iva_valor for d in detalles)
        self.total = self.subtotal + self.iva_valor - self.descuento

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: OC-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"OC-{fecha_str}-"

        ultimo = OrdenCompra.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class DetalleOrdenCompra(BaseModel):
    """Detalle de productos en orden de compra"""

    # ==================== CAMPOS ====================
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='detalles', verbose_name="Orden de Compra")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_ordenes_compra', verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad Solicitada")
    cantidad_recibida = models.IntegerField(default=0, verbose_name="Cantidad Recibida")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Descuento")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Subtotal")
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="IVA")
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Total")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Orden de Compra"
        verbose_name_plural = "Detalles de Orden de Compra"
        ordering = ['orden_compra', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    # ==================== PROPERTIES ====================
    @property
    def cantidad_pendiente(self):
        """Calcula la cantidad pendiente de recibir"""
        return self.cantidad - self.cantidad_recibida

    @property
    def esta_completo(self):
        """Verifica si se ha recibido la cantidad completa"""
        return self.cantidad_recibida >= self.cantidad

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

        if self.cantidad_recibida > self.cantidad:
            raise ValidationError("La cantidad recibida no puede ser mayor a la solicitada")

    def save(self, *args, **kwargs):
        """Calcula totales automáticamente"""
        self.calcular_totales()
        super().save(*args, **kwargs)


class RecepcionMercancia(BaseModel):
    """Recepción de mercancía de órdenes de compra"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Verificación'),
        ('verificada', 'Verificada'),
        ('rechazada', 'Rechazada')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Recepción", editable=False)
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.PROTECT, related_name='recepciones', verbose_name="Orden de Compra")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Recepción")
    recibido_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='recepciones', verbose_name="Recibido por")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    numero_guia = models.CharField(max_length=50, blank=True, verbose_name="Número de Guía de Remisión")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    documentos_adjuntos = models.FileField(upload_to='recepciones/', null=True, blank=True, verbose_name="Documentos Adjuntos")

    # ==================== META ====================
    class Meta:
        verbose_name = "Recepción de Mercancía"
        verbose_name_plural = "Recepciones de Mercancía"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['orden_compra', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_recepcion_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Recepción {self.numero} - OC {self.orden_compra.numero}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: REC-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"REC-{fecha_str}-"

        ultimo = RecepcionMercancia.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class DetalleRecepcion(BaseModel):
    """Detalle de productos recibidos"""

    # ==================== CAMPOS ====================
    recepcion = models.ForeignKey(RecepcionMercancia, on_delete=models.CASCADE, related_name='detalles', verbose_name="Recepción")
    detalle_orden = models.ForeignKey(DetalleOrdenCompra, on_delete=models.PROTECT, related_name='detalles_recepciones', verbose_name="Detalle de Orden")
    cantidad_recibida = models.IntegerField(verbose_name="Cantidad Recibida")
    cantidad_rechazada = models.IntegerField(default=0, verbose_name="Cantidad Rechazada")
    motivo_rechazo = models.TextField(blank=True, verbose_name="Motivo de Rechazo")
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name='recepciones', verbose_name="Lote Generado")
    costo_unitario_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo Unitario Real")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Recepción"
        verbose_name_plural = "Detalles de Recepción"
        ordering = ['recepcion', 'detalle_orden']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.detalle_orden.producto.nombre} - Recibido: {self.cantidad_recibida}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.cantidad_recibida + self.cantidad_rechazada <= 0:
            raise ValidationError("Debe registrar al menos una cantidad recibida o rechazada")