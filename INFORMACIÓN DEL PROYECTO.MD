# DECISIONES TÉCNICAS Y ARQUITECTURA - SISTEMA ERP MULTITENANT

## INFORMACIÓN DEL PROYECTO

### Objetivo General
Sistema ERP multitenant SaaS para empresas ecuatorianas (pequeñas a medianas) con modelo de suscripción mensual. El sistema debe ser flexible y escalable según las necesidades del cliente.

### Modelo de Negocio
- **Suscripción mensual** con planes escalonados
- **Limitaciones por plan**: cantidad de usuarios, módulos habilitados, transacciones mensuales
- **Target**: Desde negocios unipersonales hasta empresas medianas con departamentos definidos

---

## 1. STACK TECNOLÓGICO (CONFIRMADO)

### Backend
- **Python**: 3.12
- **Django**: 4.2.23 (LTS)
- **Django REST Framework**: 3.16.1
- **PostgreSQL**: Base de datos principal

### Autenticación
- **djangorestframework-simplejwt**: 5.5.1
- **Configuración JWT** (desarrollo):
  ```python
  SIMPLE_JWT = {
      'ACCESS_TOKEN_LIFETIME': timedelta(minutes=3600),
      'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
      'ROTATE_REFRESH_TOKENS': True,
  }
  ```
- **2FA**: No implementado (fase futura)

### Librerías Adicionales
- **django-cities-light**: Para ubicaciones (ciudades usando SubRegion)
- **Auditoría**: Usar **django-auditlog** (opción más óptima vs sistema custom)

---

## 2. ARQUITECTURA MULTITENANT

### Estrategia Implementada
- **Row-level multitenancy**: Campo `empresa` en cada tabla
- **Middleware personalizado**: Ya implementado para detección de tenant
- **Subdominios**: `empresa1.tuapp.com`, `empresa2.tuapp.com`
- **Aislamiento**: Cada empresa ve solo sus propios datos

### Ventajas
- Escalabilidad para SaaS
- Costos optimizados (una sola BD)
- Mantenimiento simplificado

---

## 3. SISTEMA DE PERMISOS Y ROLES

### Decisión: Permisos Granulares por Acción

#### Estructura de Roles

```python
ROLES_SISTEMA = {
    'SUPER_ADMIN': {
        'descripcion': 'Administrador total del sistema (soporte técnico)',
        'alcance': 'global',
        'permisos': '*'  # Acceso a todas las empresas y funciones
    },
    'ADMIN_EMPRESA': {
        'descripcion': 'Administrador de la empresa',
        'alcance': 'empresa',
        'permisos': '*'  # Todos los permisos dentro de su empresa
    },
    'GERENTE_DEPARTAMENTO': {
        'descripcion': 'Líder de departamento',
        'alcance': 'departamento',
        'permisos': 'todos_del_departamento'  # Acceso total a su departamento
    },
    'COLABORADOR': {
        'descripcion': 'Colaborador de departamento',
        'alcance': 'departamento',
        'permisos': 'asignados_individualmente'  # Permisos específicos
    }
}
```

#### Departamentos y Permisos Base

```python
DEPARTAMENTOS = {
    'INVENTARIO': [
        'crear_productos',
        'editar_productos',
        'eliminar_productos',
        'ajustar_stock',
        'ver_costos',
        'crear_bodegas',
        'transferir_stock',
        'ver_reportes_inventario'
    ],
    'VENTAS': [
        'crear_ventas',
        'editar_ventas',
        'anular_ventas',
        'aprobar_creditos',
        'crear_clientes',
        'ver_reportes_ventas',
        'aplicar_descuentos'
    ],
    'COMPRAS': [
        'crear_ordenes_compra',
        'aprobar_ordenes_compra',
        'recibir_productos',
        'crear_proveedores',
        'ver_reportes_compras'
    ],
    'FINANZAS': [
        'crear_asientos_contables',
        'aprobar_pagos',
        'ver_estados_financieros',
        'configurar_impuestos',
        'generar_reportes_tributarios'
    ],
    'RRHH': [
        'crear_empleados',
        'editar_empleados',
        'procesar_nomina',
        'aprobar_vacaciones',
        'ver_reportes_rrhh'
    ]
}
```

