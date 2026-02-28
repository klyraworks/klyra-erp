// frontend/src/core/api/types.ts
// ============================================================
// CONVENCIÓN DE NOMENCLATURA
// ============================================================
// Modelo             → interfaz completa (detail)
// ModeloListItem     → campos mínimos para tablas y selects
// ModeloCreate       → payload para POST
// ModeloUpdate       → payload para PATCH
// ModeloResponse     → respuestas especiales de actions
//
// Regla: los campos *_nombre son strings planos del serializer
// Las relaciones anidadas usan el tipo correspondiente
// ============================================================


// ============================================================
// COMUNES / REUTILIZABLES
// ============================================================

export interface PaginatedResponse<T> {
    count: number
    next: string | null
    previous: string | null
    results: T[]
}

export interface BuscarResponse<T> {
    results: T[]
    total: number
}


// ============================================================
// GEOGRAFÍA
// ============================================================

export interface Pais {
    id: number
    name: string
}

export interface Region {
    id: number
    geoname_id: number
    name: string
}

export interface Ciudad {
    id: number
    name: string
    region: Region | null
    pais: Pais | null
}


// ============================================================
// PERSONAS
// ============================================================

export interface Persona {
    id: number
    nombre1: string
    nombre2: string | null
    apellido1: string
    apellido2: string | null
    cedula: string | null
    pasaporte: string | null
    email: string
    telefono: string | null
    ciudad: Ciudad
    fecha_nacimiento: string | null
}


// ============================================================
// USUARIOS
// ============================================================

export interface UserBasico {
    id: number
    username: string
    is_active: boolean
}


// ============================================================
// ROLES Y DEPARTAMENTOS
// ============================================================

export interface RolBasico {
    id: string
    codigo: string
    nombre: string
}

export interface DepartamentoBasico {
    id: string
    nombre: string
}

export interface Departamento {
    id: string
    codigo: string
    nombre: string
    descripcion?: string
    jefe?: Empleado | null
    jefe_nombre?: string | null
    total_empleados: number
    is_active: boolean
    created_at?: string | number
}


// ============================================================
// EMPLEADOS
// ============================================================

/** Campos mínimos — usado en tablas, selects y buscar */
export interface EmpleadoListItem {
    id: string
    codigo: string
    nombre_completo: string
    cedula: string | null
    email: string
    puesto: string
    estado: 'activo' | 'inactivo' | 'suspendido' | 'terminado'
    rol_nombre: string | null
    departamento_nombre: string | null
    cuenta_activada: boolean
    fecha_contratacion: string
    tiene_acceso: boolean
}

/** Detalle completo — usado en retrieve */
export interface Empleado {
    id: string
    codigo: string
    persona: Persona
    usuario: UserBasico | null
    username: string | null
    puesto: Puesto
    salario: number
    fecha_contratacion: string
    fecha_terminacion: string | null
    estado: 'activo' | 'inactivo' | 'suspendido' | 'terminado'
    rol: RolBasico | null
    departamento: DepartamentoBasico | null
    debe_cambiar_password: boolean
    cuenta_activada: boolean
    fecha_activacion: string | null
    created_at: string
    updated_at: string
    email_activacion_enviado?: boolean
    nombre_completo: string
    cedula: string | null
    email: string
    rol_nombre: string | null
    departamento_nombre: string | null
    tiene_acceso: boolean
}

/** Payload para crear */
export interface EmpleadoCreate {
    persona: {
        nombre1: string
        nombre2?: string
        apellido1: string
        apellido2?: string
        cedula?: string
        pasaporte?: string
        email: string
        telefono?: string
        direccion?: string
        fecha_nacimiento?: string
    }
    puesto: string
    salario: string
    fecha_contratacion: string
    estado: string
    rol_id?: string | null
    departamento_id?: string | null
    crear_acceso: boolean
}

/** Payload para actualizar */
export interface EmpleadoUpdate {
    puesto?: string
    salario?: string
    fecha_contratacion?: string
    estado?: string
    rol_id?: string | null
    departamento_id?: string | null
}


// ============================================================
// CATEGORÍAS
// ============================================================

