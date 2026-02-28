# API — Puestos

**Base URL:** `/api/puestos/`  
**App:** `rrhh`  
**Depende de:** `Departamento` (debe existir antes de crear un puesto)

---

## Qué hace

Gestiona los puestos de trabajo de la empresa. Cada puesto pertenece a un departamento y define el rango salarial del cargo. Es requisito previo para crear empleados.

---

## Endpoints

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/puestos/` | `ver_puesto` | Listar puestos |
| POST | `/api/puestos/` | `crear_puesto` | Crear puesto |
| GET | `/api/puestos/{id}/` | `ver_puesto` | Detalle |
| PUT/PATCH | `/api/puestos/{id}/` | `editar_puesto` | Actualizar |
| DELETE | `/api/puestos/{id}/` | `eliminar_puesto` | Soft delete |
| GET | `/api/puestos/buscar/?q=texto` | `ver_puesto` | Búsqueda para selects |

---

## Campos

### Escritura (POST / PUT / PATCH)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Único por empresa |
| `descripcion` | string | — | Descripción del cargo |
| `departamento_id` | UUID | ✅ en POST | FK a Departamento activo de la empresa |
| `salario_minimo` | decimal | — | Rango inferior del cargo |
| `salario_maximo` | decimal | — | Rango superior — debe ser ≥ `salario_minimo` |

### Lectura (GET)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `codigo` | string | Auto-generado: `PUE-{PREFIJO}-{correlativo:02d}` |
| `nombre` | string | Nombre del puesto |
| `descripcion` | string | Descripción |
| `departamento` | object | `{id, codigo, nombre}` |
| `salario_minimo` | decimal | Salario mínimo del cargo |
| `salario_maximo` | decimal | Salario máximo del cargo |
| `total_empleados` | integer | Empleados activos en este puesto |
| `created_at` | datetime | Fecha de creación |
| `updated_at` | datetime | Última actualización |

---

## Ejemplos

### Crear puesto

```json
POST /api/puestos/
{
  "nombre": "Desarrollador Backend",
  "descripcion": "Desarrollo y mantenimiento de APIs REST",
  "departamento_id": "a1b2c3d4-...",
  "salario_minimo": 1200.00,
  "salario_maximo": 2500.00
}
```

**Respuesta `201`**
```json
{
  "success": true,
  "mensaje": "Puesto creado exitosamente",
  "data": {
    "id": "f1e2d3c4-...",
    "codigo": "PUE-DES-01",
    "nombre": "Desarrollador Backend",
    "descripcion": "Desarrollo y mantenimiento de APIs REST",
    "departamento": {
      "id": "a1b2c3d4-...",
      "codigo": "DEPT-TEC-01",
      "nombre": "Tecnología"
    },
    "salario_minimo": "1200.00",
    "salario_maximo": "2500.00",
    "total_empleados": 0,
    "is_active": true,
    "created_at": "2025-12-21T04:48:35Z",
    "updated_at": "2025-12-21T04:48:35Z"
  }
}
```

### Búsqueda filtrada por departamento

```
GET /api/puestos/buscar/?q=dev&departamento_id=a1b2c3d4-...
```

---

## Lógica de negocio

- **`codigo`** se genera automáticamente en el modelo. No se puede enviar manualmente.
- **`nombre`** es único por empresa. Retorna `400` si ya existe.
- **`salario_maximo`** debe ser ≥ `salario_minimo`. Se valida tanto en creación como en actualización, comparando contra el valor actual del campo si solo se envía uno de los dos en un PATCH.
- **Eliminar:** bloqueado si el puesto tiene empleados activos asignados. Retorna `400` con el conteo.
- **Cambio de rango salarial:** no afecta el salario de empleados existentes — solo aplica como referencia para nuevas contrataciones.
- **`departamento_id`** es requerido al crear. En PATCH es opcional — si no se envía, el departamento no cambia.

---

## Filtros disponibles

| Parámetro | Descripción |
|-----------|-------------|
| `departamento` | UUID — filtrar por departamento |
| `departamento_id` | UUID — alias via query param en `get_queryset` |
| `search` | Busca en `codigo` y `nombre` |
| `ordering` | `codigo`, `nombre`, `salario_minimo`, `salario_maximo`, `created_at` |
| `page` | Paginación (50 por página) |