# MODELOS - FINANZAS
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
from apps.ventas.models import Cliente
from apps.compras.models import Proveedor
from apps.seguridad.models import Empleado


class PlanCuentas(BaseModel):
    """Plan de cuentas contable"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('activo', 'Activo'),
        ('pasivo', 'Pasivo'),
        ('patrimonio', 'Patrimonio'),
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
        ('costo', 'Costo')
    ]
    NATURALEZA_CHOICES = [
        ('deudora', 'Deudora'),
        ('acreedora', 'Acreedora')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código de Cuenta", editable=False)
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Cuenta")
    naturaleza = models.CharField(max_length=10, choices=NATURALEZA_CHOICES, verbose_name="Naturaleza")
    cuenta_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcuentas', verbose_name="Cuenta Padre")
    nivel = models.IntegerField(verbose_name="Nivel")
    acepta_movimiento = models.BooleanField(default=True, verbose_name="Acepta Movimiento")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    # ==================== META ====================
    class Meta:
        verbose_name = "Plan de Cuentas"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_cuenta_empresa'),
        ]
        permissions = [
            ("gestionar_plan_cuentas", "Puede gestionar el plan de cuentas"),
            ("ver_reportes_contables", "Puede ver reportes contables"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único según nivel jerárquico"""
        if not self.cuenta_padre:
            # Nivel 1: tipo de cuenta
            prefijos = {
                'activo': '1',
                'pasivo': '2',
                'patrimonio': '3',
                'ingreso': '4',
                'gasto': '5',
                'costo': '6'
            }
            base = prefijos.get(self.tipo, '9')
            ultimo = PlanCuentas.objects.filter(empresa=self.empresa, codigo__startswith=base, nivel=1).order_by('-codigo').first()

            if ultimo:
                try:
                    return f"{int(ultimo.codigo) + 1}"
                except ValueError:
                    return f"{base}001"
            return f"{base}001"
        else:
            # Subniveles: código_padre + correlativo
            base = self.cuenta_padre.codigo
            ultimos = PlanCuentas.objects.filter(empresa=self.empresa, cuenta_padre=self.cuenta_padre).order_by('-codigo')

            if ultimos.exists():
                ultimo_codigo = ultimos.first().codigo
                try:
                    sufijo = int(ultimo_codigo.replace(base, ''))
                    return f"{base}{sufijo + 1:02d}"
                except ValueError:
                    return f"{base}01"
            return f"{base}01"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.cuenta_padre:
            self.nivel = self.cuenta_padre.nivel + 1
            if not self.cuenta_padre.acepta_movimiento and self.acepta_movimiento:
                raise ValidationError("No se puede crear una cuenta de movimiento bajo una cuenta que no acepta movimientos")
        else:
            self.nivel = 1

    def save(self, *args, **kwargs):
        """Genera código automático y calcula nivel"""
        if not self.codigo:
            self.codigo = self._generar_codigo()

        if self.cuenta_padre:
            self.nivel = self.cuenta_padre.nivel + 1
        else:
            self.nivel = 1

        super().save(*args, **kwargs)