export interface Categoria {
    id: string
    codigo?: string
    nombre: string
    descripcion: string
    nivel: number
    categoria_padre?: string
    categoria_padre_nombre?: string
    subcategorias: Categoria[]
    subcategorias_count?: number
    productos_count?: number
    ruta_completa?: string
    is_active: boolean
    imagen: string | null
    created_at?: string
    updated_at?: string
}


// ============================================================
// MARCAS
// ============================================================

export interface Marca {
    id: string
    codigo: string
    nombre: string
    descripcion: string | null
    pais_origen: number | null
    pais_origen_nombre: string | null
    logo: string | null
    is_active: boolean
    estado: 'Activa' | 'Inactiva'
    total_productos: number
    created_at: string
    updated_at: string
    created_by: { id: number; nombre: string } | null
    updated_by: { id: number; nombre: string } | null
}

export interface MarcaListItem {
    id: string
    codigo: string
    nombre: string
    descripcion: string | null
    pais_origen_nombre: string | null
    logo: string | null
    is_active: boolean
    estado: 'Activa' | 'Inactiva'
    total_productos: number
}

export interface MarcaSimple {
    id: string
    codigo: string
    nombre: string
}

export interface MarcaCreate {
    nombre: string
    descripcion?: string
    pais_origen?: number
    logo?: File
}

export interface MarcaUpdate {
    nombre?: string
    descripcion?: string
    pais_origen?: number
    logo?: File
}


// ============================================================
// UNIDADES DE MEDIDA
// ============================================================

export interface UnidadMedida {
    id: number
    codigo: string
    nombre: string
    abreviatura: string
    tipo: string
    tipo_display?: string
}

export interface UnidadConversion {
    id: string
    unidad_origen: number
    unidad_origen_nombre?: string
    unidad_destino: number
    unidad_destino_nombre?: string
    factor_conversion: number
}


// ============================================================
// PRODUCTOS
// ============================================================

export interface KitComponente {
    id: string
    componente: string
    componente_nombre: string
    componente_codigo: string
    componente_precio: string
    cantidad: number
    es_opcional: boolean
    observaciones?: string
}

export interface InventarioBodega {
    id: string
    cantidad: number
    stock_reservado: number
    bodega: BodegaListItem
}

export interface Producto {
    id: string
    codigo: string
    codigo_aux?: string | null
    nombre: string
    descripcion?: string
    tipo: 'simple' | 'kit' | 'servicio'
    tipo_display?: string
    es_kit: boolean

    // Relaciones (detail)
    categoria?: { id: string; nombre: string; codigo: string } | null
    marca?: { id: string; nombre: string } | null
    unidad_medida?: { id: string; nombre: string; abreviatura: string } | null

    // Precios
    precio_compra?: number
    precio_venta: number
    stock_minimo: number
    costo_promedio?: number
    ultimo_costo?: number
    margen_ganancia?: { monto: number; porcentaje: number } | null
    iva: boolean

    // Características
    codigo_barras?: string
    es_perecedero: boolean
    dias_vida_util?: number | null
    peso?: number | null
    imagen?: string | null

    // Stock
    stock_total?: number | undefined | null
    stock_estado?: 'normal' | 'medio' | 'bajo' | 'agotado'
    inventarios?: StockBodega[]

    // Kit
    componentes?: Componente[]
    conversiones?: UnidadConversion[] | null | undefined

    // Meta
    is_active: boolean
    created_at?: string
    updated_at?: string
}

export interface StockBodega {
    id: string
    bodega: string
    bodega_nombre: string
    bodega_codigo: string
    es_principal: boolean
    permite_ventas: boolean
    cantidad: number
    stock_reservado: number
    cantidad_disponible: number
}

export type ProductoCreate = Omit<Producto,
    'id' | 'codigo' | 'codigo_aux' | 'created_at' | 'updated_at' |
    'estado' | 'margen_ganancia' | 'stock_estado' |
    'categoria_nombre' | 'marca_nombre' | 'unidad_medida_nombre' |
    'categoria_detalle' | 'marca_detalle' | 'unidad_medida_detalle' |
    'componentes_detalle' | 'total_componentes' | 'costo_componentes'
