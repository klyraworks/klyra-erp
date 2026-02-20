// frontend/src/core/api/client.ts

// ============================================
// API ERROR - Clase personalizada
// ============================================
export class ApiError extends Error {
    titulo: string
    mensaje: string
    errores: Record<string, any> | null
    statusCode: number

    constructor(titulo: string, mensaje: string, errores: Record<string, any> | null = null, statusCode: number = 0) {
        super(mensaje)
        this.name = 'ApiError'
        this.titulo = titulo
        this.mensaje = mensaje
        this.errores = errores
        this.statusCode = statusCode
    }
}

// ============================================
// URL BASE
// ============================================
const getApiUrl = (): string => {
    if (typeof window !== 'undefined') {
        const host = window.location.hostname

        if (host === 'localhost' || host === 'klyra-erp.com') {
            console.log('⚠️ Dominio sin subdominio detectado:', host)
            return ''
        }

        if (host.includes('.local') || host.includes('.klyra-erp.com')) {
            const url = `http://${host}:8000`
            console.log('✅ URL construida:', url)
            return url
        }
    }

    const fallback = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    console.log('⚠️ Usando fallback URL:', fallback)
    return fallback
}

const API_BASE_URL = getApiUrl()
console.log('📡 API_BASE_URL:', API_BASE_URL)

// ============================================
// REFRESH TOKEN
// ============================================
async function refreshToken(): Promise<boolean> {
    try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) {
            console.log('❌ No hay refresh token disponible')
            return false
        }

        console.log('🔄 Intentando refrescar token...')

        const res = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh }),
        })

        if (res.ok) {
            const text = await res.text()
            const data = text ? JSON.parse(text) : null
            localStorage.setItem('access_token', data.access)
            if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
            console.log('✅ Token refrescado exitosamente')
            return true
        }

        console.log('❌ Refresh token inválido o expirado, status:', res.status)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        return false
    } catch (error) {
        console.warn('❌ Error al refrescar token:', error)
        return false
    }
}

// ============================================
// PARSE API ERROR - Extrae titulo/mensaje del estándar
// ============================================
function parseApiError(data: any, statusCode: number): ApiError {
    if (data && typeof data === 'object') {
        const titulo = data.titulo || 'Error'
        const mensaje = data.mensaje || data.detail || data.warn || `Error ${statusCode}`
        const errores = data.warnes || null
        console.warn('❌ API Error:', { statusCode, titulo, mensaje, errores })
        return new ApiError(titulo, mensaje, errores, statusCode)
    }

    console.warn('❌ API Error sin estructura estándar, status:', statusCode)
    return new ApiError('Error', `Error ${statusCode}`, null, statusCode)
}

// ============================================
// LOGIN
// ============================================
export async function login(username: string, password: string): Promise<{
    user: any
    empleado: any
    empresa: any
    access: string
    refresh: string
}> {
    console.log('🔐 Iniciando login para:', username)

    const res = await fetch(`${API_BASE_URL}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    })

    console.log('📥 Login response status:', res.status)

    const text = await res.text()
    const data = text ? JSON.parse(text) : null

    if (!res.ok) {
        console.warn('❌ Login fallido:', data)
        throw parseApiError(data, res.status)
    }

    if (data.data?.access) {
        localStorage.setItem('access_token', data.data.access)
        localStorage.setItem('refresh_token', data.data.refresh)
        console.log('✅ Tokens JWT guardados')
    }

    console.log('✅ Login exitoso, usuario:', data.data?.user?.username)
    return data.data
}

// ============================================
// LOGOUT
// ============================================
export async function logout(): Promise<void> {
    console.log('🚪 Cerrando sesión...')

    const token = localStorage.getItem('access_token')

    if (token) {
        await fetch(`${API_BASE_URL}/api/auth/logout/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
        }).catch((error) => console.warn('❌ Error al llamar endpoint logout:', error))
    }

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    console.log('✅ Sesión cerrada, tokens eliminados')
}

