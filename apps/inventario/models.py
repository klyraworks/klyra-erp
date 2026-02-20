# MODELOS - INVENTARIO
import re
from datetime import date

from apps.core.models import BaseModel
from apps.seguridad.models import Empleado
from cities_light.models import Country, SubRegion
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from unidecode import unidecode


class Categoria(BaseModel):
    """Categorías jerárquicas para productos"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria_padre = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='categorias_hijas', verbose_name="Categoría Padre")
    nivel = models.IntegerField(default=1, verbose_name="Nivel en Jerarquía")
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True, verbose_name="Imagen")

    # ==================== META ====================
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['codigo']
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_categoria_empresa'),
        ]
        permissions = [
            ("ver_jerarquia_categorias", "Puede ver jerarquía completa de categorías")
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: {PREFIJO}-{CORRELATIVO}"""
        prefijo = self._generar_prefijo_nombre()
        correlativo = self._generar_correlativo(prefijo)
        return f"{prefijo}-{correlativo}"

    def _generar_prefijo_nombre(self):
        """Genera prefijo de 3-5 caracteres del nombre"""
        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'PARA', 'CON', 'EN', 'Y']
        palabras = [p for p in nombre.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre]

        if len(palabras) == 1:
            palabra = palabras[0]
            if len(palabra) <= 5:
                prefijo = palabra
            else:
                consonantes = re.sub(r'[AEIOU\s\-\_]', '', palabra)
                prefijo = consonantes[:5] if len(consonantes) >= 3 else palabra[:5]
        else:
            if len(palabras) <= 2:
                prefijo = palabras[0][:3] + (palabras[1][:2] if len(palabras[1]) >= 2 else '')
            else:
                letras = [p[0] for p in palabras[:4]]
                prefijo = ''.join(letras)
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
        patron_base = f"{prefijo}-"
        ultima = Categoria.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultima:
            try:
                return f"{int(ultima.codigo.split('-')[-1]) + 1:02d}"
            except (ValueError, IndexError):
                return "01"
        return "01"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones y cálculo de nivel"""
        super().clean()

        if self.categoria_padre:
            self.nivel = self.categoria_padre.nivel + 1
        else:
            self.nivel = 1

    def save(self, *args, **kwargs):
        """Genera código automático y calcula nivel"""
        if not self.codigo:
            self.codigo = self._generar_codigo()

        if self.categoria_padre:
            self.nivel = self.categoria_padre.nivel + 1
        else:
            self.nivel = 1

        super().save(*args, **kwargs)


class Marca(BaseModel):
    """Marcas de productos"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    pais_origen = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcas', verbose_name="País de Origen")
    logo = models.ImageField(upload_to='marcas/', null=True, blank=True, verbose_name="Logo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['nombre', 'empresa'], name='unique_marca_nombre_per_empresa'),
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_marca_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return self.nombre

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: MRC-{PREFIJO}-{CORRELATIVO}"""
        prefijo = self._generar_prefijo_nombre()
        correlativo = self._generar_correlativo(prefijo)
        return f"MRC-{prefijo}-{correlativo}"

    def _generar_prefijo_nombre(self):
        """Genera prefijo de 3-5 caracteres del nombre de la marca"""
        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'Y', 'S.A.', 'SA', 'LTDA', 'CIA', 'CO']
        palabras = [p for p in nombre.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre]

        if len(palabras) == 1:
            palabra = palabras[0]
            prefijo = palabra if len(palabra) <= 5 else palabra[:5]
        else:
            if len(palabras) == 2:
                prefijo = palabras[0][:3] + palabras[1][:2]
            else:
                prefijo = palabras[0][:2] + palabras[1][:2] + (palabras[2][:1] if len(palabras) > 2 else '')

        prefijo = re.sub(r'[^A-Z0-9]', '', prefijo)

        if len(prefijo) < 3:
            prefijo = prefijo.ljust(3, 'X')
        elif len(prefijo) > 5:
            prefijo = prefijo[:5]

        return prefijo

    def _generar_correlativo(self, prefijo):
        """Genera correlativo de 2 dígitos"""
        patron_base = f"MRC-{prefijo}-"
        ultima = Marca.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultima:
            try:
                return f"{int(ultima.codigo.split('-')[-1]) + 1:02d}"
            except (ValueError, IndexError):
                return "01"
        return "01"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class UnidadMedida(models.Model):
    """Unidades de medida para productos"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('unidad', 'Unidad'),
        ('peso', 'Peso'),
        ('volumen', 'Volumen'),
        ('longitud', 'Longitud'),
        ('area', 'Área'),
        ('tiempo', 'Tiempo')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    abreviatura = models.CharField(max_length=10, verbose_name="Abreviatura")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='unidad', verbose_name="Tipo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nombre']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: {PREFIJO_TIPO}-{ABREVIATURA}"""
        prefijo_tipo = self._obtener_prefijo_tipo()
        abrev_limpia = self._limpiar_abreviatura()
        codigo = f"{prefijo_tipo}-{abrev_limpia}"

        if UnidadMedida.objects.filter(codigo=codigo).exists():
            correlativo = self._generar_correlativo(prefijo_tipo, abrev_limpia)
            codigo = f"{prefijo_tipo}-{abrev_limpia}{correlativo}"

        return codigo

    def _obtener_prefijo_tipo(self):
        """Obtiene prefijo según el tipo de unidad"""
        prefijos = {
            'unidad': 'UNI',
            'peso': 'PESO',
            'volumen': 'VOL',
            'longitud': 'LONG',
            'area': 'AREA',
            'tiempo': 'TIME'
        }
        return prefijos.get(self.tipo, 'UNI')

    def _limpiar_abreviatura(self):
        """Limpia y normaliza la abreviatura"""
        abrev = unidecode(self.abreviatura).upper()
        abrev = abrev.replace('²', '2').replace('³', '3').replace('°', 'DEG')
        abrev = re.sub(r'[^A-Z0-9]', '', abrev)
        return abrev[:5] if len(abrev) > 5 else abrev

    def _generar_correlativo(self, prefijo_tipo, abrev_limpia):
        """Genera correlativo si ya existe la combinación"""
        patron_base = f"{prefijo_tipo}-{abrev_limpia}"
        return UnidadMedida.objects.filter(codigo__startswith=patron_base).count() + 1

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)