### Validación de Permisos en ViewSets

```python
class ProductoViewSet(TenantViewSet):
    def check_permiso(self, permiso):
        """Verifica si el usuario tiene el permiso especificado"""
        if not self.request.user.tiene_permiso(permiso):
            self.logger.warning(
                f"Usuario {self.request.user.id} intentó '{permiso}' sin autorización"
            )
            raise PermissionDenied(f"No tiene permisos para {permiso}")
    
    def create(self, request, *args, **kwargs):
        self.check_permiso('crear_productos')
        # ... resto de la lógica
```

---

## 4. AUDITORÍA Y TRAZABILIDAD

### Herramienta: django-auditlog
**Justificación**: Solución robusta, mantenida, con menor overhead que un sistema custom.

### Campos de Auditoría en BaseModel

```python
class BaseModel(models.Model):
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usuarios responsables
    created_by = models.ForeignKey(
        User, 
        related_name='+', 
        on_delete=models.SET_NULL, 
        null=True
    )
    updated_by = models.ForeignKey(
        User, 
        related_name='+', 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        related_name='+', 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    # Auditoría adicional
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        abstract = True
```

### Eventos a Auditar
- **CRUD**: CREATE, UPDATE, DELETE
- **Autenticación**: LOGIN, LOGOUT, FAILED_LOGIN
- **Documentos**: PRINT, EXPORT
- **Aprobaciones**: APPROVED, REJECTED
- **Operaciones financieras**: PAYMENT, CHARGE

---

## 5. IMPUESTOS Y NORMATIVA ECUADOR

### Configuración de Impuestos

```python
# settings/base.py
TASA_IVA = Decimal('0.15')  # 15% (configurable)
MANEJA_IVA_0 = True
MANEJA_ICE = True  # Impuesto a Consumos Especiales
MANEJA_RETENCIONES = True  # Retenciones en la fuente
```

### ICE (Impuesto a Consumos Especiales)
**Productos afectados**: Alcohol, tabaco, bebidas azucaradas, vehículos de lujo  
**Implementación**: Tabla de productos con ICE + porcentajes variables

### Retenciones en la Fuente
**Escenario**: Transacciones B2B  
**Porcentajes comunes**: 1%, 2%, 10% (según tipo de bien/servicio)  
**Implementación**: Tabla de tipos de retención + cálculo automático en compras

---

## 6. INVENTARIO - REGLAS DE NEGOCIO

### Método de Valoración de Inventario
**Decisión**: **Promedio Ponderado** (estándar NIIF en Ecuador)

```python
def calcular_costo_promedio(producto, cantidad_ingreso, costo_unitario_ingreso):
    """
    Fórmula: (Stock_Anterior * Costo_Anterior + Ingreso * Costo_Ingreso) 
             / (Stock_Anterior + Ingreso)
    """
    stock_actual = producto.stock_disponible
    costo_actual = producto.costo_promedio
    
    nuevo_costo = (
        (stock_actual * costo_actual) + (cantidad_ingreso * costo_unitario_ingreso)
    ) / (stock_actual + cantidad_ingreso)
    
    return nuevo_costo
```

### Stock Negativo
- **Por defecto**: NO PERMITIR
- **Backorders con aprobación**: Permitir ventas sin stock con autorización de gerente

### Control de Lotes
**Decisión**: **Fase 2**  
**Uso futuro**: Productos perecederos (alimentos, medicinas)

### Control de Series/Seriales
**Decisión**: **Implementar en Fase 1**  
**Productos afectados**: Electrónicos, vehículos, equipos con garantía