// ============================================
// CHECK AUTH
// ============================================
export async function checkAuth(): Promise<{
    authenticated: boolean
    user?: any
    empleado?: any
    empresa?: any
}> {
    console.log('🔍 Verificando autenticación...')

    const token = localStorage.getItem('access_token')

    if (!token) {
        console.log('❌ No hay token, usuario no autenticado')
        return { authenticated: false }
    }

    console.log('🎫 Token presente, verificando con el servidor...')

    const res = await fetch(`${API_BASE_URL}/api/auth/check/`, {
        headers: { 'Authorization': `Bearer ${token}` },
    })

    console.log('📥 CheckAuth status:', res.status)

    if (res.ok) {
        const text = await res.text()
        const data = text ? JSON.parse(text) : null
        console.log('✅ Usuario autenticado:', data.data?.user?.username)
        return { authenticated: true, ...data.data }
    }

    if (res.status === 401) {
        console.log('🔄 Token expirado, intentando refresh...')
        const refreshed = await refreshToken()
        if (refreshed) {
            console.log('✅ Token refrescado, reintentando checkAuth...')
            return checkAuth()
        }
    }

    console.log('❌ Autenticación fallida, status:', res.status)
    return { authenticated: false }
}

// ============================================
// API FETCH
// ============================================
export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const token = localStorage.getItem('access_token')
    const url = `${API_BASE_URL}${endpoint}`
    const method = options?.method || 'GET'
    const isFormData = options?.body instanceof FormData

    console.log(`📡 [${method}] ${endpoint}`)

    const res = await fetch(url, {
        ...options,
        headers: {
            ...(!isFormData && { 'Content-Type': 'application/json' }),
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options?.headers,
        },
    })

    console.log(`📥 [${method}] ${endpoint} → status: ${res.status}`)

    if (!res.ok) {
        const text = await res.text()
        const data = text ? JSON.parse(text) : null

        if (res.status === 401) {
            console.log('🔄 Token expirado en apiFetch, intentando refresh...')
            const refreshed = await refreshToken()
            if (refreshed) {
                console.log('✅ Token refrescado, reintentando petición...')
                return apiFetch<T>(endpoint, options)
            }

            console.warn('❌ Sesión expirada, redirigiendo a login...')
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
            throw new ApiError('Sesión expirada', 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.', null, 401)
        }

        throw parseApiError(data, res.status)
    }

    const text = await res.text()
    const data = text ? JSON.parse(text) : null

    // Estándar de respuesta: retornar solo data.data
    if (data && typeof data === 'object' && 'success' in data && 'data' in data) {
        console.log(`✅ [${method}] ${endpoint} → respuesta estándar OK`)
        return data.data as T
    }

    console.log(`✅ [${method}] ${endpoint} → respuesta OK`)
    return data as T
}

// ============================================
// SWR FETCHER
// ============================================
export const swrFetcher = <T = unknown>(endpoint: string): Promise<T> => {
    return apiFetch<T>(endpoint)
}

