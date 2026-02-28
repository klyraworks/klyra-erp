// frontend/src/core/store/index.tsx
"use client"

import {createContext, useContext, useState, useEffect, type ReactNode} from "react"
import useSWR, {mutate} from "swr"
import {
    Venta,
    Producto,
    ClienteListItem,
    Bodega,
    Pago,
    MovimientoInventario,
    Categoria,
    UnidadMedida,
    Marca,
    ProductoCreate,
    DuplicarProductoPayload,
    InventarioTotalResponse,
    EtiquetaProductoResponse,
    AjustarStockPayload,
    CambiarUbicacionPayload,
    ReservarStockPayload,
    Ubicacion,
    Ciudad,
    StockItem,
    Empleado,
    UserBasico,
    Departamento,
    Puesto, PuestoListItem, Rol,
} from "@/src/core/api/types"
import {swrFetcher, apiFetch} from "@/src/core/api/client"

interface PaginatedResponse<T> {
    count: number
    next: string | null
    previous: string | null
    results: T[]
}

function extractArray<T>(data: T[] | PaginatedResponse<T> | undefined): T[] {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (typeof data === "object" && "results" in data) return data.results
    return []
}

interface Empresa {
    id: string
    nombre: string
    subdominio: string
    logo?: string
}

interface StoreContextType {
    user: UserBasico | null
    empleado: Empleado | null
    empresa: Empresa | null
    setAuth: (user: UserBasico, empleado: Empleado, empresa: Empresa) => void
    clearAuth: () => void
    isAuthenticated: boolean
    refreshAll: () => void
}

const StoreContext = createContext<StoreContextType | null>(null)

export function StoreProvider({children}: { children: ReactNode }) {
    const [user, setUser] = useState<UserBasico | null>(null)
    const [empleado, setEmpleado] = useState<Empleado | null>(null)
    const [empresa, setEmpresa] = useState<Empresa | null>(null)

    const setAuth = (newUser: UserBasico, newEmpleado: Empleado, newEmpresa: Empresa) => {
        setUser(newUser)
        setEmpleado(newEmpleado)
        setEmpresa(newEmpresa)
    }

    const clearAuth = () => {
        setUser(null)
        setEmpleado(null)
        setEmpresa(null)
    }

    const refreshAll = () => {
        mutate(["/api/ventas/"])
        mutate("/api/productos/")
        mutate("/api/personas/clientes/")
        mutate("/api/bodegas/")
        mutate("/api/pagos/")
        mutate("/api/movimientos-inventario/")
    }

    return (
        <StoreContext.Provider
            value={{
                user,
                empleado,
                empresa,
                setAuth,
                clearAuth,
                isAuthenticated: !!user,
                refreshAll,
            }}
        >
            {children}
        </StoreContext.Provider>
    )
}

export function useStore() {
    const context = useContext(StoreContext)
    if (!context) throw new Error("useStore must be used within StoreProvider")
    return context
}

// ============================================
// HOOKS SWR (sin token)
// ============================================