class Producto(BaseModel):
    """Modelo de producto del inventario"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('simple', 'Producto Simple'),
        ('kit', 'Kit/Paquete'),
        ('servicio', 'Servicio')
    ]

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=50, verbose_name="Código", editable=False)
    codigo_aux = models.CharField(max_length=50, verbose_name="Código Auxiliar", blank=True, null=True)
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT, related_name='productos', verbose_name="Categoría", blank=True, null=True)
    marca = models.ForeignKey('Marca', on_delete=models.SET_NULL, null=True, blank=True, related_name='productos', verbose_name="Marca")
    unidad_medida = models.ForeignKey('UnidadMedida', on_delete=models.PROTECT, related_name='productos', verbose_name="Unidad de Medida", blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='simple', verbose_name="Tipo de Producto")
    es_kit = models.BooleanField(default=False, verbose_name="Es Kit/Paquete")
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta Sugerido")
    stock_minimo = models.IntegerField(default=0, verbose_name="Stock Mínimo")
    iva = models.BooleanField(default=True, verbose_name="Aplica IVA")
    codigo_barras = models.CharField(max_length=50, blank=True, verbose_name="Código de Barras")
    es_perecedero = models.BooleanField(default=False, verbose_name="Es Perecedero")
    dias_vida_util = models.IntegerField(null=True, blank=True, verbose_name="Días de Vida Útil")
    peso = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Peso (kg)")
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, verbose_name="Imagen")
    costo_promedio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo Promedio Global")
    ultimo_costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Último Costo de Compra")

    # ==================== META ====================
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['empresa', 'nombre']),
            models.Index(fields=['categoria']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_producto_empresa'),
            models.UniqueConstraint(fields=['codigo_aux', 'empresa'], condition=Q(codigo_aux__isnull=False), name='unique_codigo_aux_not_null_empresa'),
        ]
        permissions = [
            ("ajustar_precios", "Puede ajustar precios de productos"),
            ("ver_costo_compra", "Puede ver precio de compra"),
            ("gestionar_kits", "Puede gestionar kits y componentes"),
            ("ajustar_stock", "Puede ajustar stock manualmente"),
            ("ver_reportes_producto", "Puede ver reportes y estadísticas"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== PROPERTIES ====================
    @property
    def margen_ganancia(self):
        """Calcula margen de ganancia porcentual"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0

    @property
    def stock_total(self):
        """Stock total en todas las bodegas"""
        return self.stocks.aggregate(total=Sum('cantidad'))['total'] or 0

    @property
    def necesita_reposicion(self):
        """Indica si necesita reposición"""
        return self.stock_total <= self.stock_minimo

    @property
    def stock_total_componentes(self):
        """Calcula cuántos kits se pueden armar con el stock disponible"""
        if not self.es_kit:
            return self.stock_total

        componentes = self.componentes.all()
        if not componentes.exists():
            return 0

        min_kits = float('inf')
        for componente in componentes:
            stock_componente = componente.componente.stock_total
            kits_posibles = stock_componente // componente.cantidad
            min_kits = min(min_kits, kits_posibles)

        return int(min_kits) if min_kits != float('inf') else 0

    # ==================== MÉTODOS PÚBLICOS ====================
    def actualizar_costo_promedio_global(self):
        """Recalcula el costo promedio global basado en todas las bodegas"""
        totales = self.stocks.aggregate(
            total_valor=Sum(F('cantidad') * F('costo_promedio_bodega')),
            total_cantidad=Sum('cantidad')
        )

        if totales['total_cantidad'] and totales['total_cantidad'] > 0:
            self.costo_promedio = totales['total_valor'] / totales['total_cantidad']
            self.save(update_fields=['costo_promedio'])

    # ==================== MÉTODOS PRIVADOS ====================
    def _inicializar_stock_bodegas(self):
        """Crea stock en todas las bodegas activas"""
        from apps.inventario.models import Bodega, Stock

        bodegas = Bodega.objects.filter(empresa=self.empresa, is_active=True, deleted_at__isnull=True)

        stocks = [
            Stock(
                empresa=self.empresa,
                producto=self,
                bodega=bodega,
                cantidad=0,
                stock_reservado=0,
                costo_promedio_bodega=self.precio_compra
            )
            for bodega in bodegas
        ]

        Stock.objects.bulk_create(stocks, ignore_conflicts=True)

    def _generar_codigo(self):
        """Genera código único: PRODUCTO-CATEGORIA-0001"""
        prefijo_producto = self._generar_prefijo_producto()
        prefijo_categoria = self._generar_prefijo_categoria()
        correlativo = self._generar_correlativo(prefijo_producto, prefijo_categoria)
        return f"{prefijo_producto}-{prefijo_categoria}-{correlativo}"

    def _generar_prefijo_producto(self):
        """Genera prefijo del producto basado en el nombre"""
        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'PARA', 'CON', 'EN']
        palabras = [p for p in nombre.split() if p not in stopwords]

        if not palabras:
            palabras = [nombre]

        if len(palabras) == 1:
            palabra = palabras[0]
            consonantes = re.sub(r'[AEIOU\s\-\_]', '', palabra)
            prefijo = consonantes[:5] if len(consonantes) >= 4 else palabra[:5]
        else:
            prefijo = ''.join([p[0] for p in palabras[:4]])
            if len(prefijo) < 4:
                primera_palabra = palabras[0]
                consonantes = re.sub(r'[AEIOU\s\-\_]', '', primera_palabra)
                prefijo = prefijo + consonantes[:4 - len(prefijo)]

        prefijo = re.sub(r'[^A-Z0-9]', '', prefijo)

        if len(prefijo) < 3:
            prefijo = prefijo.ljust(3, 'X')
        elif len(prefijo) > 5:
            prefijo = prefijo[:5]

        return prefijo

    def _generar_prefijo_categoria(self):
        """Genera prefijo de 3 caracteres de la categoría"""
        if self.categoria and self.categoria.codigo:
            codigo_cat = unidecode(self.categoria.codigo).upper()
            codigo_cat = re.sub(r'[^A-Z0-9]', '', codigo_cat)
            return codigo_cat[:3].ljust(3, 'X')
        return "GEN"

    def _generar_correlativo(self, prefijo_producto, prefijo_categoria):
        """Genera correlativo de 4 dígitos"""
        patron_base = f"{prefijo_producto}-{prefijo_categoria}-"
        ultimo = Producto.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                return f"{int(ultimo.codigo.split('-')[-1]) + 1:04d}"
            except (ValueError, IndexError):
                return "0001"
        return "0001"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.es_kit and self.tipo != 'kit':
            self.tipo = 'kit'

        if self.tipo == 'kit':
            self.es_kit = True

        if self.es_perecedero and not self.dias_vida_util:
            raise ValidationError("Los productos perecederos deben tener días de vida útil")

    def save(self, *args, **kwargs):
        """Genera código automático e inicializa stock"""
        is_new = self.pk is None

        if not self.codigo:
            self.codigo = self._generar_codigo()

        super().save(*args, **kwargs)

        if is_new:
            self._inicializar_stock_bodegas()


