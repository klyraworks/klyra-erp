# Klyra ERP System

Sistema ERP modular para PyMEs ecuatorianas con facturación electrónica integrada, multi‑empresa y multi‑bodega, con backend Django + DRF y frontend Next.js (React + TypeScript).

---

## 📋 Tabla de Contenidos
- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Mapa de Apps y Estado Actual](#mapa-de-apps-y-estado-actual)
- [Modelos Clave por App](#modelos-clave-por-app)
- [APIs y Endpoints Activos](#apis-y-endpoints-activos)
  - [Autenticación JWT](#autenticación-jwt)
  - [Documentación OpenAPI](#documentación-openapi)
  - [Módulo Base](#módulo-base)
  - [Módulo Inventario](#módulo-inventario)
  - [Módulo Ventas](#módulo-ventas)
  - [Módulo RRHH](#módulo-rrhh)
- [Multitenancy y Contexto de Empresa](#multitenancy-y-contexto-de-empresa)
- [Frontend (Next.js)](#frontend-nextjs)
- [Configuración y Entornos](#configuración-y-entornos)
- [Instalación y Puesta en Marcha](#instalación-y-puesta-en-marcha)
- [Despliegue](#despliegue)
- [Pruebas](#pruebas)
- [Registro y Monitoreo](#registro-y-monitoreo)
- [Roadmap](#roadmap)
- [Contribuir](#contribuir)
- [Licencia](#licencia)
- [Contacto](#contacto)

---

## 📖 Descripción
Klyra ERP es un sistema modular orientado a operaciones empresariales en Ecuador: inventario, ventas, compras, finanzas, RRHH y facturación electrónica SRI. Provee una API REST completa, interfaz moderna y un modelo de seguridad basado en permisos de Django.

Beneficios clave:
- Cumplimiento con normativa ecuatoriana (SRI) y base para facturación electrónica
- Multi‑empresa, multi‑bodega y trazabilidad de stock
- Interfaz moderna y responsive (Next.js + Tailwind)
- Documentación de API generada automáticamente (OpenAPI/Swagger)

---

## 🏗️ Arquitectura
- Monorepo con backend en Django/DRF y frontend en Next.js.
- Comunicación vía API REST (`/api/...`) protegida con JWT (access/refresh).
- Contexto multi‑empresa mediante middleware a nivel de request.
- Documentación de API con `drf-spectacular` y UI Swagger en `/api/docs/`.
- PostgreSQL como base de datos relacional.

Diagrama alto nivel:
```
[Frontend (Next.js)]  →  [API DRF: /api/*]
                             │
                             ├── apps.base, apps.inventario, apps.ventas, apps.compras,
                             │   apps.finanzas, apps.rrhh, apps.facturacion
                             │
                        [Servicios / Managers / Utils]
                             │
                         [PostgreSQL Database]
```

---

## 🛠️ Tecnologías
- Backend: Python 3.11+, Django 5.x, Django REST Framework, drf‑spectacular, SimpleJWT, CORS Headers
- DB: PostgreSQL 14+
- Frontend: Next.js 16, React 19, TypeScript, TailwindCSS 4, Radix UI, SWR
- Dev: Docker Compose (opcional), dotenv, python‑decouple, cities_light

---

## 🗂️ Estructura del Proyecto
Ruta raíz: `C:\PycharmProjects\Klyra`

```
Klyra/                      # Proyecto Django (settings, urls)
apis/                       # API REST (ViewSets/routers por módulo)
apps/                       # Apps de dominio (models, migrations)
frontend/                   # Next.js (App Router)
middleware/                 # Middlewares (TenantMiddleware)
managers/, utils/, shared/  # Utilidades y helpers comunes
templates/, static/, media/ # Plantillas, estáticos, uploads
requirements/               # Requerimientos Python por entorno
logs/                       # Archivos de log (p.ej. facturacion_electronica.log)
manage.py                   # CLI Django
```

---

## 🧭 Mapa de Apps y Estado Actual
Origen: `Klyra/settings/base.py`

- Django core y terceros (ACTIVO):
  - `django.contrib.*`, `rest_framework`, `rest_framework_simplejwt`, `corsheaders`, `cities_light`
- Apps de dominio (ACTIVO si listada abajo):
  - `apps.base` (ACTIVO)
  - `apps.compras` (ACTIVO)
  - `apps.finanzas` (ACTIVO)
  - `apps.inventario` (ACTIVO)
  - `apps.rrhh` (ACTIVO)
  - `apps.ventas` (ACTIVO)
  - `apps.facturacion` (ACTIVO)

Middlewares relevantes (ACTIVO): `middleware.tenant_middleware.TenantMiddleware`

---

## 📘 Modelos Clave por App
A continuación, un resumen de modelos principales. El detalle completo se encuentra en los archivos de cada app.

- apps.base
  - Modelos base y utilitarios compartidos (p. ej., `BaseModel`, timestamps, `is_active`).

- apps.rrhh
  - `Empleado` (relación con `Empresa`, utilizada por el middleware para determinar `request.empresa`).

- apps.inventario (archivo: `apps/inventario/models.py`)
  - `Categoria`
    - Jerárquica (`categoria_padre`, `nivel` calculado)
    - `codigo` autogenerado (prefijo + correlativo de 2 dígitos, p. ej., `MOT-01`)
    - Permisos específicos (p. ej., `ver_jerarquia_categorias`)
  - `Marca`
  - `UnidadMedida` y `UnidadConversion`
  - `Producto`
  - `Bodega`, `Stock`, `TransferenciaBodega`
  - `MovimientoInventario`, `DetalleMovimiento`

- apps.ventas
  - Entidades de ventas: `Cliente`, `Venta`, `Pago` (expuestas vía API, ver Endpoints).

- apps.compras, apps.finanzas, apps.facturacion
  - Estructura presente; detalle funcional en evolución. `apps.facturacion` integra con SRI (logs en `logs/facturacion_electronica.log`).

Nota: los modelos de Inventario están optimizados con `select_related`/`prefetch_related` a nivel de vistas para evitar N+1.

---

## 🌐 APIs y Endpoints Activos
Enrutamiento global: `Klyra/urls.py` incluye las URLs de `apis.base`, `apis.seguridad`, `apis.ventas`, `apis.inventario` bajo la raíz; cada módulo expone sus rutas bajo `/api/`.

Base URL de API en desarrollo: `http://localhost:8000/api/`

### Autenticación JWT
- `POST /api/auth/login/` → obtiene tokens de acceso y refresco
- `POST /api/auth/refresh/` → renueva token de acceso

Ejemplo (login):
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<tu_pass>"}'
```

### Documentación OpenAPI
- Esquema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`

### Módulo Base
Archivo: `apis/base/urls.py` (ACTIVO)
- `POST /api/enviaremail/` — Envío de correo (ViewSet `EnvioEmail`)
- `GET  /api/user/me/` — Usuario autenticado actual

### Módulo Inventario
Archivo: `apis/inventario/urls.py` (ACTIVO)

Recursos expuestos vía `DefaultRouter` (CRUD completo por `ModelViewSet`, salvo restricciones de permisos):
- `GET /api/productos/` — Listar
- `POST /api/productos/` — Crear
- `GET /api/productos/{id}/` — Detalle
- `PUT/PATCH /api/productos/{id}/` — Actualizar
- `DELETE /api/productos/{id}/` — Eliminar

- `GET /api/categorias/` — Listar (filtros soportados: `nivel`, `padre`, `search`)
- `POST /api/categorias/`
- `GET /api/categorias/{id}/`
- `PUT/PATCH /api/categorias/{id}/`
- `DELETE /api/categorias/{id}/`

- `GET /api/marcas/`, `POST /api/marcas/`, `GET/PUT/PATCH/DELETE /api/marcas/{id}/`
- `GET /api/unidades-medida/`, `POST /api/unidades-medida/`, `GET/PUT/PATCH/DELETE /api/unidades-medida/{id}/`
- `GET /api/movimientos-inventario/`, `POST /api/movimientos-inventario/`, `GET/PUT/PATCH/DELETE /api/movimientos-inventario/{id}/`
- `GET /api/bodegas/`, `POST /api/bodegas/`, `GET/PUT/PATCH/DELETE /api/bodegas/{id}/`

Detalles relevantes — `CategoriaViewSet` (`apis/inventario/categoria/categoria_viewset.py`):
- Permisos: `IsAuthenticated` + verificación de permisos por acción (`view/add/change/delete`)
- Optimización: `select_related('categoria_padre')` y `prefetch_related('subcategorias' ... hasta 6 niveles)`
- Ordenación por `nivel`, `nombre`, `id`
- Filtros de query:
  - `nivel`: entero (1, 2, 3, ...)
  - `padre`: id de categoría padre (vacío para raíz)
  - `search`: por `codigo`, `nombre`, `descripcion`

### Módulo Ventas
Archivo: `apis/ventas/urls.py` (ACTIVO)
- `GET/POST /api/clientes/` y `GET/PUT/PATCH/DELETE /api/clientes/{id}/`
- `GET/POST /api/productos/` y `GET/PUT/PATCH/DELETE /api/productos/{id}/` (expuesto aquí para consultas desde ventas)
- `GET/POST /api/ventas/` y `GET/PUT/PATCH/DELETE /api/ventas/{id}/`
- `GET/POST /api/pagos/` y `GET/PUT/PATCH/DELETE /api/pagos/{id}/`

### Módulo RRHH
Archivo: `apis/rrhh/urls.py` (ACTIVO)
- `GET/POST /api/empleados/` y `GET/PUT/PATCH/DELETE /api/empleados/{id}/`

Notas de estado:
- Todos los routers anteriores están INCLUIDOS en `Klyra/urls.py` → ENDPOINTS ACTIVOS.
- Autenticación JWT y documentación OpenAPI están ACTIVAS.

---

## 🏢 Multitenancy y Contexto de Empresa
Archivo: `middleware/tenant_middleware.py` (ACTIVO)
- `TenantMiddleware` adjunta `request.empresa` si el usuario autenticado posee `empleado.empresa`.
- Helpers thread‑local: `get_current_empresa()`, `set_current_empresa()`, `clear_current_empresa()`.
- Limpieza del contexto al finalizar cada request o ante excepciones.

Impacto: facilita la segregación de datos por empresa y su uso en managers/queries/permissions.

---

## ⚛️ Frontend (Next.js)
- Next.js 16 (App Router) + React 19 + TypeScript
- TailwindCSS 4 + Radix UI + SWR + React Hook Form

Rutas y módulos destacados:
- `frontend/app/(dashboard)/inventario/categorias/[id]/page.tsx`
- `frontend/app/(dashboard)/inventario/categorias/[id]/editar/page.tsx`
- Componentes: `categorias-section.tsx`, `bodegas-section.tsx`, `productos-section.tsx`
- Formularios: `activar-cuenta-form.tsx`, `producto-form.tsx`
- Componente compartido: `src/shared/components/header.tsx`

---

## ⚙️ Configuración y Entornos
Variables de entorno (via `python-decouple` y `.env`):
- `SECRET_KEY`
- `DEBUG` (true/false)
- `ALLOWED_HOSTS` (coma‑separado)
- CORS: orígenes permitidos (`http://localhost:3000`, `http://192.168.1.100:3000` por defecto)
- DB: configuración PostgreSQL (usar settings por entorno)

Archivos relevantes:
- `Klyra/settings/base.py`
- `requirements/` (dependencias por entorno)
- `docker-compose.yml` (si se usa)

---

## 🚀 Instalación y Puesta en Marcha
Backend:
1) Crear y activar entorno virtual (Windows)
```bash
python -m venv .venv
.\.venv\Scripts\activate
```
2) Instalar dependencias
```bash
pip install -r requirements/base.txt
```
3) Configurar `.env`
```bash
SECRET_KEY=...
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
```
4) Migraciones + superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```
5) Carga opcional de catálogos
```bash
python manage.py cities_light
# python manage.py setup_inventario_roles   # si existe
```
6) Ejecutar servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 📦 Despliegue
- `DEBUG=false`, `ALLOWED_HOSTS` definido
- Servir estáticos con `collectstatic` y Nginx
- WSGI/ASGI server (gunicorn/uvicorn workers)
- DB PostgreSQL gestionada, backups, HTTPS

---

## ✅ Pruebas
```bash
python manage.py test
```
- Tests unitarios por app y tests de API con DRF.

---

## 🧾 Registro y Monitoreo
- Logs en `logs/` (ej.: `logs/facturacion_electronica.log`).
- Configurar niveles de logging por entorno y rotación.

---

## 🗺️ Roadmap
- [ ] Completar reglas de negocio avanzadas en Inventario
- [ ] Flujos de compras/ventas con aprobaciones
- [ ] Contabilidad (asientos automáticos y reportes)
- [ ] Integración SRI (emisión/recepción) end‑to‑end
- [ ] Auditoría y bitácoras
- [ ] i18n

---

## 🤝 Contribuir
- Issues/PRs con descripción clara, pasos y evidencias.
- Estilo PEP8 y convenciones del proyecto.

---

## 📄 Licencia
Pendiente (propietaria o MIT). Agregar `LICENSE` cuando se decida.

---

## 📬 Contacto
- Equipo Klyra
- Soporte: soporte@klyra.local
- API Docs: `http://localhost:8000/api/docs/`
