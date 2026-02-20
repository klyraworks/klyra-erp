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

export interface Region {
    id: number
    geoname_id: number
    name: string
}

export interface Ciudad {
    id: number
    name: string
    region: Region | null
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
    direccion: string | null
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
}

/** Detalle completo — usado en retrieve */
export interface Empleado {
    id: string
    codigo: string
    persona: Persona
    usuario: UserBasico | null
    username: string | null
    puesto: string
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
    codigo_aux?: string
    nombre: string
    descripcion?: string
    tipo: 'simple' | 'kit' | 'servicio'
    es_kit: boolean
    tipo_display?: string

    // Relaciones — IDs para enviar, nombres para mostrar, detalle para renderizar
    categoria?: string
    categoria_nombre?: string
    categoria_detalle?: Categoria

    marca?: string
    marca_nombre?: string
    marca_detalle?: Marca

    unidad_medida?: number
    unidad_medida_nombre?: string
    unidad_medida_detalle?: UnidadMedida

    // Precios y stock
    precio_compra?: number
    precio_venta: number
    stock: number
    stock_minimo: number
    stock_estado?: 'agotado' | 'bajo' | 'medio' | 'normal'

    // Atributos
    iva: boolean
    codigo_barras?: string
    es_perecedero: boolean
    dias_vida_util?: number
    peso?: number
    imagen?: string | null
    is_active: boolean

    // Metadatos
    created_at?: string
    updated_at?: string

    // Calculados
    estado?: string
    margen_ganancia?: { monto: number; porcentaje: number }

    // Kit
    componentes_detalle?: KitComponente[]
    total_componentes?: number
    costo_componentes?: number | null

    // Inventario
    inventarios?: InventarioBodega[]
    conversiones_detalle?: UnidadConversion[]
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
// CLIENTES
// ============================================================

export interface Cliente {
    id: string
    ruc: string
    razon_social?: string
    nombre_completo?: string
    direccion?: string
    telefono?: string
    email?: string
    limite_credito: number
    credito_disponible: number
    activo?: boolean
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