# MODELOS - RRHH
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseModel, Persona
# from apps.seguridad.models import Empleado


class Departamento(BaseModel):
    """Departamentos organizacionales de la empresa"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Departamento")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    jefe = models.ForeignKey('seguridad.Empleado', on_delete=models.SET_NULL, null=True, blank=True, related_name='departamentos_a_cargo', verbose_name="Jefe de Departamento")

    # ==================== META ====================
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_departamento_empresa'),
            models.UniqueConstraint(fields=['nombre', 'empresa'], name='unique_nombre_departamento_empresa'),
        ]
        permissions = [
            ("ver_organigrama", "Puede ver el organigrama completo"),
            ("gestionar_departamentos", "Puede crear y modificar departamentos"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return self.nombre

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: DEPT-{PREFIJO}-{CORRELATIVO}"""
        from unidecode import unidecode
        import re

        prefijo = self._generar_prefijo_nombre()
        correlativo = self._generar_correlativo(prefijo)
        return f"DEPT-{prefijo}-{correlativo}"

    def _generar_prefijo_nombre(self):
        """Genera prefijo de 3-5 caracteres del nombre del departamento"""
        from unidecode import unidecode
        import re

        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'Y', 'DEPARTAMENTO']
        palabras = [p for p in nombre.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre]

        if len(palabras) == 1:
            palabra = palabras[0]
            prefijo = palabra if len(palabra) <= 5 else palabra[:5]
        else:
            prefijo = ''.join([p[0] for p in palabras[:4]])
            if len(prefijo) < 3:
                prefijo = palabras[0][:3]

        prefijo = re.sub(r'[^A-Z0-9]', '', prefijo)

        if len(prefijo) < 3:
            prefijo = prefijo.ljust(3, 'X')
        elif len(prefijo) > 5:
            prefijo = prefijo[:5]

        return prefijo

    def _generar_correlativo(self, prefijo):
        """Genera correlativo de 2 dígitos"""
        patron_base = f"DEPT-{prefijo}-"
        ultimo = Departamento.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                return f"{int(ultimo.codigo.split('-')[-1]) + 1:02d}"
            except (ValueError, IndexError):
                return "01"
        return "01"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class Puesto(BaseModel):
    """Puestos de trabajo disponibles en la empresa"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Puesto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción del Puesto")
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='puestos', verbose_name="Departamento")
    salario_minimo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario Mínimo")
    salario_maximo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario Máximo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_puesto_empresa'),
            models.UniqueConstraint(fields=['nombre', 'empresa'], name='unique_nombre_puesto_empresa'),
        ]
        permissions = [
            ("ver_puestos", "Puede ver puestos de trabajo"),
            ("gestionar_puestos", "Puede crear y modificar puestos de trabajo"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return self.nombre

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: PUE-{PREFIJO}-{CORRELATIVO}"""
        from unidecode import unidecode
        import re

        prefijo = self._generar_prefijo_nombre()
        correlativo = self._generar_correlativo(prefijo)
        return f"PUE-{prefijo}-{correlativo}"

    def _generar_prefijo_nombre(self):
        """Genera prefijo de 3-5 caracteres del nombre del puesto"""
        from unidecode import unidecode
        import re

        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'Y']
        palabras = [p for p in nombre.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre]

        if len(palabras) == 1:
            palabra = palabras[0]
            prefijo = palabra if len(palabra) <= 5 else palabra[:5]
        else:
            prefijo = ''.join([p[0] for p in palabras[:4]])
            if len(prefijo) < 3:
                prefijo = palabras[0][:3]

        prefijo = re.sub(r'[^A-Z0-9]', '', prefijo)

        if len(prefijo) < 3:
            prefijo = prefijo.ljust(3, 'X')
        elif len(prefijo) > 5:
            prefijo = prefijo[:5]

        return prefijo

    def _generar_correlativo(self, prefijo):
        """Genera correlativo de 2 dígitos"""
        patron_base = f"PUE-{prefijo}-"
        ultimo = Puesto.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                return f"{int(ultimo.codigo.split('-')[-1]) + 1:02d}"
            except (ValueError, IndexError):
                return "01"
        return "01"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.salario_maximo < self.salario_minimo:
            raise ValidationError("El salario máximo no puede ser menor que el salario mínimo")

    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class HistorialPuesto(BaseModel):
    """Historial de cambios de puesto de empleados"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey('seguridad.Empleado', on_delete=models.CASCADE, related_name='historial_puestos', verbose_name="Empleado")
    puesto = models.CharField(max_length=100, verbose_name="Puesto")
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='historiales_puestos', verbose_name="Departamento")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin")
    salario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario")
    motivo_cambio = models.TextField(blank=True, verbose_name="Motivo del Cambio")

    # ==================== META ====================
    class Meta:
        verbose_name = "Historial de Puesto"
        verbose_name_plural = "Historial de Puestos"
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['empleado', 'fecha_inicio']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.empleado.persona.full_name()} - {self.puesto} ({self.fecha_inicio})"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")


class PeriodoNomina(BaseModel):
    """Períodos de nómina para procesamiento de pagos"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('procesada', 'Procesada'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada')
    ]

    # ==================== CAMPOS ====================
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Período")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")

    # ==================== META ====================
    class Meta:
        verbose_name = "Período de Nómina"
        verbose_name_plural = "Períodos de Nómina"
        ordering = ['-fecha_inicio']
        constraints = [
            models.UniqueConstraint(fields=['fecha_inicio', 'fecha_fin', 'empresa'], name='unique_periodo_nomina_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.nombre} - {self.fecha_pago}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")

        if self.fecha_pago < self.fecha_fin:
            raise ValidationError("La fecha de pago debe ser igual o posterior a la fecha de fin del período")


class Nomina(BaseModel):
    """Nómina de empleados por período"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey('seguridad.Empleado', on_delete=models.CASCADE, related_name='nominas', verbose_name="Empleado")
    periodo = models.ForeignKey(PeriodoNomina, on_delete=models.PROTECT, related_name='nominas', verbose_name="Período")
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario Base")
    bonos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Bonos y Comisiones")
    horas_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Horas Extra")
    deducciones = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Deducciones")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total a Pagar", editable=False)
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Nómina"
        verbose_name_plural = "Nóminas"
        ordering = ['-periodo__fecha_inicio']
        constraints = [
            models.UniqueConstraint(fields=['empleado', 'periodo', 'empresa'], name='unique_nomina_empleado_periodo_empresa')
        ]
        permissions = [
            ("aprobar_nomina", "Puede aprobar nóminas"),
            ("ver_todas_nominas", "Puede ver nóminas de todos los empleados"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Nómina de {self.empleado.persona.full_name()} - {self.periodo.nombre}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def calcular_total(self):
        """Calcula el total a pagar"""
        return self.salario_base + self.bonos + self.horas_extra - self.deducciones

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Calcula total automáticamente"""
        self.total = self.calcular_total()
        super().save(*args, **kwargs)


class Ausencia(BaseModel):
    """Solicitudes de ausencia de empleados"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('vacaciones', 'Vacaciones'),
        ('permiso', 'Permiso Personal'),
        ('licencia_medica', 'Licencia Médica'),
        ('licencia_maternidad', 'Licencia de Maternidad'),
        ('licencia_paternidad', 'Licencia de Paternidad'),
        ('permiso_estudio', 'Permiso de Estudio'),
        ('calamidad', 'Calamidad Doméstica')
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada')
    ]

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey('seguridad.Empleado', on_delete=models.CASCADE, related_name='ausencias', verbose_name="Empleado")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo de Ausencia")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    motivo = models.TextField(verbose_name="Motivo")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    aprobado_por = models.ForeignKey('seguridad.Empleado', on_delete=models.SET_NULL, null=True, blank=True, related_name='ausencias_aprobadas', verbose_name="Aprobado por")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    comentarios_aprobacion = models.TextField(blank=True, verbose_name="Comentarios de Aprobación")

    # ==================== META ====================
    class Meta:
        verbose_name = "Ausencia"
        verbose_name_plural = "Ausencias"
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['empleado', 'fecha_inicio']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.empleado.get_full_name()} - {self.get_tipo_display()} ({self.fecha_inicio})"

    # ==================== PROPERTIES ====================
    @property
    def dias_solicitados(self):
        """Calcula los días solicitados"""
        return (self.fecha_fin - self.fecha_inicio).days + 1

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")


class Asistencia(BaseModel):
    """Registro de asistencia de empleados"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey('seguridad.Empleado', on_delete=models.CASCADE, related_name='asistencias', verbose_name="Empleado")
    fecha = models.DateField(verbose_name="Fecha")
    hora_entrada = models.TimeField(verbose_name="Hora de Entrada")
    hora_salida = models.TimeField(blank=True, null=True, verbose_name="Hora de Salida")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = ['-fecha', '-hora_entrada']
        constraints = [
            models.UniqueConstraint(fields=['empleado', 'fecha', 'hora_entrada', 'empresa'], name='unique_asistencia_empleado_fecha_empresa')
        ]
        permissions = [
            ("ver_todas_asistencias", "Puede ver asistencias de todos los empleados"),
            ("marcar_asistencia_otros", "Puede marcar asistencia de otros empleados"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Asistencia de {self.empleado.persona.full_name()} - {self.fecha}"

    # ==================== PROPERTIES ====================
    @property
    def horas_trabajadas(self):
        """Calcula las horas trabajadas"""
        if not self.hora_salida:
            return None

        entrada = datetime.combine(self.fecha, self.hora_entrada)
        salida = datetime.combine(self.fecha, self.hora_salida)

        if salida < entrada:
            salida += timedelta(days=1)

        diferencia = salida - entrada
        return diferencia.total_seconds() / 3600

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.hora_salida and self.hora_salida <= self.hora_entrada:
            raise ValidationError("La hora de salida debe ser posterior a la hora de entrada")


class Evaluacion(BaseModel):
    """Evaluaciones de desempeño de empleados"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey('seguridad.Empleado', on_delete=models.CASCADE, related_name='evaluaciones', verbose_name="Empleado Evaluado")
    evaluador = models.ForeignKey('seguridad.Empleado', on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluaciones_realizadas', verbose_name="Evaluador")
    periodo = models.CharField(max_length=100, verbose_name="Período Evaluado")
    fecha_evaluacion = models.DateField(verbose_name="Fecha de Evaluación")
    calificacion = models.IntegerField(verbose_name="Calificación")
    fortalezas = models.TextField(verbose_name="Fortalezas")
    areas_mejora = models.TextField(verbose_name="Áreas de Mejora")
    comentarios = models.TextField(blank=True, verbose_name="Comentarios Adicionales")
    objetivos = models.TextField(blank=True, verbose_name="Objetivos para el Siguiente Período")

    # ==================== META ====================
    class Meta:
        verbose_name = "Evaluación de Desempeño"
        verbose_name_plural = "Evaluaciones de Desempeño"
        ordering = ['-fecha_evaluacion']
        permissions = [
            ("realizar_evaluaciones", "Puede realizar evaluaciones de desempeño"),
            ("ver_todas_evaluaciones", "Puede ver todas las evaluaciones"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Evaluación de {self.empleado.persona.full_name()} - {self.periodo}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if not (1 <= self.calificacion <= 10):
            raise ValidationError("La calificación debe estar entre 1 y 10")
