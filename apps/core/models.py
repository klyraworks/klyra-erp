import uuid
import pytz
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from apps.core.functions import validar_cedula_ecuatoriana, validar_pasaporte
from cities_light.models import SubRegion, Region, Country

class Empresa(models.Model):
    """Configuración de la empresa para facturación. Solo puede existir UNA empresa activa."""

    # ==================== CHOICES ====================
    MONEDA_CHOICES = [('USD', 'Dólar Estadounidense'), ('EUR', 'Euro')]
    TIPO_CONTRIBUYENTE_CHOICES = [
        ('persona_natural', 'Persona Natural con RUC'),
        ('persona_natural_sin_ruc', 'Persona Natural sin RUC'),
        ('sociedad', 'Sociedad/Empresa'),
    ]
    AMBIENTE_CHOICES = [('1', 'Pruebas'), ('2', 'Producción')]
    TIPO_EMISION_CHOICES = [('1', 'Normal'), ('2', 'Contingencia')]

    # ==================== CAMPOS ====================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruc = models.CharField(max_length=13, unique=True, verbose_name="RUC")
    razon_social = models.CharField(max_length=300, verbose_name="Razón Social")
    nombre_comercial = models.CharField(max_length=300, verbose_name="Nombre Comercial")
    direccion_matriz = models.TextField(verbose_name="Dirección Matriz")
    ciudad = models.CharField(max_length=100, default="Guayaquil")
    provincia = models.CharField(max_length=100, default="Guayas")
    pais = models.CharField(max_length=100, default="Ecuador")
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    celular = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(verbose_name="Email")
    sitio_web = models.URLField(blank=True, null=True, verbose_name="Sitio Web")
    obligado_contabilidad = models.BooleanField(default=True, verbose_name="Obligado a llevar Contabilidad")
    contribuyente_especial = models.CharField(max_length=10, blank=True, null=True, verbose_name="Resolución Contribuyente Especial")
    agente_retencion = models.BooleanField(default=False, verbose_name="Agente de Retención")
    ambiente_sri = models.CharField(max_length=1, choices=AMBIENTE_CHOICES, default='1', verbose_name="Ambiente SRI")
    tipo_emision = models.CharField(max_length=1, choices=TIPO_EMISION_CHOICES, default='1', verbose_name="Tipo de Emisión")
    establecimiento = models.CharField(max_length=3, default='001', verbose_name="Código Establecimiento")
    punto_emision = models.CharField(max_length=3, default='001', verbose_name="Punto de Emisión")
    secuencial_factura = models.IntegerField(default=1, verbose_name="Secuencial Factura")
    secuencial_nota_credito = models.IntegerField(default=1, verbose_name="Secuencial Nota de Crédito")
    secuencial_nota_debito = models.IntegerField(default=1, verbose_name="Secuencial Nota de Débito")
    secuencial_guia_remision = models.IntegerField(default=1, verbose_name="Secuencial Guía de Remisión")
    secuencial_retencion = models.IntegerField(default=1, verbose_name="Secuencial Retención")
    certificado_digital = models.FileField(upload_to='certificados/', blank=True, null=True, verbose_name="Certificado Digital (.p12)")
    clave_certificado = models.CharField(max_length=255, blank=True, null=True, verbose_name="Clave del Certificado")
    fecha_expiracion_certificado = models.DateField(blank=True, null=True, verbose_name="Fecha de Expiración del Certificado")
    logo = models.ImageField(upload_to='empresa/logos/', blank=True, null=True, verbose_name="Logo de la Empresa")
    color_primario = models.CharField(max_length=7, default='#212842', verbose_name="Color Primario (Hex)")
    color_secundario = models.CharField(max_length=7, default='#F0E7D5', verbose_name="Color Secundario (Hex)")
    slogan = models.CharField(max_length=200, blank=True, null=True, verbose_name="Slogan")
    informacion_adicional = models.TextField(blank=True, null=True, verbose_name="Información Adicional")
    subdominio = models.SlugField(max_length=50, unique=True, verbose_name="Subdominio")
    dias_validez_factura = models.IntegerField(default=30, verbose_name="Días de Validez de Factura")
    leyenda_factura = models.TextField(blank=True, null=True, verbose_name="Leyenda en Facturas")
    timezone = models.CharField(max_length=50, default='America/Guayaquil', verbose_name="Zona Horaria")
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='USD')
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tipo_contribuyente = models.CharField(max_length=30, choices=TIPO_CONTRIBUYENTE_CHOICES, default='sociedad', verbose_name="Tipo de Contribuyente")
    cedula = models.CharField(max_length=10, blank=True, null=True, verbose_name="Cédula")

    # ==================== META ====================
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Configuración de Empresa"
        ordering = ['-created_at']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.razon_social} - RUC: {self.ruc}"

    # ==================== MÉTODOS PÚBLICOS ====================
    @classmethod
    def get_empresa_activa(cls):
        """Obtiene la empresa activa (singleton)"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            raise ValidationError('No hay una empresa configurada. Configure la empresa en el sistema.')
        except cls.MultipleObjectsReturned:
            return cls.objects.filter(is_active=True).first()

    def generar_numero_factura(self):
        """Genera número de factura: 001-001-000000001"""
        from django.db.models import F

        numero = f"{self.establecimiento}-{self.punto_emision}-{self.secuencial_factura:09d}"
        Empresa.objects.filter(pk=self.pk).update(secuencial_factura=F('secuencial_factura') + 1)
        self.refresh_from_db()
        return numero

    def generar_numero_nota_credito(self):
        """Genera número de nota de crédito"""
        numero = f"{self.establecimiento}-{self.punto_emision}-{self.secuencial_nota_credito:09d}"
        self.secuencial_nota_credito += 1
        self.save(update_fields=['secuencial_nota_credito'])
        return numero

    def esta_certificado_vigente(self):
        """Verifica si el certificado digital está vigente"""
        if not self.fecha_expiracion_certificado:
            return False
        return self.fecha_expiracion_certificado > timezone.now().date()

    def puede_facturar_electronicamente(self):
        """Verifica si está listo para facturar electrónicamente"""
        return (
            self.certificado_digital and
            self.clave_certificado and
            self.esta_certificado_vigente()
        )

    def obtener_fecha_empresa(self):
        """Obtiene la fecha según la zona horaria de ESTA empresa"""
        empresa_tz = pytz.timezone(self.timezone)
        return timezone.now().astimezone(empresa_tz).date()

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones"""
        super().clean()

        if self.ruc and len(self.ruc) != 13:
            raise ValidationError({'ruc': 'El RUC debe tener 13 dígitos'})

        if len(self.establecimiento) != 3:
            raise ValidationError({'establecimiento': 'Debe tener 3 dígitos (Ej: 001)'})

        if len(self.punto_emision) != 3:
            raise ValidationError({'punto_emision': 'Debe tener 3 dígitos (Ej: 001)'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BaseModel(models.Model):
    """Modelo base abstracto con campos comunes"""

    # ==================== CAMPOS ====================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_updated')
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_deleted')
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='%(class)s_set')

    # ==================== META ====================
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa']),
            models.Index(fields=['is_active']),
            models.Index(fields=['deleted_at']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.__class__.__name__} - {self.id}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def soft_delete(self, user=None):
        """Eliminación suave - marca el registro como eliminado"""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.is_active = False
        self.save(update_fields=['deleted_at', 'deleted_by', 'is_active', 'updated_at'])

    def restore(self, user=None):
        """Restaurar un registro eliminado"""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True
        self.updated_by = user
        self.save(update_fields=['deleted_at', 'deleted_by', 'is_active', 'updated_at', 'updated_by'])

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Override save para auto-asignar empresa si no existe"""
        if not self.empresa_id:
            from apps.core.middleware.tenant_middleware import get_current_empresa
            empresa = get_current_empresa()
            if empresa:
                self.empresa = empresa
        super().save(*args, **kwargs)


class Persona(models.Model):
    """Datos personales de personas naturales"""

    # ==================== CAMPOS ====================
    nombre1 = models.CharField(max_length=100, verbose_name="Primer Nombre")
    nombre2 = models.CharField(max_length=100, verbose_name="Segundo Nombre", null=True, blank=True)
    apellido1 = models.CharField(max_length=100, verbose_name="Primer Apellido")
    apellido2 = models.CharField(max_length=100, verbose_name="Segundo Apellido", null=True, blank=True)
    cedula = models.CharField(max_length=10, verbose_name="Cédula", validators=[validar_cedula_ecuatoriana], null=True, blank=True)
    email = models.EmailField(verbose_name="Correo Electrónico", null=True, blank=True)
    telefono = models.CharField(max_length=10, null=True, blank=True, verbose_name="Número de Teléfono")
    direccion = models.ForeignKey(SubRegion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Dirección", related_name='personas')
    pasaporte = models.CharField(max_length=9, validators=[validar_pasaporte], null=True, blank=True, verbose_name="Número de Pasaporte")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='personas')

    # ==================== META ====================
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        unique_together = [('cedula', 'empresa')]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.nombre1} {self.apellido1}"

    # ==================== MÉTODOS PÚBLICOS ====================
    def full_name(self):
        """Retorna el nombre completo concatenado"""
        parts = [self.nombre1, self.nombre2, self.apellido1, self.apellido2]
        return " ".join(p.strip() for p in parts if p and p.strip())


class ConfiguracionCorreo(BaseModel):
    """Configuración de correo electrónico para envío de facturas"""

    # ==================== CAMPOS ====================
    servidor_smtp = models.CharField(max_length=255, default='smtp.gmail.com', verbose_name="Servidor SMTP")
    puerto_smtp = models.IntegerField(default=587, verbose_name="Puerto SMTP")
    usar_tls = models.BooleanField(default=True, verbose_name="Usar TLS")
    email_remitente = models.EmailField(verbose_name="Email Remitente")
    nombre_remitente = models.CharField(max_length=200, verbose_name="Nombre del Remitente")
    password_email = models.CharField(max_length=255, verbose_name="Contraseña del Email")
    asunto_factura = models.CharField(max_length=200, default='Factura Electrónica #{numero}', verbose_name="Asunto del Correo")
    mensaje_factura = models.TextField(default='''Estimado/a {cliente},\n\nAdjunto encontrará su factura electrónica #{numero} por un valor de ${total}.\n\nGracias por su compra.\n\nSaludos,\n{empresa}''', verbose_name="Mensaje del Correo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Configuración de Correo"
        verbose_name_plural = "Configuración de Correo"

    # ==================== __str__ ====================
    def __str__(self):
        return f"Correo: {self.email_remitente}"


class Sucursal(BaseModel):
    """
    Sucursales de la empresa
    Código: SUC-0001
    """

    # ==================== CAMPOS ====================
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sucursales')
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=200)

    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    es_principal = models.BooleanField(default=False)
    es_activo = models.BooleanField(default=True)

    # ==================== META ====================
    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        unique_together = [['empresa', 'codigo']]
        ordering = ['codigo']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Sucursal.objects.filter(
                empresa=self.empresa
            ).order_by('-codigo').first()

            if ultimo and ultimo.codigo.startswith('SUC-'):
                numero = int(ultimo.codigo.split('-')[1]) + 1
            else:
                numero = 1

            self.codigo = f"SUC-{numero:04d}"

        # Si es principal, quitar flag de otras
        if self.es_principal:
            Sucursal.objects.filter(
                empresa=self.empresa,
                es_principal=True
            ).exclude(id=self.id).update(es_principal=False)

        super().save(*args, **kwargs)