class Bodega(BaseModel):
    """Bodegas para almacenamiento de productos"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    ciudad = models.ForeignKey(SubRegion, on_delete=models.SET_NULL, null=True, blank=True, related_name='bodegas', verbose_name="Ciudad de ubicación")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    capacidad_m3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Capacidad (m³)")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='bodegas_responsable', verbose_name="Responsable")
    es_principal = models.BooleanField(default=False, verbose_name="Es Bodega Principal")
    permite_ventas = models.BooleanField(default=True, verbose_name="Permite Ventas Directas")

    # ==================== META ====================
    class Meta:
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_bodega_empresa'),
            models.UniqueConstraint(fields=['nombre', 'empresa'], name='unique_nombre_bodega_per_empresa'),
        ]
        permissions = [
            ("ver_todas_bodegas", "Puede ver todas las bodegas"),
            ("transferir_entre_bodegas", "Puede realizar transferencias entre bodegas"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _inicializar_stock_productos(self):
        """Crea stock para todos los productos activos"""
        from apps.inventario.models import Producto, Stock

        productos = Producto.objects.filter(empresa=self.empresa, is_active=True, deleted_at__isnull=True)

        stocks = [
            Stock(
                empresa=self.empresa,
                producto=producto,
                bodega=self,
                cantidad=0,
                stock_reservado=0,
                costo_promedio_bodega=producto.precio_compra
            )
            for producto in productos
        ]

        Stock.objects.bulk_create(stocks, ignore_conflicts=True)

    def _generar_codigo(self):
        """Genera código único: BOD-{PREFIJO}-{CORRELATIVO}"""
        prefijo = self._generar_prefijo_nombre()
        correlativo = self._generar_correlativo(prefijo)
        return f"BOD-{prefijo}-{correlativo}"

    def _generar_prefijo_nombre(self):
        """Genera prefijo de 3-5 caracteres del nombre de la bodega"""
        nombre = unidecode(self.nombre).upper()
        stopwords = ['DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'BODEGA']
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
        patron_base = f"BOD-{prefijo}-"
        ultima = Bodega.objects.filter(codigo__startswith=patron_base).order_by('-codigo').first()

        if ultima:
            try:
                return f"{int(ultima.codigo.split('-')[-1]) + 1:02d}"
            except (ValueError, IndexError):
                return "01"
        return "01"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático e inicializa stock"""
        is_new = self.pk is None

        if not self.codigo:
            self.codigo = self._generar_codigo()

        super().save(*args, **kwargs)

        if is_new:
            self._inicializar_stock_productos()


