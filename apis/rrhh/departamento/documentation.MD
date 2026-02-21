# API — Departamentos

**Base URL:** `/api/departamentos/`  
**App:** `rrhh`  
**Permisos requeridos:** `ver_departamento`, `crear_departamento`, `editar_departamento`, `eliminar_departamento`

---

## Endpoints

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/departamentos/` | `ver_departamento` | Listar todos los departamentos |
| POST | `/api/departamentos/` | `crear_departamento` | Crear departamento |
| GET | `/api/departamentos/{id}/` | `ver_departamento` | Detalle de un departamento |
| PUT/PATCH | `/api/departamentos/{id}/` | `editar_departamento` | Actualizar departamento |
| DELETE | `/api/departamentos/{id}/` | `eliminar_departamento` | Soft delete |
| GET | `/api/departamentos/buscar/?q=texto` | `ver_departamento` | Búsqueda para selects |

---

## Campos

### Escritura (POST / PUT / PATCH)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Único por empresa |
| `descripcion` | string | — | Descripción opcional |
| `jefe_id` | UUID | — | FK a Empleado activo. `null` para quitar jefe |

### Lectura (GET)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `codigo` | string | Auto-generado: `DEPT-{PREFIJO}-{correlativo:02d}` |
| `nombre` | string | Nombre del departamento |
| `descripcion` | string | Descripción |
| `jefe` | object | `{id, codigo, nombre}` del jefe asignado |
| `total_empleados` | integer | Empleados activos en el departamento |
| `is_active` | boolean | Estado del registro |
| `created_at` | datetime | Fecha de creación |
| `updated_at` | datetime | Fecha de última actualización |

---

## Ejemplos

### Crear departamento

```json
POST /api/departamentos/
{
  "nombre": "Tecnología",
  "descripcion": "Departamento de desarrollo y sistemas",
  "jefe_id": "c012cb64-e9e4-4884-a364-78738fcdd61b"
}
```

**Respuesta `201`**
```json
{
  "success": true,
  "mensaje": "Departamento creado exitosamente",
  "data": {
    "id": "a1b2c3d4-...",
    "codigo": "DEPT-TEC-01",
    "nombre": "Tecnología",
    "descripcion": "Departamento de desarrollo y sistemas",
    "jefe": {
      "id": "c012cb64-...",
      "codigo": "EMP-0001",
      "nombre": "Carlos Mendoza"
    },
    "total_empleados": 0,
    "is_active": true,
    "created_at": "2025-12-21T04:48:35Z",
    "updated_at": "2025-12-21T04:48:35Z"
  }
}
```

### Quitar jefe de un departamento

```json
PATCH /api/departamentos/{id}/
{
  "jefe_id": null
}
```

### Búsqueda para select

```
GET /api/departamentos/buscar/?q=tec
```

```json
{
  "success": true,
  "data": {
    "results": [
      { "id": "a1b2c3d4-...", "codigo": "DEPT-TEC-01", "nombre": "Tecnología", "jefe_nombre": "Carlos Mendoza", "total_empleados": 5 }
    ],
    "total": 1
  }
}
```

---

## Lógica de negocio

- **`codigo`** se genera automáticamente en el modelo (`DEPT-{PREFIJO}-{correlativo:02d}`). No se puede enviar manualmente.
- **`nombre`** es único por empresa. Intentar crear o actualizar con un nombre existente retorna `400`.
- **`jefe_id`** debe ser un empleado activo de la misma empresa. Enviar `null` limpia el jefe asignado.
- **Eliminar:** no se permite si el departamento tiene empleados activos asignados. Retorna `400` con el conteo de empleados que bloquean la eliminación. Si no tiene empleados, aplica soft delete (`deleted_at`).
- **Dependencias:** `Empleado` tiene FK a `Departamento`. Crear empleados requiere que el departamento exista previamente.

---

## Filtros disponibles

| Parámetro | Descripción |
|-----------|-------------|
| `jefe` | UUID — filtrar por jefe asignado |
| `search` | Busca en `codigo` y `nombre` |
| `ordering` | `codigo`, `nombre`, `created_at` (prefijo `-` para DESC) |
| `page` | Paginación (50 por página) |