# apps/seguridad/models.py
import uuid

from apps.core.models import BaseModel, Empresa
from apps.personas.models import Persona
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

class Empleado(BaseModel):
    """Empleados de la empresa"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
        ('terminado', 'Terminado'),
        ('licencia', 'En Licencia'),
        ('vacaciones', 'De Vacaciones')
    ]

    # ==================== CAMPOS ====================
    rol = models.ForeignKey('seguridad.Rol', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Rol")
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='empleados', verbose_name="Persona")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Usuario del Sistema")
    puesto = models.ForeignKey('rrhh.Puesto', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Puesto")
    fecha_contratacion = models.DateField(verbose_name="Fecha de Contratación")
    fecha_terminacion = models.DateField(null=True, blank=True, verbose_name="Fecha de Terminación")
    salario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario Actual")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado del Empleado")
    departamento = models.ForeignKey('rrhh.Departamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados', verbose_name="Departamento")
    debe_cambiar_password = models.BooleanField(default=False, verbose_name='Debe cambiar contraseña')
    password_changed_at = models.DateTimeField(null=True, blank=True, verbose_name='Última cambio de contraseña')
    cuenta_activada = models.BooleanField(default=False, verbose_name='Cuenta activada')
    fecha_activacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de activación')

    # ==================== META ====================
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['persona__apellido1', 'persona__nombre1']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['persona']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_empleado_empresa'),
            models.UniqueConstraint(fields=['persona', 'empresa'], name='unique_empleado_per_empresa'),
            models.UniqueConstraint(fields=['usuario', 'empresa'], name='unique_usuario_empleado_empresa'),
        ]
        permissions = [
            ("ver_salarios", "Puede ver información salarial"),
            ("aprobar_ausencias", "Puede aprobar solicitudes de ausencia"),
            ("gestionar_nomina", "Puede gestionar nómina"),
            ("ver_reportes_rrhh", "Puede ver reportes de recursos humanos"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.persona.full_name()} - {self.empresa.nombre_comercial}"

    # ==================== PROPERTIES ====================
    @property
    def esta_activo(self):
        """Verifica si el empleado está activo"""
        return self.estado in ['activo', 'vacaciones', 'licencia'] and self.is_active

    # ==================== MÉTODOS PÚBLICOS ====================
    def get_full_name(self):
        """Retorna el nombre completo del empleado"""
        return self.persona.full_name()

    def activar_cuenta(self):
        """Marca la cuenta como activada"""
        self.cuenta_activada = True
        self.fecha_activacion = self.empresa.obtener_fecha_empresa()
        self.debe_cambiar_password = False
        self.save(update_fields=['cuenta_activada', 'fecha_activacion', 'debe_cambiar_password'])

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: EMP-{CORRELATIVO}"""
        patron_base = "EMP-"
        ultimo = Empleado.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

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

        if self.fecha_terminacion and self.fecha_terminacion < self.fecha_contratacion:
            raise ValidationError("La fecha de terminación no puede ser anterior a la fecha de contratación")

        if self.estado == 'terminado' and not self.fecha_terminacion:
            raise ValidationError("Debe especificar la fecha de terminación para empleados terminados")

    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class ActivationToken(models.Model):
    """Tokens de activación para nuevos empleados"""

    # ==================== CAMPOS ====================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='activation_tokens', verbose_name='Empleado')
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='Token')
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    expires_at = models.DateTimeField(verbose_name='Expira en')
    usado = models.BooleanField(default=False, verbose_name='Usado')
    fecha_uso = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de uso')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP de activación')
    user_agent = models.TextField(null=True, blank=True, verbose_name='Navegador')

    # ==================== META ====================
    class Meta:
        verbose_name = 'Token de Activación'
        verbose_name_plural = 'Tokens de Activación'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['token', 'usado', 'expires_at']),
            models.Index(fields=['empleado', 'usado']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Token para {self.empleado.persona.full_name()}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def is_valid(self):
        """Verifica si el token es válido"""
        return not self.usado and self.expires_at > timezone.now()

    def time_remaining(self):
        """Retorna tiempo restante hasta expiración"""
        if self.usado:
            return None

        delta = self.expires_at - timezone.now()

        if delta.total_seconds() <= 0:
            return "Expirado"

        hours = delta.total_seconds() // 3600
        minutes = (delta.total_seconds() % 3600) // 60

        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        return f"{int(minutes)}m"


class OTPToken(BaseModel):
    """Códigos OTP para reset de contraseña"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='otp_tokens', verbose_name='Empleado')
    otp = models.CharField(max_length=8, verbose_name='Código OTP')
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    expires_at = models.DateTimeField(verbose_name='Expira en')
    usado = models.BooleanField(default=False, verbose_name='Usado')
    fecha_uso = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de uso')
    intentos_fallidos = models.IntegerField(default=0, verbose_name='Intentos fallidos')
    bloqueado = models.BooleanField(default=False, verbose_name='Bloqueado por intentos')

    # ==================== META ====================
    class Meta:
        verbose_name = 'Token OTP'
        verbose_name_plural = 'Tokens OTP'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['empleado', 'usado', 'expires_at']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"OTP para {self.empleado.persona.full_name()}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def is_valid(self):
        """Verifica si el OTP es válido"""
        return not self.usado and not self.bloqueado and self.expires_at > timezone.now()

    def increment_failed_attempts(self):
        """Incrementa contador de intentos fallidos"""
        self.intentos_fallidos += 1

        if self.intentos_fallidos >= 3:
            self.bloqueado = True

        self.save(update_fields=['intentos_fallidos', 'bloqueado'])


class PasswordResetToken(BaseModel):
    """Tokens para reset de contraseña por email"""

    # ==================== CAMPOS ====================
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='password_reset_tokens', verbose_name='Empleado')
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='Token')
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    expires_at = models.DateTimeField(verbose_name='Expira en')
    usado = models.BooleanField(default=False, verbose_name='Usado')
    fecha_uso = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de uso')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP de reset')

    # ==================== META ====================
    class Meta:
        verbose_name = 'Token de Reset de Contraseña'
        verbose_name_plural = 'Tokens de Reset de Contraseña'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['token', 'usado', 'expires_at']),
            models.Index(fields=['empleado', 'usado']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Reset token para {self.empleado.persona.full_name()}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def is_valid(self):
        """Verifica si el token es válido"""
        return not self.usado and self.expires_at > timezone.now()


class Rol(BaseModel):
    """
    Rol de empleado con permisos técnicos (Django) y permisos de negocio.

    Combina:
    - Permisos técnicos via grupos Django (CRUD)
    - Permisos de negocio específicos del ERP
    - Metadata multi-tenant
    """

    # ==================== CAMPOS BÁSICOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Rol")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    nivel_jerarquico = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)], verbose_name="Nivel Jerárquico", help_text="1=más bajo, 10=más alto")

    # ==================== PERMISOS TÉCNICOS ====================
    grupos_django = models.ManyToManyField(Group, related_name='roles_empresa', blank=True, verbose_name="Grupos de Permisos Django")

    # ==================== PERMISOS DE NEGOCIO ====================
    monto_maximo_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Descuento Máximo (%)")
    monto_maximo_aprobacion = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Monto Máximo de Aprobación")
    limite_credito_clientes = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="Límite de Crédito a Clientes")
    puede_aprobar_vacaciones = models.BooleanField(default=False, verbose_name="Puede Aprobar Vacaciones")
    puede_ver_salarios = models.BooleanField(default=False, verbose_name="Puede Ver Salarios")
    puede_modificar_precios = models.BooleanField(default=False, verbose_name="Puede Modificar Precios")
    puede_anular_documentos = models.BooleanField(default=False, verbose_name="Puede Anular Documentos")

    # ==================== META ====================
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['-nivel_jerarquico', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_rol_empresa'),
            models.UniqueConstraint(fields=['nombre', 'empresa'], name='unique_nombre_rol_empresa'),
        ]
        permissions = [
            ("gestionar_roles", "Puede gestionar roles de la empresa"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.nombre} (Nivel {self.nivel_jerarquico}) - {self.empresa.nombre_comercial}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def tiene_permiso_django(self, codename):
        """Verifica si el rol tiene un permiso Django específico vía grupos"""
        return self.grupos_django.filter(
            permissions__codename=codename
        ).exists()

    def puede_aprobar_monto(self, monto):
        """Verifica si puede aprobar un monto específico"""
        return Decimal(str(monto)) <= self.monto_maximo_aprobacion

    def puede_dar_descuento(self, porcentaje):
        """Verifica si puede dar un descuento específico"""
        return Decimal(str(porcentaje)) <= self.monto_maximo_descuento

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: ROL-{CORRELATIVO}"""
        patron_base = "ROL-"
        ultimo = Rol.objects.filter(
            empresa=self.empresa,
            codigo__startswith=patron_base
        ).order_by('-codigo').first()

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
        super().clean()
        if self.monto_maximo_descuento > 100:
            raise ValidationError("El descuento máximo no puede superar el 100%")

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)