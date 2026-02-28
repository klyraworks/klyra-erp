# API de Clientes — Klyra ERP

**Base URL:** `/api/personas/clientes/`  
**Autenticación:** `Authorization: Bearer <token>`  
**App:** `apis/persona`

---

## Endpoints

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/api/personas/clientes/` | `ver_cliente` | Listar clientes |
| POST | `/api/personas/clientes/` | `crear_cliente` | Crear cliente |
| GET | `/api/personas/clientes/{id}/` | `ver_cliente` | Detalle de cliente |
| PUT | `/api/personas/clientes/{id}/` | `editar_cliente` | Actualizar cliente |
| PATCH | `/api/personas/clientes/{id}/` | `editar_cliente` | Actualizar parcial |
| DELETE | `/api/personas/clientes/{id}/` | `eliminar_cliente` | Eliminar (soft delete) |
| GET | `/api/personas/clientes/buscar/` | `ver_cliente` | Búsqueda para selects |
| PATCH | `/api/personas/clientes/{id}/cambiar_estado/` | `editar_cliente` | Activar / Desactivar |
| GET | `/api/personas/clientes/{id}/saldo_credito/` | `gestionar_credito` | Consultar saldo de crédito |
| GET | `/api/personas/clientes/consumidor_final/` | `ver_cliente` | Obtener consumidor final (singleton) |

---

## Filtros y búsqueda

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `tipo` | string | `natural` \| `juridica` |
| `tipo_identificacion` | string | `ruc` \| `cedula` \| `pasaporte` \| `consumidor_final` |
| `activo` | boolean | `true` \| `false` |
| `search` | string | Busca en `razon_social`, `identificacion`, `codigo` |
| `ordering` | string | `razon_social`, `codigo`, `created_at` (prefijo `-` para DESC) |

---

## Referencia de campos

### Choices

**`tipo`**

| Valor | Etiqueta |
|-------|----------|
| `natural` | Persona Natural |
| `juridica` | Persona Jurídica |

**`tipo_identificacion`**

| Valor | Etiqueta |
|-------|----------|
| `ruc` | RUC |
| `cedula` | Cédula |
| `pasaporte` | Pasaporte |
| `consumidor_final` | Consumidor Final |

---

## POST `/api/personas/clientes/` — Crear cliente

**Body:**

```json
{
  "tipo": "natural",
  "tipo_identificacion": "cedula",
  "identificacion": "1234567890",
  "razon_social": "Carlos Mendoza",
  "limite_credito": "500.00",
  "descuento_porcentaje": "5.00",
  "email_facturacion": "carlos@email.com",
  "telefono_facturacion": "0991234567",
  "direccion": "Av. Principal 123",
  "persona_id": "uuid-opcional-o-null"
}
```

**Respuesta `201`:**

```json
{
  "success": true,
  "mensaje": "Cliente creado exitosamente",
  "data": { /* ClienteDetailSerializer */ }
}
```

**Validaciones:**
- `identificacion` única por empresa
- RUC → 13 dígitos exactos
- Cédula → 10 dígitos exactos
- `tipo = juridica` requiere `tipo_identificacion = ruc`
- `persona_id` debe pertenecer a la misma empresa

---

## GET `/api/personas/clientes/{id}/saldo_credito/`

**Respuesta `200`:**

```json
{
  "success": true,
  "data": {
    "limite_credito": 500.00,
    "credito_disponible": 320.00,
    "credito_usado": 180.00,
    "porcentaje_usado": 36.0
  }
}
```

---

## PATCH `/api/personas/clientes/{id}/cambiar_estado/`

Alterna `is_active` del cliente. No requiere body.

**Respuesta `200`:**

```json
{
  "success": true,
  "mensaje": "Cliente activado exitosamente",
  "data": { "is_active": true }
}
```

> El **consumidor final** no puede ser desactivado ni eliminado.

---

## GET `/api/personas/clientes/consumidor_final/`

Retorna el consumidor final de la empresa. Si no existe, lo crea automáticamente (singleton por empresa).

**Respuesta `200`:**

```json
{
  "success": true,
  "data": {
    "codigo": "CLI-0001",
    "tipo_identificacion": "consumidor_final",
    "identificacion": "9999999999999",
    "razon_social": "CONSUMIDOR FINAL",
    ...
  }
}
```

---

## GET `/api/personas/clientes/buscar/?q=texto`

Búsqueda sobre `razon_social`, `identificacion` y `codigo`. Solo retorna clientes activos. Máximo 20 resultados.

**Respuesta `200`:**

```json
{
  "success": true,
  "data": {
    "results": [ /* ClienteListSerializer[] */ ],
    "total": 5
  }
}
```

---

## Gestión de crédito

El crédito se administra mediante los métodos del modelo. Los ViewSets de ventas y finanzas deben invocarlos directamente, **nunca modificar `credito_disponible` directamente en la BD**.

| Método | Cuándo llamarlo |
|--------|----------------|
| `cliente.reducir_credito(monto)` | Al confirmar una venta a crédito |
| `cliente.liberar_credito(monto)` | Al registrar un pago o anular una venta |
| `cliente.puede_comprar_a_credito(monto)` | Antes de confirmar la venta (validación previa) |

`liberar_credito` nunca supera el `limite_credito` — el excedente se descarta automáticamente.

---

## Permisos personalizados

| Permiso | Descripción |
|---------|-------------|
| `ver_cliente` | CRUD lectura + buscar + consumidor_final |
| `crear_cliente` | POST |
| `editar_cliente` | PUT, PATCH, cambiar_estado |
| `eliminar_cliente` | DELETE (soft delete) |
| `gestionar_credito` | Consultar saldo_credito |
| `ver_historial_compras` | Acceso al historial de compras del cliente |