// // frontend/src/core/api/client.ts
//
// // ============================================
// // API ERROR - Clase personalizada
// // ============================================
// export class ApiError extends Error {
//     titulo: string
//     mensaje: string
//     errores: Record<string, any> | null
//     statusCode: number
//
//     constructor(titulo: string, mensaje: string, errores: Record<string, any> | null = null, statusCode: number = 0) {
//         super(mensaje)
//         this.name = 'ApiError'
//         this.titulo = titulo
//         this.mensaje = mensaje
//         this.warnes = errores
//         this.statusCode = statusCode
//     }
// }
//
// // ============================================
// // URL BASE
// // ============================================
// const getApiUrl = (): string => {
//     if (typeof window !== 'undefined') {
//         const host = window.location.hostname
//
//         if (host === 'localhost' || host === 'klyra-erp.com') {
//             return ''
//         }
//
//         if (host.includes('.local') || host.includes('.klyra-erp.com')) {
//             return `http://${host}:8000`
//         }
//     }
//
//     return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
// }
//
// const API_BASE_URL = getApiUrl()
//
// // ============================================
// // REFRESH TOKEN
// // ============================================
// async function refreshToken(): Promise<boolean> {
//     try {
//         const refresh = localStorage.getItem('refresh_token')
//         if (!refresh) return false
//
//         const res = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ refresh }),
//         })
//
//         if (res.ok) {
//             const data = await res.json()
//             localStorage.setItem('access_token', data.access)
//             if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
//             return true
//         }
//
//         localStorage.removeItem('access_token')
//         localStorage.removeItem('refresh_token')
//         return false
//     } catch {
//         return false
//     }
// }
//
// // ============================================
// // PARSE API ERROR - Extrae titulo/mensaje del estándar
// // ============================================
// function parseApiError(data: any, statusCode: number): ApiError {
//     // Respuesta con estándar definido
//     if (data && typeof data === 'object') {
//         const titulo = data.titulo || 'Error'
//         const mensaje = data.mensaje || data.detail || data.warn || `Error ${statusCode}`
//         const errores = data.warnes || null
//         return new ApiError(titulo, mensaje, errores, statusCode)
//     }
//
//     return new ApiError('Error', `Error ${statusCode}`, null, statusCode)
// }
//
// // ============================================
// // LOGIN
// // ============================================
// export async function login(username: string, password: string): Promise<{
//     user: any
//     empleado: any
//     empresa: any
//     access: string
//     refresh: string
// }> {
//     const res = await fetch(`${API_BASE_URL}/api/auth/login/`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ username, password }),
//     })
//
//     const data = await res.json()
//
//     if (!res.ok) {
//         throw parseApiError(data, res.status)
//     }
//
//     if (data.data?.access) {
//         localStorage.setItem('access_token', data.data.access)
//         localStorage.setItem('refresh_token', data.data.refresh)
//     }
//
//     return data.data
// }
//
// // ============================================
// // LOGOUT
// // ============================================
// export async function logout(): Promise<void> {
//     const token = localStorage.getItem('access_token')
//
//     if (token) {
//         await fetch(`${API_BASE_URL}/api/auth/logout/`, {
//             method: 'POST',
//             headers: { 'Authorization': `Bearer ${token}` },
//         }).catch(() => {})
//     }
//
//     localStorage.removeItem('access_token')
//     localStorage.removeItem('refresh_token')
// }
//
// // ============================================
// // CHECK AUTH
// // ============================================
// export async function checkAuth(): Promise<{
//     authenticated: boolean
//     user?: any
//     empleado?: any
//     empresa?: any
// }> {
//     const token = localStorage.getItem('access_token')
//     if (!token) return { authenticated: false }
//
//     const res = await fetch(`${API_BASE_URL}/api/auth/check/`, {
//         headers: { 'Authorization': `Bearer ${token}` },
//     })
//
//     if (res.ok) {
//         const data = await res.json()
//         return { authenticated: true, ...data.data }
//     }
//
//     if (res.status === 401) {
//         const refreshed = await refreshToken()
//         if (refreshed) return checkAuth()
//     }
//
//     return { authenticated: false }
// }
//
// // ============================================
// // API FETCH
// // ============================================
// export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
//     const token = localStorage.getItem('access_token')
//     const url = `${API_BASE_URL}${endpoint}`
//
//     const isFormData = options?.body instanceof FormData
//
//     const res = await fetch(url, {
//         ...options,
//         headers: {
//             ...(!isFormData && { 'Content-Type': 'application/json' }),
//             ...(token && { 'Authorization': `Bearer ${token}` }),
//             ...options?.headers,
//         },
//     })
//
//     if (!res.ok) {
//         const data = await res.json().catch(() => ({}))
//
//         if (res.status === 401) {
//             const refreshed = await refreshToken()
//             if (refreshed) return apiFetch<T>(endpoint, options)
//
//             localStorage.removeItem('access_token')
//             localStorage.removeItem('refresh_token')
//             window.location.href = '/login'
//             throw new ApiError('Sesión expirada', 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.', null, 401)
//         }
//
//         throw parseApiError(data, res.status)
//     }
//
//     const data = await res.json()
//
//     // Estándar de respuesta: retornar solo data.data
//     if (data && typeof data === 'object' && 'success' in data && 'data' in data) {
//         return data.data as T
//     }
//
//     return data as T
// }
//
// // ============================================
// // SWR FETCHER
// // ============================================
// export const swrFetcher = <T = unknown>(endpoint: string): Promise<T> => {
//     return apiFetch<T>(endpoint)
// }