class Ubicacion(BaseModel):
    """Ubicaciones físicas dentro de las bodegas"""

    # ==================== CAMPOS ====================
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='ubicaciones', verbose_name="Bodega")
    pasillo = models.CharField(max_length=20, verbose_name="Pasillo")
    estante = models.CharField(max_length=20, verbose_name="Estante")
    nivel = models.CharField(max_length=20, verbose_name="Nivel")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    # ==================== META ====================
    class Meta:
        verbose_name = "Ubicación en Bodega"
        verbose_name_plural = "Ubicaciones en Bodegas"
        ordering = ['bodega', 'pasillo', 'estante', 'nivel']
        constraints = [
            models.UniqueConstraint(fields=['bodega', 'pasillo', 'estante', 'nivel', 'empresa'], name='unique_ubicacion_bodega_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.bodega.codigo} - {self.pasillo}/{self.estante}/{self.nivel}"


class Stock(BaseModel):
    """Stock de un producto en una bodega específica"""

    # ==================== CAMPOS ====================
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stocks', verbose_name="Producto")
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='stocks', verbose_name="Bodega")
    cantidad = models.IntegerField(default=0, verbose_name="Cantidad en Stock")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks', verbose_name="Ubicación en Bodega")
    stock_reservado = models.IntegerField(default=0, verbose_name="Stock Reservado")
    costo_promedio_bodega = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo Promedio en esta Bodega")
    precio_venta_bodega = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta Específico")

    # ==================== META ====================
    class Meta:
        verbose_name = "Stock por Bodega"
        verbose_name_plural = "Stock por Bodegas"
        ordering = ['bodega', 'producto']
        indexes = [
            models.Index(fields=['empresa', 'producto', 'bodega']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['producto', 'bodega', 'empresa'], name='unique_producto_bodega_empresa')
        ]
        permissions = [
            ('view_stock_todas_bodegas', 'Puede ver inventario de todas las bodegas'),
            ('view_stock_valorizado', 'Puede ver valores monetarios del inventario'),
            ('exportar_stock', 'Puede exportar reportes de inventario'),
            ('ajustar_precio_bodega', 'Puede ajustar precio de venta por bodega'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} - {self.bodega.nombre}: {self.cantidad}"

    # ==================== PROPERTIES ====================
    @property
    def precio_venta_efectivo(self):
        """Precio que se usará para vender en esta bodega"""
        return self.precio_venta_bodega if self.precio_venta_bodega is not None else self.producto.precio_venta

    @property
    def cantidad_disponible(self):
        """Cantidad disponible para venta (sin reservas)"""
        return max(0, self.cantidad - self.stock_reservado)

    @property
    def valor_inventario(self):
        """Valorización del stock en esta bodega"""
        return self.cantidad * self.costo_promedio_bodega

    # ==================== MÉTODOS PRIVADOS ====================
    @staticmethod
    def _generar_referencia_reserva(tipo='reservar'):
        """Genera referencia única para reservas/liberaciones: RES-YYYYMMDD-####"""
        fecha_hoy = date.today().strftime('%Y%m%d')
        prefix = f"RES-{fecha_hoy}" if tipo == 'reservar' else f"LIB-{fecha_hoy}"

        hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoy_fin = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        count = Stock.objects.filter(updated_at__range=(hoy_inicio, hoy_fin)).count()
        nuevo_numero = count + 1

        return f"{prefix}-{nuevo_numero:04d}"


class MovimientoInventario(BaseModel):
    """Movimientos de inventario (entradas, salidas, transferencias, ajustes)"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('transferencia', 'Transferencia'),
        ('ajuste', 'Ajuste de Inventario'),
        ('devolucion', 'Devolución'),
        ('merma', 'Merma/Pérdida')
    ]
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aplicado', 'Aplicado'),
        ('anulado', 'Anulado')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Movimiento", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Movimiento")
    bodega_origen = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='movimientos_origen', null=True, blank=True, verbose_name="Bodega Origen")
    bodega_destino = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='movimientos_destino', null=True, blank=True, verbose_name="Bodega Destino")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_inventario', verbose_name="Empleado Responsable")
    referencia = models.CharField(max_length=100, blank=True, default='', verbose_name="Referencia Externa")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    autorizado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_autorizados', verbose_name="Autorizado por")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")

    # ==================== META ====================
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
            models.Index(fields=['empresa', 'tipo', 'fecha']),
        ]
        permissions = [
            ("autorizar_movimiento", "Puede autorizar movimientos de inventario"),
            ("ver_todos_movimientos", "Puede ver todos los movimientos"),
            ("anular_movimiento", "Puede anular movimientos de inventario"),
            ("ver_kardex", "Puede ver kardex de productos"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.tipo.upper()} {self.numero} - {self.fecha.strftime('%Y-%m-%d')}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: MOV-TIPO-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        prefijo_tipo = self.tipo[:3].upper()
        patron_base = f"MOV-{prefijo_tipo}-{fecha_str}-"

        ultimo = MovimientoInventario.objects.filter(numero__startswith=patron_base).order_by('-numero').first()

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

        if self.tipo == 'transferencia':
            if not self.bodega_origen or not self.bodega_destino:
                raise ValidationError("Las transferencias requieren bodega origen y destino")
            if self.bodega_origen == self.bodega_destino:
                raise ValidationError("La bodega origen y destino no pueden ser la misma")
        elif self.tipo == 'entrada':
            if not self.bodega_destino:
                raise ValidationError("Las entradas requieren bodega destino")
        elif self.tipo == 'salida':
            if not self.bodega_origen:
                raise ValidationError("Las salidas requieren bodega origen")

    def save(self, *args, **kwargs):
        """Genera número automático"""
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)


class DetalleMovimiento(BaseModel):
    """Detalle de cada producto en un movimiento de inventario"""

    # ==================== CAMPOS ====================
    movimiento = models.ForeignKey(MovimientoInventario, on_delete=models.CASCADE, related_name='detalles', verbose_name="Movimiento")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_movimientos', verbose_name="Producto")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Unitario")
    costo_promedio_resultante = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo Promedio Resultante")
    lote = models.CharField(max_length=50, blank=True, verbose_name="Número de Lote")
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    stock_anterior = models.IntegerField(null=True, blank=True, verbose_name="Stock Anterior")
    stock_posterior = models.IntegerField(null=True, blank=True, verbose_name="Stock Posterior")
    lote_obj = models.ForeignKey('Lote', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos', verbose_name="Lote Asociado")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Movimiento"
        verbose_name_plural = "Detalles de Movimiento"
        ordering = ['movimiento', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.codigo} - Cant: {self.cantidad}"


class TransferenciaBodega(BaseModel):
    """Transferencias entre bodegas"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En Tránsito'),
        ('recibida', 'Recibida'),
        ('anulada', 'Anulada')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Transferencia", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    fecha_envio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Envío")
    fecha_recepcion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Recepción")
    bodega_origen = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='transferencias_origen', verbose_name="Bodega Origen")
    bodega_destino = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='transferencias_destino', verbose_name="Bodega Destino")
    solicitante = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_solicitadas', verbose_name="Solicitante")
    despachado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_despachadas', verbose_name="Despachado por")
    recibido_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_recibidas', verbose_name="Recibido por")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    motivo = models.TextField(verbose_name="Motivo de la Transferencia")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    movimiento = models.OneToOneField(MovimientoInventario, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencia', verbose_name="Movimiento de Inventario")

    # ==================== META ====================
    class Meta:
        verbose_name = "Transferencia entre Bodegas"
        verbose_name_plural = "Transferencias entre Bodegas"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Transferencia {self.numero}: {self.bodega_origen.codigo} → {self.bodega_destino.codigo}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: TRF-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"TRF-{fecha_str}-"

        ultima = TransferenciaBodega.objects.filter(numero__startswith=patron_base).order_by('-numero').first()

        if ultima:
            try:
                correlativo = int(ultima.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.bodega_origen == self.bodega_destino:
            raise ValidationError("La bodega origen y destino no pueden ser la misma")

    def save(self, *args, **kwargs):
        """Genera número automático"""
        if not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)