class CentroCosto(BaseModel):
    """Centros de costo para distribución de gastos"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='centros_costo', verbose_name="Responsable")
    centro_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcentros', verbose_name="Centro Padre")

    # ==================== META ====================
    class Meta:
        verbose_name = "Centro de Costo"
        verbose_name_plural = "Centros de Costo"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_centro_costo_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: CC-{CORRELATIVO}"""
        patron_base = "CC-"
        ultimo = CentroCosto.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                correlativo = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:03d}"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class AsientoContable(BaseModel):
    """Asientos contables"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
        ('traspaso', 'Traspaso'),
        ('ajuste', 'Ajuste'),
        ('apertura', 'Apertura'),
        ('cierre', 'Cierre')
    ]
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('contabilizado', 'Contabilizado'),
        ('anulado', 'Anulado')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Asiento", editable=False)
    fecha = models.DateField(verbose_name="Fecha")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    descripcion = models.TextField(verbose_name="Descripción")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Referencia")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='asientos', verbose_name="Responsable")
    contabilizado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='asientos_contabilizados', verbose_name="Contabilizado por")
    fecha_contabilizacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Contabilización")

    # ==================== META ====================
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha', '-numero']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['empresa', 'fecha', 'tipo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_asiento_empresa'),
        ]
        permissions = [
            ("contabilizar_asiento", "Puede contabilizar asientos"),
            ("anular_asiento", "Puede anular asientos contabilizados"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Asiento {self.numero} - {self.fecha}"

    # ==================== PROPERTIES ====================
    @property
    def esta_cuadrado(self):
        """Verifica que el asiento esté cuadrado"""
        total_debito = sum(d.debito for d in self.detalles.all())
        total_credito = sum(d.credito for d in self.detalles.all())
        return abs(total_debito - total_credito) < 0.01

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: ASI-YYYYMMDD-####"""
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"ASI-{fecha_str}-"

        ultimo = AsientoContable.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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

        if self.estado == 'contabilizado' and not self.esta_cuadrado:
            raise ValidationError("El asiento no está cuadrado. La suma de débitos debe ser igual a la suma de créditos.")

    def save(self, *args, **kwargs):
        """Genera número automático"""
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)


class DetalleAsiento(BaseModel):
    """Detalle de asientos contables"""

    # ==================== CAMPOS ====================
    asiento = models.ForeignKey(AsientoContable, on_delete=models.CASCADE, related_name='detalles', verbose_name="Asiento")
    cuenta = models.ForeignKey(PlanCuentas, on_delete=models.PROTECT, related_name='detalles_asientos', verbose_name="Cuenta")
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, null=True, blank=True, related_name='detalles_asientos', verbose_name="Centro de Costo")
    debito = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Débito")
    credito = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Crédito")
    descripcion = models.CharField(max_length=200, blank=True, verbose_name="Descripción")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Asiento"
        verbose_name_plural = "Detalles de Asiento"
        ordering = ['asiento', 'id']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.cuenta.codigo} - D:{self.debito} C:{self.credito}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if not self.cuenta.acepta_movimiento:
            raise ValidationError("La cuenta seleccionada no acepta movimientos")

        if self.debito > 0 and self.credito > 0:
            raise ValidationError("Una línea no puede tener débito y crédito al mismo tiempo")

        if self.debito == 0 and self.credito == 0:
            raise ValidationError("Debe ingresar un valor en débito o crédito")