>

export type ProductoDuplicar = {
    nombre?: string
    codigo_aux?: string
}


// ============================================================
// BODEGAS
// ============================================================

/** Campos mínimos — usado en selects */
export interface BodegaListItem {
    id: string
    codigo: string
    nombre: string
    es_principal: boolean
    permite_ventas: boolean
    is_active: boolean
}

/** Detalle completo */
export interface Bodega {
    id: string
    codigo: string
    nombre: string
    ciudad: Ciudad | null
    direccion: string
    telefono: string
    capacidad_m3: number | null
    responsable: EmpleadoListItem | null   // ← usa EmpleadoListItem, no Empleado completo
    es_principal: boolean
    permite_ventas: boolean
    is_active: boolean
    total_productos?: number
    valor_total_inventario?: number
    responsable_nombre?: string
    ciudad_nombre?: string
}


// ============================================================
// COMPONENTES
// ============================================================

export interface Componente {
    id: string
    componente: string          // UUID del producto componente
    componente_nombre?: string
    componente_codigo?: string
    componente_precio?: number
    cantidad: number
    es_opcional: boolean
    observaciones?: string
    // Campos locales (solo en frontend, no vienen del API)
    nombre?: string
    codigo?: string
    precio_venta?: number
}


// ============================================================
// CLIENTES
// ============================================================

// ── Agregar a src/core/api/types.ts ──────────────────────────────────────────

export type ClienteTipo = "natural" | "juridica"
export type ClienteTipoIdentificacion = "ruc" | "cedula" | "pasaporte" | "consumidor_final"

export interface Cliente {
    id: string
    codigo: string
    tipo: ClienteTipo
    tipo_identificacion: ClienteTipoIdentificacion
    identificacion: string
    razon_social: string
    limite_credito: string
    descuento_porcentaje: string
    email_facturacion: string | null
    telefono_facturacion: string | null
    direccion: string | null
    is_active: boolean
    created_at: string
    updated_at: string
}

export interface ClienteListItem {
    id: string
    codigo: string
    tipo: ClienteTipo
    tipo_identificacion: ClienteTipoIdentificacion
    identificacion: string
    razon_social: string
    limite_credito: string
    is_active: boolean
}

export interface ClienteCreate {
    tipo: ClienteTipo
    tipo_identificacion: ClienteTipoIdentificacion
    identificacion: string
    razon_social: string
    limite_credito?: string
    descuento_porcentaje?: string
    email_facturacion?: string | null
    telefono_facturacion?: string | null
    direccion?: string | null
}

export interface ClienteUpdate extends Partial<ClienteCreate> {}

export interface ClienteSaldo {
    limite_credito: number
    credito_disponible: number
    credito_usado: number
    porcentaje_usado: number
}


// ============================================================
// VENTAS
// ============================================================

export interface VentaDetalle {
    id: string
    producto: string
    producto_nombre?: string
    cantidad: number
    precio_unitario: number
    subtotal: number
}

export interface Venta {
    id: string
    numero: string
    fecha: string
    cliente?: string
    cliente_nombre?: string
    estado: 'borrador' | 'confirmada' | 'facturada' | 'despachada' | 'anulada' | 'pendiente'
    tipo_pago: 'contado' | 'credito'
    subtotal: number
    impuesto: number
    total: number
    saldo_pendiente?: number
    observaciones?: string
    detalles?: VentaDetalle
    fecha_local: string
}


// ============================================================
// PAGOS
// ============================================================

export interface Pago {
    id: string
    venta?: { id: string; numero: string }
    fecha: string
    monto: number
    metodo: string
    referencia?: string
    observaciones?: string
    fecha_local: string
}


// ============================================================
// MOVIMIENTOS DE INVENTARIO
// ============================================================

export interface MovimientoDetalle {
    id: string
    producto: string
    producto_nombre?: string
    cantidad: number
}

export interface MovimientoInventario {
    id: string
    numero: string
    tipo: 'entrada' | 'salida' | 'ajuste' | 'transferencia'
    fecha: string
    bodega_origen?: string
    bodega_origen_nombre?: string
    bodega_destino?: string
    bodega_destino_nombre?: string
    referencia?: string
    observaciones?: string
    detalles?: MovimientoDetalle
    fecha_local: string
}