class DetalleTransferencia(BaseModel):
    """Detalle de productos en una transferencia"""

    # ==================== CAMPOS ====================
    transferencia = models.ForeignKey(TransferenciaBodega, on_delete=models.CASCADE, related_name='detalles', verbose_name="Transferencia")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_transferencias', verbose_name="Producto")
    cantidad_solicitada = models.IntegerField(verbose_name="Cantidad Solicitada")
    cantidad_enviada = models.IntegerField(default=0, verbose_name="Cantidad Enviada")
    cantidad_recibida = models.IntegerField(default=0, verbose_name="Cantidad Recibida")
    lote = models.CharField(max_length=50, blank=True, verbose_name="Número de Lote")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    costo_unitario_transferencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Costo Unitario")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Transferencia"
        verbose_name_plural = "Detalles de Transferencia"
        ordering = ['transferencia', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} - Solicitado: {self.cantidad_solicitada}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.cantidad_solicitada <= 0:
            raise ValidationError("La cantidad solicitada debe ser mayor a 0")

        if self.cantidad_enviada > self.cantidad_solicitada:
            raise ValidationError("La cantidad enviada no puede ser mayor a la solicitada")

        if self.cantidad_recibida > self.cantidad_enviada:
            raise ValidationError("La cantidad recibida no puede ser mayor a la enviada")


