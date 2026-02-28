from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel, Empresa, Persona

class Proveedor(BaseModel):
    """Proveedores de productos y servicios"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica')
    ]
    CATEGORIA_CHOICES = [
        ('A', 'Categoría A - Estratégico'),
        ('B', 'Categoría B - Importante'),
        ('C', 'Categoría C - Regular')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    persona = models.OneToOneField(Persona, on_delete=models.CASCADE, related_name='proveedor', verbose_name="Persona")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='natural', verbose_name="Tipo de Proveedor")
    ruc = models.CharField(max_length=13, verbose_name="RUC")
    razon_social = models.CharField(max_length=200, blank=True, verbose_name="Razón Social")
    categoria = models.CharField(max_length=1, choices=CATEGORIA_CHOICES, default='C', verbose_name="Categoría")
    dias_credito = models.IntegerField(default=0, verbose_name="Días de Crédito")
    cuenta_bancaria = models.CharField(max_length=50, blank=True, verbose_name="Cuenta Bancaria")
    banco = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    contacto_principal = models.CharField(max_length=200, blank=True, verbose_name="Contacto Principal")
    telefono_contacto = models.CharField(max_length=15, blank=True, verbose_name="Teléfono de Contacto")
    calificacion = models.IntegerField(default=5, verbose_name="Calificación (1-10)")

    # ==================== META ====================
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['razon_social', 'persona__apellido1']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['ruc']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_proveedor_empresa'),
            models.UniqueConstraint(fields=['ruc', 'empresa'], name='unique_ruc_proveedor_empresa'),
        ]
        permissions = [
            ("ver_historial_compras_proveedor", "Puede ver historial de compras del proveedor"),
            ("gestionar_calificacion", "Puede gestionar calificación de proveedores"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.ruc} - {self.razon_social or self.persona.full_name()}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: PROV-{CORRELATIVO}"""
        patron_base = "PROV-"
        ultimo = Proveedor.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                correlativo = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if not (1 <= self.calificacion <= 10):
            raise ValidationError("La calificación debe estar entre 1 y 10")

    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class Cliente(BaseModel):
    """Clientes con soporte para facturación electrónica Ecuador"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica')
    ]
    TIPO_IDENTIFICACION_CHOICES = [
        ('ruc', 'RUC'),
        ('cedula', 'Cédula'),
        ('pasaporte', 'Pasaporte'),
        ('consumidor_final', 'Consumidor Final')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='clientes', verbose_name="Persona")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='natural', verbose_name="Tipo de Cliente")
    tipo_identificacion = models.CharField(max_length=20, choices=TIPO_IDENTIFICACION_CHOICES, default='cedula', verbose_name="Tipo de Identificación")
    identificacion = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de Identificación")
    ruc = models.CharField(max_length=13, blank=True, null=True, verbose_name="RUC (Deprecado)")
    razon_social = models.CharField(max_length=200, blank=True, verbose_name="Razón Social")
    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Límite de Crédito")
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Descuento (%)")
    credito_disponible = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Crédito Disponible")
    email_facturacion = models.EmailField(blank=True, null=True, verbose_name="Email para Facturas")
    telefono_facturacion = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Facturación")
    direccion = models.TextField(blank=True, verbose_name="Dirección")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razon_social', 'persona__apellido1']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['identificacion']),
            models.Index(fields=['empresa', 'persona']),  # + esto
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_cliente_empresa'),
            models.UniqueConstraint(fields=['identificacion', 'empresa'], name='unique_identificacion_per_empresa'),
            models.UniqueConstraint(fields=['persona', 'empresa'], name='unique_persona_cliente_empresa'),  # + esto
        ]
        permissions = [
            ("ver_historial_compras", "Puede ver historial de compras del cliente"),
            ("gestionar_credito", "Puede gestionar límite de crédito"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        if self.es_consumidor_final():
            return "CONSUMIDOR FINAL"
        return f"{self.identificacion} - {self.razon_social or self.persona.full_name()}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def es_consumidor_final(self):
        """Verifica si es un cliente consumidor final"""
        return self.tipo_identificacion == 'consumidor_final' or self.identificacion == '9999999999999'

    def get_nombre_facturacion(self):
        """Retorna el nombre que debe aparecer en la factura"""
        if self.es_consumidor_final():
            return "CONSUMIDOR FINAL"

        if self.razon_social:
            return self.razon_social

        return self.persona.full_name()

    def get_email_facturacion(self):
        """Retorna el email donde enviar facturas"""
        if self.es_consumidor_final():
            return None

        return self.email_facturacion or (self.persona.email if hasattr(self.persona, 'email') else None)

    def get_direccion_facturacion(self):
        """Retorna dirección para la factura"""
        if self.es_consumidor_final():
            return "S/N"

        return self.direccion or "No especificada"

    def get_telefono_facturacion(self):
        """Retorna teléfono para la factura"""
        if self.es_consumidor_final():
            return "S/N"

        return self.telefono_facturacion or (self.persona.telefono if hasattr(self.persona, 'telefono') else "S/N")

    def puede_comprar_a_credito(self, monto=None):
        """Verifica si el cliente puede comprar a crédito"""
        if self.es_consumidor_final():
            return False

        if self.limite_credito <= 0:
            return False

        if monto is not None:
            return self.credito_disponible >= monto

        return True

    def reducir_credito(self, monto):
        """Reduce el crédito disponible cuando se confirma una venta a crédito"""
        if self.credito_disponible < monto:
            raise ValidationError(
                f"Crédito insuficiente. Disponible: ${self.credito_disponible}, Requerido: ${monto}"
            )

        self.credito_disponible -= monto
        self.save(update_fields=['credito_disponible'])

    def liberar_credito(self, monto):
        """Libera crédito cuando se registra un pago o se anula una venta"""
        nuevo_credito = min(
            self.credito_disponible + monto,
            self.limite_credito
        )

        self.credito_disponible = nuevo_credito
        self.save(update_fields=['credito_disponible'])

    @classmethod
    def get_consumidor_final(cls, empresa):
        """Obtiene o crea el cliente CONSUMIDOR FINAL"""
        persona_cf, created = Persona.objects.get_or_create(
            cedula='9999999999',
            empresa=empresa,
            defaults={
                'nombre1': 'CONSUMIDOR',
                'apellido1': 'FINAL',
                'email': 'consumidorfinal@sistema.local'
            }
        )

        cliente_cf, created = cls.objects.get_or_create(
            empresa=empresa,
            identificacion='9999999999999',
            defaults={
                'persona': persona_cf,
                'tipo': 'natural',
                'tipo_identificacion': 'consumidor_final',
                'razon_social': 'CONSUMIDOR FINAL',
                'limite_credito': 0,
                'is_active': True
            }
        )

        return cliente_cf

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: CLI-{CORRELATIVO}"""
        patron_base = "CLI-"
        ultimo = Cliente.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                correlativo = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.tipo_identificacion == 'ruc':
            if not self.identificacion or len(self.identificacion) != 13:
                raise ValidationError({'identificacion': 'El RUC debe tener exactamente 13 dígitos'})

        elif self.tipo_identificacion == 'cedula':
            if not self.identificacion or len(self.identificacion) != 10:
                raise ValidationError({'identificacion': 'La cédula debe tener exactamente 10 dígitos'})

        elif self.tipo_identificacion == 'consumidor_final':
            self.identificacion = '9999999999999'
            if not self.razon_social:
                self.razon_social = 'CONSUMIDOR FINAL'

        if self.tipo == 'juridica' and self.tipo_identificacion != 'ruc':
            raise ValidationError({'tipo_identificacion': 'Las personas jurídicas deben tener RUC'})

        if not self.es_consumidor_final() and not self.email_facturacion:
            if hasattr(self.persona, 'email') and self.persona.email:
                self.email_facturacion = self.persona.email

        if self.tipo_identificacion == 'ruc':
            self.ruc = self.identificacion

    def save(self, *args, **kwargs):
        """Genera código e inicializa crédito disponible"""
        if not self.codigo:
            self.codigo = self._generar_codigo()

        if not self.pk and self.credito_disponible == 0:
            self.credito_disponible = self.limite_credito

        self.full_clean()
        super().save(*args, **kwargs)
