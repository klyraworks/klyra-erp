# API — Movimientos de Inventario

**Base URL:** `/api/movimientos-inventario/`

---

## Índice

- [Modelo de datos](#modelo-de-datos)
- [Endpoints](#endpoints)
  - [Listar movimientos](#get-apimovimientos-inventario)
  - [Crear movimiento](#post-apimovimientos-inventario)
  - [Detalle de movimiento](#get-apimovimientos-inventarioid)
  - [Crear entrada](#post-apimovimientos-inventariocrear-entrada)
  - [Crear salida](#post-apimovimientos-inventariocrear-salida)
  - [Crear transferencia](#post-apimovimientos-inventariocrear-transferencia)
  - [Anular movimiento](#post-apimovimientos-inventarioidanular)
  - [Kardex](#get-apimovimientos-inventariokardex)
  - [Resumen](#get-apimovimientos-inventarioresumen)
- [Permisos](#permisos)
- [Tipos y estados](#tipos-y-estados)

---

## Modelo de datos

### MovimientoInventario

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `numero` | string | Auto-generado. Formato: `{PREFIJO}-YYYYMMDD-####` |
| `fecha` | datetime | Fecha y hora del movimiento (UTC) |
| `fecha_local` | datetime | Fecha en timezone de la empresa |
| `tipo` | string | Ver [tipos válidos](#tipos-y-estados) |
| `tipo_display` | string | Nombre legible del tipo |
| `estado` | string | `borrador` / `aplicado` / `anulado` |
| `bodega_origen` | UUID (write) | FK a Bodega — requerido para salidas, transferencias y mermas |
| `bodega_origen_nombre` | string (read) | Nombre de la bodega origen |
| `bodega_destino` | UUID (write) | FK a Bodega — requerido para entradas y transferencias |
| `bodega_destino_nombre` | string (read) | Nombre de la bodega destino |
| `responsable` | UUID (write) | FK a Empleado — opcional |
| `responsable_nombre` | string (read) | Nombre completo del responsable |
| `autorizado_por` | UUID | FK a User — opcional |
| `autorizado_por_nombre` | string (read) | Nombre del autorizador |
| `referencia` | string | Auto-generada si no se provee. Formato: `{TIPO}-REF-YYYYMMDD-###` |
| `observaciones` | string | Notas adicionales — opcional |
| `detalles` | array (read) | Lista de productos del movimiento |
| `detalles_data` | array (write) | Productos a incluir en el movimiento |
| `total_productos` | integer (read) | Cantidad de ítems distintos |
| `cantidad_total` | integer (read) | Suma de todas las cantidades |
| `costo_total` | decimal (read) | Costo total del movimiento |
| `created_at` | datetime | Fecha de creación |
| `updated_at` | datetime | Fecha de última actualización |

### DetalleMovimiento

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `producto` | UUID (write) | FK a Producto |
| `producto_nombre` | string (read) | Nombre del producto |
| `producto_codigo` | string (read) | Código del producto |
| `unidad_medida` | string (read) | Nombre de la unidad de medida |
| `cantidad` | integer | Cantidad — debe ser mayor a cero |
| `costo_unitario` | decimal | Auto-completado desde `ultimo_costo` → `costo_promedio` → `precio_compra` |
| `lote` | string | Auto-generado si no se provee. Formato: `L-{PREFIJO}-YYYYMMDD-###` |
| `fecha_vencimiento` | date | Obligatoria para productos perecederos. Auto-calculada si el producto tiene `dias_vida_util` |
| `stock_anterior` | integer (read) | Stock antes del movimiento |
| `stock_posterior` | integer (read) | Stock después del movimiento |
| `observaciones` | string | Notas del ítem — opcional |

---

## Endpoints

### GET `/api/movimientos-inventario/`

Listar movimientos con filtros y paginación.

**Permiso:** `ver_movimiento_inventario`

#### Query params

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `tipo` | string | Filtrar por tipo: `entrada`, `salida`, `transferencia`, etc. |
| `bodega_id` | UUID | Filtrar por bodega origen o destino |
| `producto_id` | UUID | Filtrar movimientos que incluyan el producto |
| `fecha_desde` | date | Filtrar desde fecha (`YYYY-MM-DD`) |
| `fecha_hasta` | date | Filtrar hasta fecha (`YYYY-MM-DD`) |
| `search` | string | Buscar en `numero`, `referencia`, `observaciones` |
| `ordering` | string | Ordenar por `fecha`, `numero`, `tipo`. Prefijo `-` para DESC |
| `page` | integer | Página (paginación por 50) |

#### Respuesta `200`

```json
{
  "success": true,
  "data": {
    "count": 120,
    "next": "/api/movimientos-inventario/?page=2",
    "previous": null,
    "results": [
      {
        "id": "501ee8e5-dc23-4bcb-9378-49991157ad97",
        "numero": "ENT-20251221-0001",
        "fecha": "2025-12-21T04:48:35.173643Z",
        "fecha_local": "2025-12-20T23:48:35",
        "tipo": "entrada",
        "tipo_display": "Entrada",
        "estado": "aplicado",
        "bodega_origen_nombre": null,
        "bodega_destino_nombre": "Bodega Central",
        "responsable_nombre": null,
        "referencia": "ENT-REF-20251221-001",
        "observaciones": "Ingreso desde proveedor",
        "total_productos": 2,
        "cantidad_total": 40,
        "costo_total": 2210.0
      }
    ]
  }
}
```

---

### POST `/api/movimientos-inventario/`

Crear un movimiento genérico especificando `tipo` en el body. Para flujos más directos usar los atajos por tipo.

**Permiso:** `crear_movimiento_inventario`

#### Body

```json
{
  "tipo": "entrada",
  "bodega_destino": "1c6c87a3-0a3a-4878-a0e1-a08aee947205",
  "responsable": "c012cb64-e9e4-4884-a364-78738fcdd61b",
  "referencia": "COMPRA-2025-001",
  "observaciones": "Texto opcional",
  "detalles_data": [
    {
      "producto": "fd87d709-a089-4892-817a-06f4cab9c1a2",
      "cantidad": 20,
      "costo_unitario": 25.50,
      "lote": "L-PFTA-20251221-001",
      "fecha_vencimiento": "2026-06-01",
      "observaciones": "Texto opcional"
    }
  ]
}
```

> `costo_unitario`, `lote` y `fecha_vencimiento` son opcionales — se auto-completan según las reglas del producto.

#### Respuesta `201`

```json
{
  "success": true,
  "mensaje": "Movimiento registrado exitosamente",
  "data": { /* MovimientoInventario completo */ }
}
```

---

### GET `/api/movimientos-inventario/{id}/`

Detalle completo de un movimiento, incluyendo todos sus detalles de productos.

**Permiso:** `ver_movimiento_inventario`

#### Respuesta `200`

```json
{
  "success": true,
  "data": {
    "id": "501ee8e5-dc23-4bcb-9378-49991157ad97",
    "numero": "ENT-20251221-0001",
    "fecha": "2025-12-21T04:48:35.173643Z",
    "fecha_local": "2025-12-20T23:48:35",
    "tipo": "entrada",
    "tipo_display": "Entrada",
    "estado": "aplicado",
    "bodega_destino_nombre": "Bodega Central",
    "referencia": "ENT-REF-20251221-001",
    "observaciones": "Ingreso de productos",
    "detalles": [
      {
        "id": "03ed6852-9c44-4e83-9f42-ad591892cc1e",
        "producto_nombre": "Pastillas de freno TVS Apache",
        "producto_codigo": "PFTA-SIS-0001",
        "unidad_medida": "Par",
        "cantidad": 20,
        "costo_unitario": "25.50",
        "lote": "L-PFTA-20251221-001",
        "fecha_vencimiento": null,
        "stock_anterior": 0,
        "stock_posterior": 20,
        "observaciones": ""
      }
    ],
    "total_productos": 1,
    "cantidad_total": 20,
    "costo_total": 510.0
  }
}
```

---

### POST `/api/movimientos-inventario/crear-entrada/`

Atajo para registrar una entrada. Fuerza `tipo = "entrada"` — no incluirlo en el body.

**Permiso:** `crear_movimiento_inventario`

**Reglas de bodegas:**
- `bodega_destino` → **requerida**
- `bodega_origen` → **no debe enviarse**

#### Body

```json
{
  "bodega_destino": "1c6c87a3-0a3a-4878-a0e1-a08aee947205",
  "observaciones": "Ingreso desde proveedor Dell",
  "detalles_data": [
    {
      "producto": "fd87d709-a089-4892-817a-06f4cab9c1a2",
      "cantidad": 20
    },
    {
      "producto": "78b6e874-1710-4e4b-9dca-2638a7cd857e",
      "cantidad": 10
    }
  ]
}
```

#### Respuesta `201`

```json
{
  "success": true,
  "mensaje": "Entrada de inventario registrada exitosamente",
  "data": { /* MovimientoInventario completo */ }
}
```

---

### POST `/api/movimientos-inventario/crear-salida/`

Atajo para registrar una salida. Fuerza `tipo = "salida"`.

**Permiso:** `crear_movimiento_inventario`

**Reglas de bodegas:**
- `bodega_origen` → **requerida**
- `bodega_destino` → **no debe enviarse**

> Valida stock disponible antes de aplicar. Si el stock es insuficiente retorna `400` con el detalle del producto.

#### Body

```json
{
  "bodega_origen": "1c6c87a3-0a3a-4878-a0e1-a08aee947205",
  "referencia": "VENTA-2025-00123",
  "detalles_data": [
    {
      "producto": "fd87d709-a089-4892-817a-06f4cab9c1a2",
      "cantidad": 5
    }
  ]
}
```

#### Respuesta `201`

```json
{
  "success": true,
  "mensaje": "Salida de inventario registrada exitosamente",
  "data": { /* MovimientoInventario completo */ }
}
```

---

### POST `/api/movimientos-inventario/crear-transferencia/`

Atajo para transferir stock entre bodegas. Fuerza `tipo = "transferencia"`.

**Permiso:** `crear_movimiento_inventario`

**Reglas de bodegas:**
- `bodega_origen` → **requerida**
- `bodega_destino` → **requerida**, debe ser diferente a `bodega_origen`

#### Body

```json
{
  "bodega_origen": "1c6c87a3-0a3a-4878-a0e1-a08aee947205",
  "bodega_destino": "7b3f91a2-1234-4def-b456-c9d8e7f01234",
  "observaciones": "Reabastecimiento sucursal norte",
  "detalles_data": [
    {
      "producto": "fd87d709-a089-4892-817a-06f4cab9c1a2",
      "cantidad": 10
    }
  ]
}
```

#### Respuesta `201`

```json
{
  "success": true,
  "mensaje": "Transferencia registrada exitosamente",
  "data": { /* MovimientoInventario completo */ }
}
```

---

### POST `/api/movimientos-inventario/{id}/anular/`

Anula un movimiento creando un movimiento inverso que revierte el stock. Los movimientos no se editan — solo se anulan.

**Permiso:** `autorizar_movimiento`

**Tipos anulables:** `entrada`, `salida`, `transferencia`

| Tipo original | Movimiento inverso generado |
|---------------|-----------------------------|
| `entrada` | `salida` (bodegas invertidas) |
| `salida` | `entrada` (bodegas invertidas) |
| `transferencia` | `transferencia` (origen/destino intercambiados) |

#### Body

```json
{
  "motivo": "Error en la factura de compra"
}
```

#### Respuesta `200`

```json
{
  "success": true,
  "mensaje": "Movimiento anulado exitosamente",
  "data": {
    "movimiento_original": "ENT-20251221-0001",
    "movimiento_anulacion": "SAL-20251221-0002"
  }
}
```

---

### GET `/api/movimientos-inventario/kardex/`

Historial cronológico de movimientos de un producto (kardex), con stock antes y después de cada movimiento.

**Permiso:** `ver_movimiento_inventario`

#### Query params

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | UUID | ✅ | Producto a consultar |
| `bodega_id` | UUID | — | Filtrar por bodega específica |
| `fecha_desde` | date | — | Desde `YYYY-MM-DD` |
| `fecha_hasta` | date | — | Hasta `YYYY-MM-DD` |

#### Respuesta `200`

```json
{
  "success": true,
  "data": {
    "producto": {
      "id": "fd87d709-a089-4892-817a-06f4cab9c1a2",
      "codigo": "PFTA-SIS-0001",
      "nombre": "Pastillas de freno TVS Apache",
      "stock_actual": 45,
      "stock_reservado": 5,
      "stock_disponible": 40
    },
    "kardex": [
      {
        "fecha": "2025-12-21T04:48:35.173643Z",
        "numero": "ENT-20251221-0001",
        "tipo": "entrada",
        "tipo_display": "Entrada",
        "bodega_origen": null,
        "bodega_destino": "Bodega Central",
        "cantidad": 20,
        "stock_anterior": 0,
        "stock_posterior": 20,
        "costo_unitario": 25.50,
        "lote": "L-PFTA-20251221-001",
        "referencia": "ENT-REF-20251221-001",
        "observaciones": ""
      }
    ],
    "total_movimientos": 1
  }
}
```

---

### GET `/api/movimientos-inventario/resumen/`

Resumen estadístico de movimientos agrupado por tipo para un período.

**Permiso:** `ver_movimiento_inventario`

#### Query params

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `fecha_desde` | date | Desde `YYYY-MM-DD` |
| `fecha_hasta` | date | Hasta `YYYY-MM-DD` |

#### Respuesta `200`

```json
{
  "success": true,
  "data": {
    "periodo": {
      "desde": "2025-01-01",
      "hasta": "2025-12-31"
    },
    "total_movimientos": 350,
    "por_tipo": [
      { "tipo": "entrada",       "total": 120, "productos": 1840 },
      { "tipo": "salida",        "total": 180, "productos": 3200 },
      { "tipo": "transferencia", "total": 40,  "productos": 620  },
      { "tipo": "merma",         "total": 10,  "productos": 85   }
    ]
  }
}
```

---

## Permisos

| Permiso | Endpoints |
|---------|-----------|
| `ver_movimiento_inventario` | `list`, `retrieve`, `kardex`, `resumen` |
| `crear_movimiento_inventario` | `create`, `crear-entrada`, `crear-salida`, `crear-transferencia` |
| `autorizar_movimiento` | `anular` |

---

## Tipos y estados

### Tipos de movimiento (`tipo`)

| Valor | Descripción | Bodega origen | Bodega destino |
|-------|-------------|:---:|:---:|
| `entrada` | Ingreso de productos al inventario | ✗ | ✅ |
| `salida` | Egreso de productos del inventario | ✅ | ✗ |
| `transferencia` | Traslado entre bodegas | ✅ | ✅ |
| `ajuste` | Ajuste de inventario | opcional | opcional |
| `devolucion` | Devolución de producto | opcional | opcional |
| `merma` | Pérdida o deterioro | ✅ | ✗ |

### Estados (`estado`)

| Valor | Descripción |
|-------|-------------|
| `borrador` | Creado pero no aplicado |
| `aplicado` | Stock actualizado |
| `anulado` | Revertido mediante movimiento inverso |

---

## Comportamiento automático

### Número de movimiento
Se genera automáticamente al crear. No se puede especificar manualmente.

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| entrada | `ENT-YYYYMMDD-####` | `ENT-20251221-0001` |
| salida | `SAL-YYYYMMDD-####` | `SAL-20251221-0003` |
| transferencia | `TRF-YYYYMMDD-####` | `TRF-20251221-0001` |
| ajuste | `AJU-YYYYMMDD-####` | `AJU-20251221-0001` |
| devolucion | `DEV-YYYYMMDD-####` | `DEV-20251221-0001` |
| merma | `MER-YYYYMMDD-####` | `MER-20251221-0001` |

### Número de lote
Auto-generado por producto si no se provee. Formato: `L-{PREFIJO}-YYYYMMDD-###`

### Costo unitario
Auto-completado siguiendo esta prioridad: `ultimo_costo` → `costo_promedio` → `precio_compra`

### Fecha de vencimiento (productos perecederos)
- Si el producto tiene `dias_vida_util`: se calcula como `hoy + dias_vida_util`
- Si no tiene `dias_vida_util`: debe enviarse manualmente, de lo contrario retorna error `400`

### Referencia
Auto-generada si no se envía. Formato: `{TIPO}-REF-YYYYMMDD-###`

---

## Errores comunes

| Código | Causa |
|--------|-------|
| `400` | Stock insuficiente para salida o transferencia |
| `400` | Bodega origen igual a bodega destino en transferencia |
| `400` | Producto perecedero sin fecha de vencimiento ni `dias_vida_util` |
| `400` | `detalles_data` vacío |
| `400` | Motivo de anulación no enviado |
| `400` | Tipo de movimiento no anulable (`ajuste`, `devolucion`, `merma`) |
| `403` | Permiso insuficiente |
| `404` | Producto o movimiento no encontrado |