class AjusteInventario(BaseModel):
    """Ajustes de inventario por conteos físicos o correcciones"""

    # ==================== CHOICES ====================
    TIPO_CHOICES = [
        ('ajuste_positivo', 'Ajuste Positivo'),
        ('ajuste_negativo', 'Ajuste Negativo'),
        ('conteo_fisico', 'Conteo Físico'),
        ('correccion', 'Corrección')
    ]
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('aplicado', 'Aplicado')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Ajuste", editable=False)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Ajuste")
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='ajustes', verbose_name="Bodega")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='ajustes_inventario', verbose_name="Responsable")
    aprobado_por = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='ajustes_aprobados', verbose_name="Aprobado por")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador', verbose_name="Estado")
    motivo = models.TextField(verbose_name="Motivo del Ajuste")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    movimiento = models.OneToOneField(MovimientoInventario, on_delete=models.SET_NULL, null=True, blank=True, related_name='ajuste', verbose_name="Movimiento de Inventario")

    # ==================== META ====================
    class Meta:
        verbose_name = "Ajuste de Inventario"
        verbose_name_plural = "Ajustes de Inventario"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
        ]
        permissions = [
            ("aprobar_ajuste", "Puede aprobar ajustes de inventario"),
            ("realizar_conteo_fisico", "Puede realizar conteo físico"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Ajuste {self.numero} - {self.bodega.codigo}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: AJU-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"AJU-{fecha_str}-"

        ultimo = AjusteInventario.objects.filter(numero__startswith=patron_base).order_by('-numero').first()

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


class DetalleAjuste(BaseModel):
    """Detalle de productos en un ajuste de inventario"""

    # ==================== CAMPOS ====================
    ajuste = models.ForeignKey(AjusteInventario, on_delete=models.CASCADE, related_name='detalles', verbose_name="Ajuste")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_ajustes', verbose_name="Producto")
    cantidad_sistema = models.IntegerField(verbose_name="Cantidad en Sistema")
    cantidad_fisica = models.IntegerField(verbose_name="Cantidad Física")
    diferencia = models.IntegerField(editable=False, verbose_name="Diferencia")
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Unitario")
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Costo Total")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Ajuste"
        verbose_name_plural = "Detalles de Ajuste"
        ordering = ['ajuste', 'producto']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} - Dif: {self.diferencia}"

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Calcula diferencia y costo total automáticamente"""
        self.diferencia = self.cantidad_fisica - self.cantidad_sistema
        self.costo_total = abs(self.diferencia) * self.costo_unitario
        super().save(*args, **kwargs)


class ConteoFisico(BaseModel):
    """Conteos físicos de inventario"""

    # ==================== CHOICES ====================
    ESTADO_CHOICES = [
        ('planificado', 'Planificado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado')
    ]
    TIPO_CHOICES = [
        ('total', 'Conteo Total'),
        ('ciclico', 'Conteo Cíclico')
    ]

    # ==================== CAMPOS ====================
    numero = models.CharField(max_length=20, verbose_name="Número de Conteo", editable=False)
    fecha_programada = models.DateField(verbose_name="Fecha Programada")
    fecha_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Finalización")
    bodega = models.ForeignKey(Bodega, on_delete=models.PROTECT, related_name='conteos', verbose_name="Bodega")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='conteos_responsable', verbose_name="Responsable")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='planificado', verbose_name="Estado")
    tipo_conteo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='total', verbose_name="Tipo de Conteo")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Conteo Físico"
        verbose_name_plural = "Conteos Físicos"
        ordering = ['-fecha_programada']
        indexes = [
            models.Index(fields=['empresa', 'numero']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"Conteo {self.numero} - {self.bodega.codigo}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_numero(self):
        """Genera número único: CNT-YYYYMMDD-####"""
        fecha_str = timezone.now().strftime('%Y%m%d')
        patron_base = f"CNT-{fecha_str}-"

        ultimo = ConteoFisico.objects.filter(numero__startswith=patron_base).order_by('-numero').first()

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


class DetalleConteo(BaseModel):
    """Detalle de productos contados en un conteo físico"""

    # ==================== CAMPOS ====================
    conteo = models.ForeignKey(ConteoFisico, on_delete=models.CASCADE, related_name='detalles', verbose_name="Conteo")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_conteos', verbose_name="Producto")
    cantidad_sistema = models.IntegerField(verbose_name="Cantidad en Sistema")
    cantidad_contada = models.IntegerField(null=True, blank=True, verbose_name="Cantidad Contada")
    contador = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_contados', verbose_name="Contador")
    fecha_conteo = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Conteo")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Conteo"
        verbose_name_plural = "Detalles de Conteo"
        ordering = ['conteo', 'producto']
        constraints = [
            models.UniqueConstraint(fields=['conteo', 'producto', 'empresa'], name='unique_conteo_producto_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} - Sistema: {self.cantidad_sistema}"

    # ==================== PROPERTIES ====================
    @property
    def diferencia(self):
        """Calcula diferencia entre cantidad contada y sistema"""
        if self.cantidad_contada is not None:
            return self.cantidad_contada - self.cantidad_sistema
        return None


class HistoricoPrecio(BaseModel):
    """Histórico de cambios de precios de productos"""

    # ==================== CAMPOS ====================
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='historico_precios', verbose_name="Producto")
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, null=True, blank=True, related_name='historico_precios', verbose_name="Bodega")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta")
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Anterior")
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Cambio")
    responsable = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='cambios_precio', verbose_name="Responsable")
    motivo = models.TextField(blank=True, verbose_name="Motivo del Cambio")

    # ==================== META ====================
    class Meta:
        verbose_name = "Histórico de Precios"
        verbose_name_plural = "Históricos de Precios"
        ordering = ['-fecha_cambio']
        indexes = [
            models.Index(fields=['producto', 'fecha_cambio']),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        bodega_str = f" - {self.bodega.codigo}" if self.bodega else " - Global"
        return f"{self.producto.nombre}{bodega_str}: ${self.precio_venta} ({self.fecha_cambio.strftime('%Y-%m-%d')})"


class KitComponente(BaseModel):
    """Componentes que conforman un kit"""

    # ==================== CAMPOS ====================
    kit = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='componentes', limit_choices_to={'es_kit': True}, verbose_name="Kit")
    componente = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='parte_de_kits', verbose_name="Componente")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    es_opcional = models.BooleanField(default=False, verbose_name="Componente Opcional")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    # ==================== META ====================
    class Meta:
        verbose_name = "Componente de Kit"
        verbose_name_plural = "Componentes de Kit"
        ordering = ['kit', 'componente']
        constraints = [
            models.UniqueConstraint(fields=['kit', 'componente', 'empresa'], name='unique_kit_componente_empresa')
        ]
        permissions = [
            ("ver_composicion_kit", "Puede ver composición de kits"),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.kit.nombre} → {self.componente.nombre} (x{self.cantidad})"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.kit == self.componente:
            raise ValidationError("Un kit no puede contenerse a sí mismo")

        if self.componente.es_kit:
            raise ValidationError("Un componente no puede ser otro kit (no se permiten kits anidados)")

        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")