export function useVentas() {
    const result = useSWR<Venta[] | PaginatedResponse<Venta>>("/api/ventas/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useProductos() {
    const result = useSWR<Producto[] | PaginatedResponse<Producto>>("/api/productos/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useClientes() {
    const result = useSWR<ClienteListItem[] | PaginatedResponse<ClienteListItem>>(
        "/api/personas/clientes/",
        swrFetcher
    )
    return { ...result, data: extractArray(result.data) }
}

export function useBodegas() {
    const result = useSWR<Bodega[] | PaginatedResponse<Bodega>>("/api/bodegas/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function usePagos() {
    const result = useSWR<Pago[] | PaginatedResponse<Pago>>("/api/pagos/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useCategorias() {
    const result = useSWR<Categoria[] | PaginatedResponse<Categoria>>("/api/categorias/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useDepartamentos() {
    const result = useSWR<Departamento[] | PaginatedResponse<Departamento>>("/api/rrhh/departamentos/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useEmpleados() {
    const result = useSWR<Empleado[] | PaginatedResponse<Empleado>>("/api/seguridad/empleados/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function usePuestos() {
    const result = useSWR<PuestoListItem[] | PaginatedResponse<PuestoListItem>>("/api/rrhh/puestos/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useRoles() {
    const result = useSWR<Rol[] | PaginatedResponse<Rol>>("/api/seguridad/roles/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}



export function useCategoriasArbolExpandido() {
    const result = useSWR<{ total_categorias: number; categorias: Categoria[] }>(
        "/api/categorias/arbol_expandido/",
        swrFetcher
    )

    return {
        ...result,
        data: result.data?.categorias || [],
        total: result.data?.total_categorias || 0
    }
}

export function useUnidadesMedida() {
    const result = useSWR<UnidadMedida[] | PaginatedResponse<UnidadMedida>>("/api/unidades-medida/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useMarcas() {
    const result = useSWR<Marca[] | PaginatedResponse<Marca>>("/api/marcas/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useMovimientos() {
    const result = useSWR<MovimientoInventario[] | PaginatedResponse<MovimientoInventario>>(
        "/api/movimientos-inventario/", swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useUbicaciones(bodegaId?: string) {
    const url = bodegaId ? `/api/ubicaciones/?bodega_id=${bodegaId}` : "/api/ubicaciones/"
    const result = useSWR<Ubicacion[] | PaginatedResponse<Ubicacion>>(url, swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export function useCiudades() {
    const result = useSWR<Ciudad[]>("/api/core/ciudades/", swrFetcher)
    return result
}

// ============================================
// FUNCIONES (sin token)
// ============================================

export async function addProducto(producto: ProductoCreate): Promise<Producto> {
    const nuevoProducto = await apiFetch<Producto>("/api/productos/", {
        method: "POST",
        body: JSON.stringify(producto),
    })

    mutate("/api/productos/")
    return nuevoProducto
}

export async function viewProducto(producto: Producto): Promise<Producto> {
    return await apiFetch<Producto>(`/api/productos/${producto.id}/`, {
        method: "GET",
    })
}


export async function ajustarStockBodega(
    stockId: string,
    payload: AjustarStockPayload
): Promise<any> {
    const resultado = await apiFetch(
        `/api/stock/${stockId}/ajustar_stock/`,
        {
            method: "POST",
            body: JSON.stringify(payload),
        }
    )

    mutate("/api/stock/")
    mutate("/api/productos/")
    return resultado
}

export async function cambiarUbicacionBodega(
    stockId: string,
    payload: CambiarUbicacionPayload
): Promise<any> {
    const resultado = await apiFetch(
        `/api/stock/${stockId}/cambiar-ubicacion/`,
        {
            method: "POST",
            body: JSON.stringify(payload),
        }
    )

    mutate("/api/stock/")
    return resultado
}

export async function reservarStockBodega(
    stockId: string,
    payload: ReservarStockPayload
): Promise<any> {
    const resultado = await apiFetch(
        `/api/stock/${stockId}/reservar_stock/`,
        {
            method: "POST",
            body: JSON.stringify(payload),
        }
    )

    mutate("/api/stock/")
    return resultado
}

export async function getKardex(
    productoId: string,
    bodegaId?: string,
    fechaDesde?: string,
    fechaHasta?: string
) {
    let url = `/api/movimientos-inventario/kardex/?producto_id=${productoId}`
    if (bodegaId) url += `&bodega_id=${bodegaId}`
    if (fechaDesde) url += `&fecha_desde=${fechaDesde}`
    if (fechaHasta) url += `&fecha_hasta=${fechaHasta}`

    return await apiFetch(url, {method: "GET"})
}

export function useStock() {
    const result = useSWR<StockItem[] | PaginatedResponse<StockItem>>('/api/stock/', swrFetcher)
    return {...result, data: extractArray(result.data)}
}

export async function agregarImagenProducto(
    productoId: string,
    imagen: File
): Promise<{ imagen_url: string }> {
    const formData = new FormData()
    formData.append('imagen', imagen)

    return await apiFetch(`/api/productos/${productoId}/agregar_imagen/`, {
        method: 'POST',
        body: formData,
    })
}

export async function duplicarProducto(
    productoId: string,
    payload: DuplicarProductoPayload
): Promise<Producto> {
    const resultado = await apiFetch<Producto>(
        `/api/productos/${productoId}/duplicar/`,
        {
            method: 'POST',
            body: JSON.stringify(payload),
        }
    )
    mutate('/api/productos/')
    return resultado
}

export async function getInventarioTotal(productoId: string): Promise<InventarioTotalResponse> {
    return await apiFetch<InventarioTotalResponse>(
        `/api/productos/${productoId}/inventario_total/`,
        {method: 'GET'}
    )
}

export async function getEtiquetaProducto(productoId: string): Promise<EtiquetaProductoResponse> {
    return await apiFetch<EtiquetaProductoResponse>(
        `/api/productos/${productoId}/imprimir_etiqueta/`,
        {method: 'GET'}
    )
}