```python
class Serie(BaseModel):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100, unique=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('DISPONIBLE', 'Disponible'),
            ('VENDIDO', 'Vendido'),
            ('DEFECTUOSO', 'Defectuoso'),
            ('EN_GARANTIA', 'En garantía')
        ]
    )
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE)
    fecha_ingreso = models.DateField()
    venta = models.ForeignKey('Venta', null=True, blank=True, on_delete=models.SET_NULL)
```

### Listas de Precios
**Decisión**: **Fase 2**  
**Uso futuro**: Precios diferenciados (público, mayorista, distribuidor)

---

## 7. ESTANDARIZACIÓN DE RESPUESTAS API

### Problema Identificado
Actualmente las respuestas de error usan campos inconsistentes:
- `mensaje_error`
- `error_mensaje`
- `mensaje`
- `error`

**Solución**: Un solo formato estándar para todas las APIs.

### Estructura Estándar de Respuestas

```python
# apis/base/response_handler.py
from rest_framework.response import Response
from rest_framework import status

class StandardResponse:
    """
    Manejador centralizado de respuestas API
    """
    
    @staticmethod
    def success(data=None, mensaje=None, status_code=status.HTTP_200_OK):
        """
        Respuesta exitosa
        
        Uso:
            return StandardResponse.success(
                data={'producto': {...}},
                mensaje="Producto creado exitosamente"
            )
        """
        return Response({
            'success': True,
            'data': data,
            'mensaje': mensaje,
            'error': None,
            'info': None
        }, status=status_code)
    
    @staticmethod
    def error(mensaje, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Respuesta de error (para el usuario)
        
        Uso:
            return StandardResponse.error(
                mensaje="No tiene permisos para crear productos",
                status_code=status.HTTP_403_FORBIDDEN
            )
        """
        return Response({
            'success': False,
            'data': None,
            'mensaje': None,
            'error': mensaje,  # ÚNICO campo para errores
            'info': None
        }, status=status_code)
    
    @staticmethod
    def info(mensaje, data=None):
        """
        Respuesta informativa (avisos, warnings)
        
        Uso:
            return StandardResponse.info(
                mensaje="El producto ya existe, se actualizó el stock",
                data={'producto': {...}}
            )
        """
        return Response({
            'success': True,
            'data': data,
            'mensaje': None,
            'error': None,
            'info': mensaje  # Para avisos no críticos
        }, status=status.HTTP_200_OK)
```

### Manejo de Errores con Logging Dual

```python
class ProductoViewSet(TenantViewSet):
    logger = logging.getLogger(__name__)
    
    def create(self, request, *args, **kwargs):
        try:
            # Validar permisos
            self.check_permiso('crear_productos')
            
            # Lógica de negocio
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            producto = serializer.save()
            
            # Log para desarrollador (consola)
            self.logger.info(
                f"Producto creado: {producto.codigo} | "
                f"Usuario: {request.user.id} | "
                f"Empresa: {request.tenant.id}"
            )
            
            # Respuesta para usuario (frontend)
            return StandardResponse.success(
                data=serializer.data,
                mensaje="Producto creado exitosamente"
            )
            
        except PermissionDenied as e:
            # Log detallado para desarrollador
            self.logger.warning(
                f"Permiso denegado | Usuario: {request.user.id} | "
                f"Acción: crear_productos | IP: {request.META.get('REMOTE_ADDR')}"
            )
            # Mensaje simple para usuario
            return StandardResponse.error(
                mensaje="No tiene permisos para crear productos",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        except ValidationError as e:
            # Log detallado con traceback
            self.logger.error(
                f"Error de validación al crear producto | "
                f"Data: {request.data} | Error: {str(e)}",
                exc_info=True
            )
            # Mensaje amigable para usuario
            return StandardResponse.error(
                mensaje="Datos inválidos. Revise la información ingresada",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            
        except Exception as e:
            # Log crítico con stack trace completo
            self.logger.critical(
                f"Error inesperado al crear producto | "
                f"Usuario: {request.user.id} | "
                f"Data: {request.data}",
                exc_info=True
            )
            # Mensaje genérico para usuario
            return StandardResponse.error(
                mensaje="Error interno del sistema. Contacte al administrador",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### Campos Únicos por Tipo de Respuesta

| Tipo | Campo Frontend | Descripción |
|------|---------------|-------------|
| **Éxito** | `mensaje` | Confirmación de acción exitosa |
| **Error** | `error` | Mensaje de error para el usuario |
| **Información** | `info` | Avisos no críticos |
| **Datos** | `data` | Payload de la respuesta |

**Beneficio**: El frontend solo necesita verificar `response.error`, `response.info`, o `response.mensaje` sin adivinar el nombre del campo.

---

## 8. ESTRUCTURA ESTÁNDAR DE VIEWSETS

### Template de ViewSet

```python
# ==================== IMPORTS ====================
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from apis.core.tenant_viewset import TenantViewSet
from apis.core.response_handler import StandardResponse