class UnidadConversion(BaseModel):
    """Conversiones entre unidades de medida para un producto"""

    # ==================== CAMPOS ====================
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='conversiones', verbose_name="Producto")
    unidad_origen = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT, related_name='conversiones_origen', verbose_name="Unidad Origen")
    unidad_destino = models.ForeignKey(UnidadMedida, on_delete=models.PROTECT, related_name='conversiones_destino', verbose_name="Unidad Destino")
    factor_conversion = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Factor de Conversión")

    # ==================== META ====================
    class Meta:
        verbose_name = "Conversión de Unidad"
        verbose_name_plural = "Conversiones de Unidad"
        ordering = ['producto', 'unidad_origen']
        constraints = [
            models.UniqueConstraint(fields=['producto', 'unidad_origen', 'unidad_destino', 'empresa'], name='unique_conversion_empresa')
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre}: 1 {self.unidad_origen.abreviatura} = {self.factor_conversion} {self.unidad_destino.abreviatura}"

    # ==================== OVERRIDES ====================
    def clean(self):
        """Validaciones del modelo"""
        super().clean()

        if self.unidad_origen == self.unidad_destino:
            raise ValidationError("La unidad origen y destino no pueden ser iguales")

        if self.factor_conversion <= 0:
            raise ValidationError("El factor de conversión debe ser mayor a 0")