class CuentaBancaria(BaseModel):
    """Cuentas bancarias de la empresa"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('ahorros', 'Ahorros'),
        ('corriente', 'Corriente')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    banco = models.CharField(max_length=100, verbose_name="Banco")
    numero_cuenta = models.CharField(max_length=50, verbose_name="Número de Cuenta")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Cuenta")
    moneda = models.CharField(max_length=3, default='USD', verbose_name="Moneda")
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Inicial")
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Saldo Actual")
    cuenta_contable = models.ForeignKey(PlanCuentas, on_delete=models.PROTECT, related_name='cuentas_bancarias', verbose_name="Cuenta Contable")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        ordering = ['banco', 'numero_cuenta']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_cuenta_bancaria_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.banco} - {self.numero_cuenta}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: CTA-{BANCO}-{CORRELATIVO}"""
        import re
        from unidecode import unidecode

        banco_limpio = unidecode(self.banco).upper()
        banco_limpio = re.sub(r'[^A-Z0-9]', '', banco_limpio)
        prefijo_banco = banco_limpio[:4] if len(banco_limpio) >= 4 else banco_limpio.ljust(4, 'X')

        patron_base = f"CTA-{prefijo_banco}-"
        ultimo = CuentaBancaria.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                correlativo = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:02d}"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class MovimientoBancario(BaseModel):
    """Movimientos bancarios (depósitos, retiros, transferencias)"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('deposito', 'Depósito'),
        ('retiro', 'Retiro'),
        ('transferencia', 'Transferencia'),
        ('nota_debito', 'Nota de Débito'),
        ('nota_credito', 'Nota de Crédito')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número", editable=False)
    fecha = models.DateField(verbose_name="Fecha")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, related_name='movimientos', verbose_name="Cuenta Bancaria")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    concepto = models.TextField(verbose_name="Concepto")
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="Número de Documento")
    beneficiario = models.CharField(max_length=200, blank=True, verbose_name="Beneficiario")
    asiento = models.ForeignKey(AsientoContable, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_bancarios', verbose_name="Asiento Contable")
    conciliado = models.BooleanField(default=False, verbose_name="Conciliado")

    # ==================== META ====================
    class Meta:
        verbose_name = "Movimiento Bancario"
        verbose_name_plural = "Movimientos Bancarios"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['cuenta_bancaria', 'fecha']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_movimiento_bancario_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.tipo} - {self.numero} - ${self.monto}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: MB-YYYYMMDD-####"""
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"MB-{fecha_str}-"

        ultimo = MovimientoBancario.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class ConciliacionBancaria(BaseModel):
    """Conciliaciones bancarias"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('conciliada', 'Conciliada'),
        ('cerrada', 'Cerrada')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número", editable=False)
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, related_name='conciliaciones', verbose_name="Cuenta Bancaria")
    fecha_inicio = models.DateField(verbose_name="Fecha Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha Fin")
    saldo_inicial_libro = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Inicial en Libros")
    saldo_final_libro = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Final en Libros")
    saldo_final_banco = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Final según Banco")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='conciliaciones', verbose_name="Responsable")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Conciliación Bancaria"
        verbose_name_plural = "Conciliaciones Bancarias"
        ordering = ['-fecha_fin']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_conciliacion_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Conciliación {self.numero} - {self.cuenta_bancaria}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: CONC-YYYYMMDD-####"""
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"CONC-{fecha_str}-"

        ultimo = ConciliacionBancaria.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class CuentaPorCobrar(BaseModel):
    """Cuentas por cobrar a clientes"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Cobro Parcial'),
        ('cobrada', 'Cobrada'),
        ('vencida', 'Vencida'),
        ('incobrable', 'Incobrable')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número", editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cuentas_cobrar', verbose_name="Cliente")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Total")
    monto_cobrado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Cobrado")
    saldo = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Pendiente")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Referencia (Factura, etc.)")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cuenta por Cobrar"
        verbose_name_plural = "Cuentas por Cobrar"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['cliente', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_cxc_empresa'),
        ]
        permissions = [
            ("gestionar_cobranza", "Puede gestionar cobranza"),
            ("declarar_incobrable", "Puede declarar cuentas como incobrables"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"CxC {self.numero} - {self.cliente}"

    # ==================== PROPERTIES ====================
    @property
    def dias_vencidos(self):
        """Calcula los días de vencimiento"""
        if self.fecha_vencimiento < date.today():
            return (date.today() - self.fecha_vencimiento).days
        return 0

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: CXC-YYYYMMDD-####"""
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"CXC-{fecha_str}-"

        ultimo = CuentaPorCobrar.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class CobroCuentaPorCobrar(BaseModel):
    """Cobros realizados a cuentas por cobrar"""

    # ==================== CHOICES ====================
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta')
    ]

    # ==================== CAMPOS ====================
    cuenta_cobrar = models.ForeignKey(CuentaPorCobrar, on_delete=models.PROTECT, related_name='cobros', verbose_name="Cuenta por Cobrar")
    fecha = models.DateField(verbose_name="Fecha de Cobro")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, verbose_name="Método de Pago")
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="Número de Documento")
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, null=True, blank=True, related_name='cobros', verbose_name="Cuenta Bancaria")
    asiento = models.ForeignKey(AsientoContable, on_delete=models.SET_NULL, null=True, blank=True, related_name='cobros', verbose_name="Asiento Contable")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cobro de Cuenta por Cobrar"
        verbose_name_plural = "Cobros de Cuentas por Cobrar"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['cuenta_cobrar', 'fecha']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Cobro ${self.monto} - {self.cuenta_cobrar.numero}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.monto > self.cuenta_cobrar.saldo:
            raise ValidationError("El monto del cobro no puede ser mayor al saldo pendiente")