# ==================== CONFIGURACIÓN ====================
class ProductoViewSet(TenantViewSet):
    """
    ViewSet para gestión de productos
    
    Endpoints:
        - GET /api/productos/ - Listar productos
        - POST /api/productos/ - Crear producto
        - GET /api/productos/{id}/ - Detalle producto
        - PUT /api/productos/{id}/ - Actualizar producto
        - DELETE /api/productos/{id}/ - Eliminar producto
        - POST /api/productos/{id}/ajustar_stock/ - Ajustar stock
    """
    
    logger = logging.getLogger(__name__)
    serializer_class = ProductoSerializer
    
    # ==================== QUERYSET OPTIMIZADO ====================
    def get_queryset(self):
        """
        Queryset optimizado con select_related y prefetch_related
        para reducir queries N+1
        """
        return Producto.objects.select_related(
            'categoria',
            'marca',
            'unidad_medida',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'stock_set__bodega',
            'series_set'
        ).filter(
            empresa=self.request.tenant,
            deleted_at__isnull=True  # Excluir eliminados (soft delete)
        )
    
    # ==================== PERMISOS ====================
    def check_permiso(self, permiso):
        """Verifica si el usuario tiene el permiso especificado"""
        if not self.request.user.tiene_permiso(permiso):
            self.logger.warning(
                f"Permiso denegado: {permiso} | Usuario: {self.request.user.id}"
            )
            raise PermissionDenied(f"No tiene permisos para {permiso}")
    
    # ==================== CRUD OPERATIONS ====================
    
    def list(self, request, *args, **kwargs):
        """Listar productos con filtros"""
        self.check_permiso('ver_productos')
        # ... lógica de listado
    
    def create(self, request, *args, **kwargs):
        """Crear nuevo producto"""
        self.check_permiso('crear_productos')
        # ... lógica de creación
    
    def update(self, request, *args, **kwargs):
        """Actualizar producto existente"""
        self.check_permiso('editar_productos')
        # ... lógica de actualización
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar producto (soft delete)"""
        self.check_permiso('eliminar_productos')
        # ... lógica de eliminación
    
    # ==================== CUSTOM ACTIONS ====================
    
    @action(detail=True, methods=['post'])
    def ajustar_stock(self, request, pk=None):
        """
        Ajustar stock de producto manualmente
        
        Body:
            {
                "bodega_id": 1,
                "cantidad": 10,
                "tipo": "entrada|salida",
                "observaciones": "Ajuste por inventario físico"
            }
        """
        self.check_permiso('ajustar_stock')
        # ... lógica de ajuste
    
    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        """
        Listar productos con stock por debajo del mínimo
        """
        self.check_permiso('ver_reportes_inventario')
        # ... lógica de consulta
    
    # ==================== FUNCIONES AUXILIARES ====================
    
    def _validar_stock_disponible(self, producto, bodega, cantidad):
        """Valida si hay stock suficiente en la bodega"""
        stock = Stock.objects.filter(
            producto=producto,
            bodega=bodega
        ).first()
        
        if not stock or stock.cantidad_disponible < cantidad:
            return False
        return True
    
    def _generar_movimiento_inventario(self, producto, bodega, cantidad, tipo, observaciones):
        """Genera un registro de movimiento de inventario"""
        # ... lógica de creación de movimiento
```

### Secciones Obligatorias en Cada ViewSet

1. **IMPORTS**: Librerías necesarias
2. **CONFIGURACIÓN**: Docstring, logger, serializer_class
3. **QUERYSET OPTIMIZADO**: `get_queryset()` con joins
4. **PERMISOS**: `check_permiso()` centralizado
5. **CRUD OPERATIONS**: list, create, retrieve, update, destroy
6. **CUSTOM ACTIONS**: Endpoints adicionales con `@action`
7. **FUNCIONES AUXILIARES**: Métodos privados de soporte

---

## 9. LÓGICA DE NEGOCIO EN MODELOS

### Principio: Fat Models, Thin Views
**Toda la lógica de negocio debe estar en los modelos**, no en ViewSets.

### Ejemplo: Generación de Códigos

```python
class Producto(BaseModel):
    # ... campos
    
    def save(self, *args, **kwargs):
        """Override save para generar código automáticamente"""
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)
    
    def _generar_codigo(self):
        """
        Genera código único en formato: PRODUCTO-CATEGORIA-0001
        
        Ejemplos:
            - Capuchones + Transmisión → CPCH-TRA-0001
            - Pines sin categoría → PINS-GEN-0001
        """
        prefijo_producto = self._generar_prefijo_producto()
        prefijo_categoria = self._generar_prefijo_categoria()
        correlativo = self._generar_correlativo(prefijo_producto, prefijo_categoria)
        
        return f"{prefijo_producto}-{prefijo_categoria}-{correlativo}"
    
    def _generar_prefijo_producto(self):
        """Extrae consonantes principales del nombre"""
        # ... lógica de extracción
    
    def _generar_prefijo_categoria(self):
        """Genera prefijo de 3 letras de la categoría"""
        # ... lógica
    
    def _generar_correlativo(self, prefijo_producto, prefijo_categoria):
        """Genera número secuencial único"""
        # ... lógica
```

### Validaciones en Modelos

```python
class Producto(BaseModel):
    def clean(self):
        """Validaciones personalizadas"""
        # Validar precio mayor a costo
        if self.precio_venta <= self.costo_compra:
            raise ValidationError({
                'precio_venta': 'El precio de venta debe ser mayor al costo de compra'
            })
        
        # Validar stock mínimo positivo
        if self.stock_minimo < 0:
            raise ValidationError({
                'stock_minimo': 'El stock mínimo no puede ser negativo'
            })
    
    def calcular_margen(self):
        """Calcula el margen de ganancia"""
        if self.costo_compra == 0:
            return Decimal('0.00')
        
        margen = ((self.precio_venta - self.costo_compra) / self.costo_compra) * 100
        return round(margen, 2)
    
    def tiene_stock_disponible(self, bodega=None):
        """Verifica si hay stock disponible"""
        if bodega:
            stock = self.stock_set.filter(bodega=bodega).first()
            return stock and stock.cantidad_disponible > 0
        else:
            return self.stock_set.filter(cantidad_disponible__gt=0).exists()
```

---

## 10. PRIORIDAD DE MÓDULOS - ORDEN DE DESARROLLO

### Fase 1 (Actual - MVP)

1. **Inventario** (ya avanzado)
   - Productos, Categorías, Marcas
   - Bodegas, Ubicaciones
   - Stock, Movimientos
   - **NUEVO**: Series/Seriales

2. **Ventas**
   - Clientes
   - Cotizaciones
   - Ventas (con manejo de crédito)
   - Notas de crédito/débito

3. **Compras**
   - Proveedores
   - Solicitudes de compra
   - Órdenes de compra
   - Recepción de productos

4. **Finanzas/Contabilidad**
   - Plan de cuentas (Ecuador)
   - Asientos contables manuales
   - Asientos automáticos (desde ventas/compras)
   - Cuentas por cobrar/pagar
   - Reportes tributarios básicos

5. **RRHH**
   - Empleados
   - Departamentos
   - Nómina básica (Ecuador - IESS)
   - Vacaciones y permisos

### Fase 2 (Funcionalidades Avanzadas)

- **Facturación Electrónica SRI**
- **Control de Lotes** (productos perecederos)
- **Listas de Precios** (múltiples)
- **Promociones y Descuentos**
- **Workflows de Aprobación Multinivel**
- **Caché con Redis**
- **Reportes avanzados**

---

## 11. CONFIGURACIONES ESPECÍFICAS ECUADOR

### Impuestos

```python
# apis/base/impuestos.py
IMPUESTOS_ECUADOR = {
    'IVA_15': {
        'codigo': '2',
        'tasa': Decimal('0.15'),
        'descripcion': 'IVA 15%'
    },
    'IVA_0': {
        'codigo': '0',
        'tasa': Decimal('0.00'),
        'descripcion': 'IVA 0%'
    },
    'NO_OBJETO_IVA': {
        'codigo': '6',
        'tasa': Decimal('0.00'),
        'descripcion': 'No objeto de IVA'
    },
    'EXENTO_IVA': {
        'codigo': '7',
        'tasa': Decimal('0.00'),
        'descripcion': 'Exento de IVA'
    }
}

TIPOS_RETENCION = {
    'RENTA_1': {'codigo': '1', 'porcentaje': Decimal('1.00')},
    'RENTA_2': {'codigo': '2', 'porcentaje': Decimal('2.00')},
    'RENTA_8': {'codigo': '8', 'porcentaje': Decimal('8.00')},
    'RENTA_10': {'codigo': '10', 'porcentaje': Decimal('10.00')},
    'IVA_30': {'codigo': '30', 'porcentaje': Decimal('30.00')},
    'IVA_70': {'codigo': '70', 'porcentaje': Decimal('70.00')},
    'IVA_100': {'codigo': '100', 'porcentaje': Decimal('100.00')}
}
```

### Tipos de Identificación

```python
TIPOS_IDENTIFICACION_ECUADOR = {
    'CEDULA': {
        'codigo': '05',
        'longitud': 10,
        'validacion': 'cedula_ecuador'
    },
    'RUC': {
        'codigo': '04',
        'longitud': 13,
        'validacion': 'ruc_ecuador'
    },
    'PASAPORTE': {
        'codigo': '06',
        'longitud_max': 20,
        'validacion': None
    }
}
```

---

## 12. MODELOS ADICIONALES NECESARIOS

### Serie/Serial (Fase 1)

```python
class Serie(BaseModel):
    """
    Números de serie únicos para productos específicos
    (electrónicos, vehículos, equipos)
    """
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100, unique=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('DISPONIBLE', 'Disponible en bodega'),
            ('VENDIDO', 'Vendido'),
            ('DEFECTUOSO', 'Defectuoso/Dañado'),
            ('EN_GARANTIA', 'En proceso de garantía'),
            ('DADO_DE_BAJA', 'Dado de baja')
        ],
        default='DISPONIBLE'
    )
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE)
    fecha_ingreso = models.DateField()
    venta = models.ForeignKey(
        'Venta', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='series_vendidas'
    )
    fecha_venta = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Serie'
        verbose_name_plural = 'Series'
        indexes = [
            models.Index(fields=['numero_serie']),
            models.Index(fields=['producto', 'estado'])
        ]
```

### Configuración del Sistema (Multi-tenant)

```python
class ConfiguracionEmpresa(BaseModel):
    """
    Configuraciones específicas por empresa
    """
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE)
    clave = models.CharField(max_length=100)  # 'tasa_iva', 'dias_credito_default'
    valor = models.TextField()
    tipo_dato = models.CharField(
        max_length=20,
        choices=[
            ('STRING', 'Texto'),
            ('INTEGER', 'Número entero'),
            ('DECIMAL', 'Número decimal'),
            ('BOOLEAN', 'Verdadero/Falso'),
            ('JSON', 'Objeto JSON')
        ]
    )
    descripcion = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('empresa', 'clave')
    
    def get_valor_typed(self):
        """Retorna el valor en el tipo de dato correcto"""
        if self.tipo_dato == 'INTEGER':
            return int(self.valor)
        elif self.tipo_dato == 'DECIMAL':
            return Decimal(self.valor)
        elif self.tipo_dato == 'BOOLEAN':
            return self.valor.lower() == 'true'
        elif self.tipo_dato == 'JSON':
            import json
            return json.loads(self.valor)
        else:
            return self.valor
```

---

## 13. SISTEMA DE ENVÍO DE EMAILS

### Configuración Actual
- **Sistema de creación de usuarios**: Ya implementado con envío de emails
- **Provider**: Definir en settings (SendGrid, AWS SES, SMTP)

### Plantillas de Email Necesarias

```python
TIPOS_EMAIL = {
    'BIENVENIDA': 'Bienvenida a nuevo usuario',
    'RESET_PASSWORD': 'Recuperación de contraseña',
    'VENTA_CONFIRMADA': 'Confirmación de venta al cliente',
    'FACTURA_ELECTRONICA': 'Envío de factura electrónica',
    'STOCK_BAJO': 'Alerta de stock bajo mínimo',
    'ORDEN_COMPRA': 'Envío de orden de compra a proveedor',
    'APROBACION_PENDIENTE': 'Solicitud de aprobación',
    'NOMINA_GENERADA': 'Rol de pagos generado'
}
```

---

## 14. TESTING Y CALIDAD

### Fixtures de Datos Iniciales

```python
# fixtures/ecuador_base.json
- Plan de cuentas contable estándar Ecuador
- Tipos de identificación
- Formas de pago (efectivo, transferencia, tarjeta)
- Tipos de comprobantes SRI
- Códigos de impuestos
- Provincias y ciudades (django-cities-light)
```

### Estrategia de Testing
- **Unit tests**: Modelos y funciones de negocio
- **Integration tests**: APIs completas
- **Fixtures por módulo**: Datos de prueba por departamento

---

## 15. ESTRUCTURA DEL DOCUMENTO TÉCNICO SOLICITADO

### Formato: Documento Modular LaTeX

```
/plan-desarrollo-backend/
├── main.tex                          # Documento principal
├── 00-introduccion/
│   ├── vision-sistema.tex
│   ├── modelo-negocio-saas.tex
│   ├── alcance-fases.tex
│   └── stack-tecnologico.tex
├── 01-arquitectura/
│   ├── multitenant-rowlevel.tex
│   ├── autenticacion-jwt.tex
│   ├── sistema-permisos-granular.tex
│   └── auditoria-django-auditlog.tex
├── 02-estandares-codigo/
│   ├── estructura-viewsets.tex
│   ├── respuestas-api-estandar.tex
│   ├── manejo-errores-logging.tex
│   └── naming-conventions.tex
├── 03-modelos-base/
│   ├── base-model-auditoria.tex
│   ├── tenant-model.tex
│   ├── user-departamento-roles.tex
│   └── configuracion-empresa.tex
├── 04-modulo-inventario/
│   ├── modelos-inventario.tex
│   ├── apis-inventario.tex
│   ├── reglas-negocio.tex
│   ├── series-productos.tex
│   ├── valoracion-promedio-ponderado.tex
│   └── movimientos-stock.tex
├── 05-modulo-ventas/
│   ├── modelos-ventas.tex
│   ├── apis-ventas.tex
│   ├── reglas-negocio-credito.tex
│   ├── calculo-impuestos.tex
│   └── notas-credito-debito.tex
├── 06-modulo-compras/
│   ├── modelos-compras.tex
│   ├── apis-compras.tex
│   ├── workflow-aprobaciones.tex
│   └── recepcion-productos.tex
├── 07-modulo-finanzas/
│   ├── modelos-contabilidad.tex
│   ├── plan-cuentas-ecuador.tex
│   ├── asientos-automaticos.tex
│   ├── cuentas-cobrar-pagar.tex
│   ├── retenciones-ecuador.tex
│   └── reportes-tributarios.tex
├── 08-modulo-rrhh/
│   ├── modelos-rrhh.tex
│   ├── nomina-ecuador-iess.tex
│   ├── apis-empleados.tex
│   └── vacaciones-permisos.tex
├── 09-integraciones/
│   ├── sri-facturacion-fase2.tex
│   ├── emails-plantillas.tex
│   └── notificaciones-sistema.tex
├── 10-testing-calidad/
│   ├── estrategia-pruebas.tex
│   ├── fixtures-datos-ecuador.tex
│   └── ci-cd-pipeline.tex
├── 11-deployment/
│   ├── configuracion-produccion.tex
│   ├── migraciones-database.tex
│   └── monitoring-logging.tex
└── anexos/
    ├── permisos-completos.tex
    ├── codigos-impuestos-sri.tex
    ├── plan-cuentas-niif-ecuador.tex
    ├── tipos-identificacion.tex
    └── glosario-terminos.tex
```

---

## 16. NOTAS IMPORTANTES PARA LA GENERACIÓN DEL DOCUMENTO

### Contexto que la IA ya tiene:
- Todos los modelos actuales del sistema
- Estructura de carpetas y archivos
- Implementación de multitenant
- Sistema de subdominios
- Envío de emails

### Información adicional proporcionada en este documento:
- Decisiones técnicas confirmadas
- Sistema de permisos granular por acción
- Estructura estándar de respuestas API
- Manejo de errores dual (usuario + desarrollador)
- Reglas de negocio específicas Ecuador
- Orden de desarrollo de módulos
- Modelos adicionales necesarios (Series, ConfiguraciónEmpresa)

### Enfoque del documento:
- **Backend únicamente** (no frontend)
- **Guía de desarrollo modular** en LaTeX
- **Prioridad**: Claridad, detalle técnico, ejemplos de código
- **Target**: Desarrolladores que implementarán cada módulo

---

## RESUMEN EJECUTIVO

Este documento consolida las decisiones técnicas y arquitectónicas para el desarrollo de un **Sistema ERP Multitenant SaaS** orientado a empresas ecuatorianas. El sistema se construye sobre:

- **Tecnología**: Django 4.2, DRF 3.16, PostgreSQL, Python 3.12
- **Arquitectura**: Row-level multitenancy con subdominios
- **Permisos**: Granular por acción con roles jerárquicos (Admin → Gerente → Colaborador)
- **Auditoría**: django-auditlog con campos extendidos
- **Respuestas API**: Formato estándar único (`error`, `mensaje`, `info`, `data`)
- **Logging**: Dual (usuario amigable + desarrollador detallado)
- **Inventario**: Valoración por promedio ponderado, control de series
- **Normativa**: Impuestos Ecuador (IVA 15%, retenciones, ICE)
- **Fases**: Inventario → Ventas → Compras → Finanzas → RRHH
- **Fase 2**: SRI, lotes, listas de precios, promociones

El sistema prioriza **flexibilidad** (desde negocios unipersonales hasta empresas medianas) y **escalabilidad** (modelo SaaS con planes de suscripción).