// ============================================================
// INVENTARIO — RESPONSES ESPECIALES
// ============================================================

export interface InventarioBodegaItem {
    id: string
    producto_id: string
    producto_codigo: string
    producto_nombre: string
    categoria_nombre: string
    unidad_medida: string
    bodega_id: string
    bodega_codigo: string
    bodega_nombre: string
    cantidad: number
    stock_reservado: number
    stock_disponible: number
    estado_stock: 'sin_stock' | 'critico' | 'bajo' | 'normal'
    necesita_reposicion: boolean
}

// Alias — mismo shape, nombre semántico para el contexto de stock
export type StockItem = InventarioBodegaItem

export interface InventarioTotalResponse {
    producto: {
        id: string
        codigo: string
        nombre: string
        stock_minimo: number
    }
    resumen: {
        total_bodegas: number
        stock_total: number
        stock_reservado: number
        stock_disponible: number
        estado_general: string
        necesita_reposicion: boolean
    }
    valorizacion?: {
        valor_compra: number
        valor_venta: number
        utilidad_potencial: number
    }
    por_bodega: Array<{
        bodega: {
            id: string
            codigo: string
            nombre: string
            es_principal: boolean
            permite_ventas: boolean
        }
        ubicacion?: { id: string; nombre: string }
        cantidad: number
        stock_reservado: number
        stock_disponible: number
        estado: string
    }>
}

export interface EtiquetaProductoResponse {
    producto: {
        codigo: string
        codigo_barras: string
        nombre: string
        descripcion: string
        precio_venta: number
        unidad_medida: string
    }
    categoria: string
    marca: string
    iva: string
    fecha_generacion: string
    empresa: { nombre: string; ruc: string }
}


// ============================================================
// ROLES - PERMISOS
// ============================================================

export interface PermisoDjango {
    id: number
    codename: string
    name: string
}

export interface GrupoDjango {
    id: number
    nombre: string
    permisos: PermisoDjango[]
}

export interface RolListItem {
    id: string
    codigo: string
    nombre: string
    descripcion: string
    nivel_jerarquico: number
    total_grupos: number
    total_empleados: number
}

export interface Rol {
    id: string
    codigo: string
    nombre: string
    descripcion: string
    nivel_jerarquico: number
    grupos_django: GrupoDjango[]
    total_empleados: number
    monto_maximo_descuento: string | null
    monto_maximo_aprobacion: string | null
    limite_credito_clientes: string | null
    puede_aprobar_vacaciones: boolean
    puede_ver_salarios: boolean
    puede_modificar_precios: boolean
    puede_anular_documentos: boolean
    is_active: boolean
    created_at: string
    updated_at: string
}

// ============================================================
// INVENTARIO — PAYLOADS
// ============================================================

export interface PuestoListItem {
    id: string
    codigo: string
    nombre: string
    descripcion?: string
    departamento_nombre: string | null
    salario_minimo: string | null
    salario_maximo: string | null
    total_empleados: number
}

export interface Puesto {
    id: string
    codigo: string
    nombre: string
    descripcion: string
    departamento: { id: string; codigo: string; nombre: string } | null
    salario_minimo: string | null
    salario_maximo: string | null
    total_empleados: number
    is_active: boolean
    created_at: string
    updated_at: string
}

// ============================================================
// INVENTARIO — PAYLOADS
// ============================================================

export interface AjustarStockPayload {
    cantidad: number
    tipo: 'incremento' | 'decremento' | 'establecer'
    motivo: string
    referencia?: string
}

export interface CambiarUbicacionPayload {
    ubicacion_id: string
    motivo?: string
}

export interface DuplicarProductoPayload {
    nombre?: string
    codigo_aux?: string
}

export interface ReservarStockPayload {
    cantidad: number
    tipo: 'reservar' | 'liberar'
    referencia: string | undefined
    motivo?: string
}

export interface Ubicacion {
    id: string
    bodega: string
    pasillo: string
    estante: string
    nivel: string
    descripcion?: string
}

