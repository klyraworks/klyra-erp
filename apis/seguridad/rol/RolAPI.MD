# API — Roles

**Base URL:** `/api/roles/`  
**App:** `seguridad`

---

## Qué hace

Gestiona los roles del sistema con soporte multi-tenant. Cada rol combina **permisos técnicos** (via grupos Django) y **permisos de negocio** (campos booleanos y límites operativos). Al modificar los grupos de un rol, los cambios se propagan **inmediatamente** a los `user_permissions` de todos los empleados activos con ese rol — sin re-login.

---

## Endpoints

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/roles/` | `ver_rol` | Listar roles |
| POST | `/api/roles/` | `crear_rol` | Crear rol |
| GET | `/api/roles/{id}/` | `ver_rol` | Detalle con grupos y permisos |
| PUT/PATCH | `/api/roles/{id}/` | `editar_rol` | Actualizar |
| DELETE | `/api/roles/{id}/` | `eliminar_rol` | Soft delete |
| GET | `/api/roles/buscar/?q=texto` | `ver_rol` | Búsqueda para selects |
| GET | `/api/roles/grupos-disponibles/` | `ver_rol` | Grupos Django del sistema |
| POST | `/api/roles/{id}/asignar-grupos/` | `editar_rol` | Reemplazar grupos del rol |

---

## Campos

### Escritura (POST / PUT / PATCH)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Único por empresa |
| `descripcion` | string | — | Descripción del rol |
| `nivel_jerarquico` | integer | — | 1–10, donde 10 es el más alto. Default: 1 |
| `grupos_django_ids` | integer[] | — | IDs de `Group` de Django a asignar |
| `monto_maximo_descuento` | decimal | — | Descuento máximo permitido (%) — 0 a 100 |
| `monto_maximo_aprobacion` | decimal | — | Monto máximo que puede aprobar |
| `limite_credito_clientes` | decimal | — | Límite de crédito que puede otorgar a clientes |
| `puede_aprobar_vacaciones` | boolean | — | Default: false |
| `puede_ver_salarios` | boolean | — | Default: false |
| `puede_modificar_precios` | boolean | — | Default: false |
| `puede_anular_documentos` | boolean | — | Default: false |

### Lectura (GET)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `codigo` | string | Auto-generado: `ROL-{correlativo:04d}` |
| `nombre` | string | Nombre del rol |
| `descripcion` | string | Descripción |
| `nivel_jerarquico` | integer | Nivel jerárquico del rol |
| `grupos_django` | array | `[{id, name, permisos: [{id, codename, name}]}]` |
| `total_empleados` | integer | Empleados activos con este rol |
| `monto_maximo_descuento` | decimal | — |
| `monto_maximo_aprobacion` | decimal | — |
| `limite_credito_clientes` | decimal | — |
| `puede_aprobar_vacaciones` | boolean | — |
| `puede_ver_salarios` | boolean | — |
| `puede_modificar_precios` | boolean | — |
| `puede_anular_documentos` | boolean | — |
| `created_at` | datetime | Fecha de creación |
| `updated_at` | datetime | Última actualización |

---

## Ejemplos

### Crear rol

```json
POST /api/roles/
{
  "nombre": "Supervisor de Ventas",
  "descripcion": "Acceso completo al módulo de ventas",
  "nivel_jerarquico": 5,
  "grupos_django_ids": [2, 3],
  "monto_maximo_descuento": 15.00,
  "monto_maximo_aprobacion": 5000.00,
  "puede_modificar_precios": true,
  "puede_anular_documentos": true
}
```

**Respuesta `201`**
```json
{
  "success": true,
  "mensaje": "Rol creado exitosamente",
  "data": {
    "id": "a1b2c3d4-...",
    "codigo": "ROL-0001",
    "nombre": "Supervisor de Ventas",
    "nivel_jerarquico": 5,
    "grupos_django": [
      {
        "id": 2,
        "name": "Ventas - Básico",
        "permisos": [
          { "id": 45, "codename": "ver_venta", "name": "Puede ver ventas" },
          { "id": 46, "codename": "crear_venta", "name": "Puede crear ventas" }
        ]
      }
    ],
    "total_empleados": 0,
    "monto_maximo_descuento": "15.00",
    "monto_maximo_aprobacion": "5000.00",
    "puede_modificar_precios": true,
    "puede_anular_documentos": true,
    "puede_aprobar_vacaciones": false,
    "puede_ver_salarios": false,
    "limite_credito_clientes": "0.00",
    "is_active": true,
    "created_at": "2025-12-21T04:48:35Z",
    "updated_at": "2025-12-21T04:48:35Z"
  }
}
```

### Asignar/reemplazar grupos

```json
POST /api/roles/{id}/asignar-grupos/
{
  "grupos_ids": [2, 3, 5]
}
```

### Consultar grupos disponibles

```
GET /api/roles/grupos-disponibles/
GET /api/roles/grupos-disponibles/?q=ventas
```

**Respuesta `200`**
```json
{
  "success": true,
  "data": {
    "total": 3,
    "grupos": [
      {
        "id": 2,
        "nombre": "Ventas - Básico",
        "permisos": [
          { "id": 45, "codename": "ver_venta", "name": "Puede ver ventas" }
        ]
      }
    ]
  }
}
```

---

## Lógica de negocio

- **`codigo`** se genera automáticamente: `ROL-0001`, `ROL-0002`, etc. No se puede enviar manualmente.
- **`nombre`** es único por empresa.
- **Permisos técnicos:** se gestionan a través de `grupos_django` — grupos de Django que agrupan `Permission`. El sistema usa `tiene_permiso_django(codename)` para verificar acceso.
- **Permisos de negocio:** campos directos del modelo que el ERP consulta para operaciones específicas (`puede_aprobar_monto()`, `puede_dar_descuento()`). No están ligados al sistema de permisos de Django.
- **Sincronización:** al modificar `grupos_django_ids` (vía `update`, `partial_update` o `asignar-grupos`), el sistema ejecuta `user.user_permissions.set(permisos_de_grupos)` en cada empleado activo con ese rol. El efecto es inmediato sin re-login.
- **`grupos_django_ids` en PATCH:** si no se envía el campo, los grupos existentes no se tocan. Enviar `[]` elimina todos los grupos del rol y limpia `user_permissions` de sus empleados.
- **Eliminar:** bloqueado si tiene empleados activos asignados.
- **Al asignar rol a un empleado** (desde `EmpleadoViewSet`): sincronizar también `user_permissions` con `usuario.user_permissions.set(Permission.objects.filter(group__in=nuevo_rol.grupos_django.all()).distinct())`.

---

## Filtros disponibles

| Parámetro | Descripción |
|-----------|-------------|
| `search` | Busca en `codigo` y `nombre` |
| `ordering` | `codigo`, `nombre`, `nivel_jerarquico`, `created_at` |
| `page` | Paginación (50 por página) |
| `q` | En `grupos-disponibles` — filtrar por nombre de grupo |