class CuentaPorPagar(BaseModel):
    """Cuentas por pagar a proveedores"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número", editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='cuentas_pagar', verbose_name="Proveedor")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Total")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Pagado")
    saldo = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Saldo Pendiente")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    referencia = models.CharField(max_length=100, blank=True, verbose_name="Referencia (Factura, OC, etc.)")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Cuenta por Pagar"
        verbose_name_plural = "Cuentas por Pagar"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['proveedor', 'estado']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['numero', 'empresa'], name='unique_numero_cxp_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"CxP {self.numero} - {self.proveedor}"

    # ==================== PROPERTIES ====================
    @property
    def dias_vencidos(self):
        """Calcula los días de vencimiento"""
        if self.fecha_vencimiento < date.today():
            return (date.today() - self.fecha_vencimiento).days
        return 0

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: CXP-YYYYMMDD-####"""
        from django.utils import timezone
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"CXP-{fecha_str}-"

        ultimo = CuentaPorPagar.objects.filter(empresa=self.empresa, numero__startswith=patron_base).order_by('-numero').first()

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


class PagoCuentaPorPagar(BaseModel):
    """Pagos realizados a cuentas por pagar"""

    # ==================== CHOICES ====================
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque')
    ]

    # ==================== CAMPOS ====================
    cuenta_pagar = models.ForeignKey(CuentaPorPagar, on_delete=models.PROTECT, related_name='pagos', verbose_name="Cuenta por Pagar")
    fecha = models.DateField(verbose_name="Fecha de Pago")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES, verbose_name="Método de Pago")
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="Número de Documento")
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, null=True, blank=True, related_name='pagos', verbose_name="Cuenta Bancaria")
    asiento = models.ForeignKey(AsientoContable, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos', verbose_name="Asiento Contable")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Pago de Cuenta por Pagar"
        verbose_name_plural = "Pagos de Cuentas por Pagar"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['cuenta_pagar', 'fecha']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Pago ${self.monto} - {self.cuenta_pagar.numero}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.monto > self.cuenta_pagar.saldo:
            raise ValidationError("El monto del pago no puede ser mayor al saldo pendiente")


class Presupuesto(BaseModel):
    """Presupuestos anuales por centro de costo"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado')
    ]

    # ==================== CAMPOS ====================
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    año = models.IntegerField(verbose_name="Año")
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, related_name='presupuestos', verbose_name="Centro de Costo")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='presupuestos', verbose_name="Responsable")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ['-año']
        constraints = [
            models.UniqueConstraint(fields=['año', 'centro_costo', 'empresa'], name='unique_presupuesto_año_centro_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.nombre} - {self.año}"


class DetallePresupuesto(BaseModel):
    """Detalle mensual de presupuestos"""

    # ==================== CAMPOS ====================
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='detalles', verbose_name="Presupuesto")
    cuenta = models.ForeignKey(PlanCuentas, on_delete=models.PROTECT, related_name='detalles_presupuestos', verbose_name="Cuenta")
    enero = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Enero")
    febrero = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Febrero")
    marzo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Marzo")
    abril = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Abril")
    mayo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Mayo")
    junio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Junio")
    julio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Julio")
    agosto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Agosto")
    septiembre = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Septiembre")
    octubre = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Octubre")
    noviembre = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Noviembre")
    diciembre = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Diciembre")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Presupuesto"
        verbose_name_plural = "Detalles de Presupuesto"
        ordering = ['presupuesto', 'cuenta']
        constraints = [
            models.UniqueConstraint(fields=['presupuesto', 'cuenta', 'empresa'], name='unique_presupuesto_cuenta_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.cuenta.nombre} - Total: ${self.total_anual}"

    # ==================== PROPERTIES ====================
    @property
    def total_anual(self):
        """Calcula el total anual"""
        return (
            self.enero + self.febrero + self.marzo + self.abril +
            self.mayo + self.junio + self.julio + self.agosto +
            self.septiembre + self.octubre + self.noviembre + self.diciembre
        )