class Lote(BaseModel):
    """Lotes individuales de productos para trazabilidad FIFO"""

    # ==================== CAMPOS ====================
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes', verbose_name="Producto")
    bodega = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='lotes', verbose_name="Bodega")
    numero_lote = models.CharField(max_length=50, verbose_name="Número de Lote")
    cantidad_inicial = models.IntegerField(verbose_name="Cantidad Inicial")
    cantidad = models.IntegerField(verbose_name="Cantidad Actual")
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Unitario")
    fecha_ingreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ingreso")
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    proveedor = models.ForeignKey('personas.Proveedor', on_delete=models.PROTECT, null=True, blank=True, related_name='lotes_suministrados', verbose_name="Proveedor")
    movimiento_origen = models.ForeignKey(MovimientoInventario, on_delete=models.PROTECT, related_name='lotes_generados', verbose_name="Movimiento de Origen")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # ==================== META ====================
    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ['fecha_ingreso', 'numero_lote']
        indexes = [
            models.Index(fields=['producto', 'bodega', 'fecha_ingreso']),
            models.Index(fields=['numero_lote']),
            models.Index(fields=['fecha_vencimiento']),
        ]
        permissions = [
            ('ver_lotes_todas_bodegas', 'Puede ver lotes de todas las bodegas'),
            ('gestionar_lotes', 'Puede crear y modificar lotes'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.numero_lote} - {self.producto.nombre} ({self.cantidad}/{self.cantidad_inicial})"

    # ==================== PROPERTIES ====================
    @property
    def cantidad_usada(self):
        """Cantidad que ya se ha vendido/usado de este lote"""
        return self.cantidad_inicial - self.cantidad

    @property
    def esta_vencido(self):
        """Verifica si el lote está vencido"""
        if not self.fecha_vencimiento:
            return False
        return timezone.now().date() > self.fecha_vencimiento

    @property
    def dias_hasta_vencimiento(self):
        """Días restantes hasta el vencimiento"""
        if not self.fecha_vencimiento:
            return None
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Marca como inactivo si se agota"""
        if self.cantidad == 0:
            self.activo = False
        super().save(*args, **kwargs)


class DetalleLoteSalida(BaseModel):
    """Registra qué lotes específicos se usaron en cada salida de inventario"""

    # ==================== CAMPOS ====================
    detalle_movimiento = models.ForeignKey(DetalleMovimiento, on_delete=models.CASCADE, related_name='lotes_usados', verbose_name="Detalle de Movimiento")
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='salidas', verbose_name="Lote")
    cantidad = models.IntegerField(verbose_name="Cantidad Tomada")
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Unitario")

    # ==================== META ====================
    class Meta:
        verbose_name = "Detalle de Lote en Salida"
        verbose_name_plural = "Detalles de Lotes en Salidas"
        ordering = ['detalle_movimiento', 'lote']

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.lote.numero_lote}: {self.cantidad} unidades"

    # ==================== PROPERTIES ====================
    @property
    def valor_total(self):
        """Valor total de esta porción del lote"""
        return self.cantidad * self.costo_unitario


class ListaPrecio(BaseModel):
    """Listas de precios diferenciadas para productos"""

    # ==================== CAMPOS ====================
    codigo = models.CharField(max_length=20, verbose_name="Código", editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    porcentaje_incremento = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Porcentaje sobre Precio Base")
    es_predeterminada = models.BooleanField(default=False, verbose_name="Es Predeterminada")
    es_activa = models.BooleanField(default=True, verbose_name="Activa")

    # ==================== META ====================
    class Meta:
        verbose_name = "Lista de Precio"
        verbose_name_plural = "Listas de Precios"
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'empresa'], name='unique_codigo_lista_precio_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # ==================== MÉTODOS PRIVADOS ====================
    def _generar_codigo(self):
        """Genera código único: LP-{CORRELATIVO}"""
        patron_base = "LP-"
        ultimo = ListaPrecio.objects.filter(empresa=self.empresa, codigo__startswith=patron_base).order_by('-codigo').first()

        if ultimo:
            try:
                correlativo = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                correlativo = 1
        else:
            correlativo = 1

        return f"{patron_base}{correlativo:04d}"

    def _desmarcar_predeterminadas(self):
        """Desmarca otras listas como predeterminadas"""
        ListaPrecio.objects.filter(
            empresa=self.empresa,
            es_predeterminada=True
        ).exclude(id=self.id).update(es_predeterminada=False)

    # ==================== OVERRIDES ====================
    def save(self, *args, **kwargs):
        """Genera código automático y gestiona lista predeterminada"""
        if not self.codigo:
            self.codigo = self._generar_codigo()

        if self.es_predeterminada:
            self._desmarcar_predeterminadas()

        super().save(*args, **kwargs)


class PrecioProducto(BaseModel):
    """Precios por producto según lista de precios"""

    # ==================== CAMPOS ====================
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='precios', verbose_name="Lista de Precio")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios_listas', verbose_name="Producto")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")

    # ==================== META ====================
    class Meta:
        verbose_name = "Precio de Producto"
        verbose_name_plural = "Precios de Productos"
        ordering = ['lista_precio', 'producto']
        constraints = [
            models.UniqueConstraint(fields=['lista_precio', 'producto', 'empresa'], name='unique_lista_producto_empresa'),
        ]

    # ==================== __str__ ====================
    def __str__(self):
        return f"{self.producto.nombre} - {self.lista_precio.nombre}: ${self.precio}"