"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { alertas } from "@/components/alerts/alertas-toast"

// ============================================
// TIPOS
// ============================================
interface EmpleadoInfo {
    nombre: string
    nombre_completo: string
    username: string
    puesto: string
}

interface VerificarTokenResponse {
    valido: boolean
    empleado: EmpleadoInfo
    expira_en: string
}

interface ActivarCuentaResponse {
    access: string
    refresh: string
    empleado: {
        id: string
        nombre_completo: string
        username: string
        puesto: string
    }
}

// ============================================
// HELPERS
// ============================================
const getApiUrl = (): string => {
    if (typeof window !== 'undefined') {
        const host = window.location.hostname
        if (host.includes('.local') || host.includes('.klyra-erp.com')) {
            return `http://${host}:8000`
        }
    }
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

async function verificarToken(token: string): Promise<VerificarTokenResponse> {
    const res = await fetch(
        `${getApiUrl()}/api/verificar-token/?token=${token}`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } }
    )
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Token inválido o expirado.')
    return data.data
}

async function activarCuenta(
    token: string,
    password: string,
    password_confirmacion: string
): Promise<ActivarCuentaResponse> {
    const res = await fetch(
        `${getApiUrl()}/api/activar-cuenta/`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, password, password_confirmacion }),
        }
    )
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || data.errores?.password?.[0] || 'Error al activar la cuenta.')
    return data.data
}

// ============================================
// ESTADOS DEL FORMULARIO
// ============================================
type FormState = 'verificando' | 'token_invalido' | 'listo' | 'enviando' | 'activado'

// ============================================
// COMPONENTE PRINCIPAL
// ============================================
export function ActivarCuentaForm() {
    const router = useRouter()
    const params = useParams()
    const token = params?.id as string

    const [estado, setEstado] = useState<FormState>('verificando')
    const [empleado, setEmpleado] = useState<EmpleadoInfo | null>(null)
    const [errorToken, setErrorToken] = useState('')

    const [formData, setFormData] = useState({
        password: '',
        password_confirmacion: '',
    })
    const [mostrarPassword, setMostrarPassword] = useState(false)
    const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false)
    const [errores, setErrores] = useState<Record<string, string>>({})

    // -- Verificar token al montar
    useEffect(() => {
        if (!token) {
            setEstado('token_invalido')
            setErrorToken('No se proporcionó un token de activación.')
            return
        }

        verificarToken(token)
            .then((data) => {
                setEmpleado(data.empleado)
                setEstado('listo')
            })
            .catch((err) => {
                setErrorToken(err.message)
                setEstado('token_invalido')
            })
    }, [token])

    // -- Validación local
    const validar = (): boolean => {
        const nuevosErrores: Record<string, string> = {}

        if (!formData.password) {
            nuevosErrores.password = 'La contraseña es requerida.'
        } else if (formData.password.length < 8) {
            nuevosErrores.password = 'La contraseña debe tener al menos 8 caracteres.'
        }

        if (!formData.password_confirmacion) {
            nuevosErrores.password_confirmacion = 'Confirma tu contraseña.'
        } else if (formData.password !== formData.password_confirmacion) {
            nuevosErrores.password_confirmacion = 'Las contraseñas no coinciden.'
        }

        setErrores(nuevosErrores)
        return Object.keys(nuevosErrores).length === 0
    }

    // -- Submit
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (estado === 'enviando') return
        if (!validar()) return

        setEstado('enviando')
        setErrores({})

        try {
            const data = await activarCuenta(
                token,
                formData.password,
                formData.password_confirmacion
            )

            // Guardar tokens JWT — login automático
            localStorage.setItem('access_token', data.access)
            localStorage.setItem('refresh_token', data.refresh)

            setEstado('activado')
            alertas.success(
                `¡Bienvenido ${data.empleado.nombre_completo}!`,
                'Cuenta activada'
            )

            setTimeout(() => {
                router.push('/dashboard')
            }, 2000)

        } catch (err: any) {
            setEstado('listo')
            alertas.error(err.message, 'Error al activar')
        }
    }

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        if (errores[field]) {
            setErrores(prev => ({ ...prev, [field]: '' }))
        }
    }

    // ============================================
    // RENDERS POR ESTADO
    // ============================================
    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <div className="w-full max-w-md">

                {/* Logo / Header */}
                <div className="text-center mb-8">
                    <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <i className="fa-solid fa-shield-halved text-primary text-2xl"></i>
                    </div>
                    <h1 className="text-2xl font-bold text-foreground">Klyra ERP</h1>
                    <p className="text-sm text-muted-foreground mt-1">Sistema de gestión empresarial</p>
                </div>

                {/* Card */}
                <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">

                    {/* ── VERIFICANDO ── */}
                    {estado === 'verificando' && (
                        <div className="p-8 text-center">
                            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-spinner fa-spin text-primary text-xl"></i>
                            </div>
                            <p className="text-sm text-muted-foreground">Verificando enlace de activación...</p>
                        </div>
                    )}

                    {/* ── TOKEN INVÁLIDO ── */}
                    {estado === 'token_invalido' && (
                        <div className="p-8 text-center">
                            <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-link-slash text-destructive text-xl"></i>
                            </div>
                            <h2 className="text-lg font-semibold text-foreground mb-2">Enlace inválido</h2>
                            <p className="text-sm text-muted-foreground mb-6">{errorToken}</p>
                            <p className="text-xs text-muted-foreground">
                                Solicita un nuevo enlace de activación a tu administrador.
                            </p>
                        </div>
                    )}

                    {/* ── FORMULARIO ── */}
                    {(estado === 'listo' || estado === 'enviando') && empleado && (
                        <>
                            {/* Header del form */}
                            <div className="px-6 py-5 border-b border-border bg-muted/30">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <i className="fa-solid fa-user text-primary"></i>
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                                            Activar cuenta
                                        </p>
                                        <p className="text-sm font-semibold text-foreground truncate">
                                            {empleado.nombre_completo}
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                            <span className="font-mono">{empleado.username}</span>
                                            {' · '}{empleado.puesto}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Cuerpo del form */}
                            <form onSubmit={handleSubmit} className="p-6 space-y-5">
                                <p className="text-sm text-muted-foreground">
                                    Define una contraseña segura para acceder al sistema.
                                </p>

                                {/* Password */}
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-lock mr-2"></i>
                                        Nueva contraseña
                                    </label>
                                    <div className="relative">
                                        <input
                                            type={mostrarPassword ? 'text' : 'password'}
                                            value={formData.password}
                                            onChange={(e) => handleInputChange('password', e.target.value)}
                                            className={`w-full px-4 py-2.5 pr-10 bg-background border rounded-lg text-sm 
                                                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary 
                                                transition-all ${errores.password ? 'border-destructive' : 'border-border'}`}
                                            placeholder="Mínimo 8 caracteres"
                                            disabled={estado === 'enviando'}
                                            autoComplete="new-password"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setMostrarPassword(!mostrarPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                            tabIndex={-1}
                                        >
                                            <i className={`fa-solid ${mostrarPassword ? 'fa-eye-slash' : 'fa-eye'} text-sm`}></i>
                                        </button>
                                    </div>
                                    {errores.password && (
                                        <p className="text-xs text-destructive mt-1.5">
                                            <i className="fa-solid fa-circle-exclamation mr-1"></i>
                                            {errores.password}
                                        </p>
                                    )}
                                </div>

                                {/* Confirmar password */}
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-lock mr-2"></i>
                                        Confirmar contraseña
                                    </label>
                                    <div className="relative">
                                        <input
                                            type={mostrarConfirmacion ? 'text' : 'password'}
                                            value={formData.password_confirmacion}
                                            onChange={(e) => handleInputChange('password_confirmacion', e.target.value)}
                                            className={`w-full px-4 py-2.5 pr-10 bg-background border rounded-lg text-sm 
                                                focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary 
                                                transition-all ${errores.password_confirmacion ? 'border-destructive' : 'border-border'}`}
                                            placeholder="Repite tu contraseña"
                                            disabled={estado === 'enviando'}
                                            autoComplete="new-password"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setMostrarConfirmacion(!mostrarConfirmacion)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                            tabIndex={-1}
                                        >
                                            <i className={`fa-solid ${mostrarConfirmacion ? 'fa-eye-slash' : 'fa-eye'} text-sm`}></i>
                                        </button>
                                    </div>
                                    {errores.password_confirmacion && (
                                        <p className="text-xs text-destructive mt-1.5">
                                            <i className="fa-solid fa-circle-exclamation mr-1"></i>
                                            {errores.password_confirmacion}
                                        </p>
                                    )}
                                </div>

                                {/* Indicador de coincidencia */}
                                {formData.password && formData.password_confirmacion && (
                                    <div className={`flex items-center gap-2 text-xs ${
                                        formData.password === formData.password_confirmacion
                                            ? 'text-green-600 dark:text-green-400'
                                            : 'text-destructive'
                                    }`}>
                                        <i className={`fa-solid ${
                                            formData.password === formData.password_confirmacion
                                                ? 'fa-circle-check'
                                                : 'fa-circle-xmark'
                                        }`}></i>
                                        {formData.password === formData.password_confirmacion
                                            ? 'Las contraseñas coinciden'
                                            : 'Las contraseñas no coinciden'}
                                    </div>
                                )}

                                {/* Submit */}
                                <button
                                    type="submit"
                                    disabled={estado === 'enviando'}
                                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary
                                        text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90
                                        transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm mt-2"
                                >
                                    {estado === 'enviando' ? (
                                        <>
                                            <i className="fa-solid fa-spinner fa-spin"></i>
                                            Activando cuenta...
                                        </>
                                    ) : (
                                        <>
                                            <i className="fa-solid fa-circle-check"></i>
                                            Activar mi cuenta
                                        </>
                                    )}
                                </button>
                            </form>
                        </>
                    )}

                    {/* ── ACTIVADO ── */}
                    {estado === 'activado' && (
                        <div className="p-8 text-center">
                            <div className="w-14 h-14 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-check text-green-500 text-3xl"></i>
                            </div>
                            <h2 className="text-lg font-semibold text-foreground mb-2">
                                ¡Cuenta activada!
                            </h2>
                            <p className="text-sm text-muted-foreground mb-4">
                                Tu cuenta está lista. Redirigiendo al sistema...
                            </p>
                            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                                <i className="fa-solid fa-spinner fa-spin"></i>
                                Ingresando automáticamente
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer */}
                <p className="text-center text-xs text-muted-foreground mt-6">
                    Klyra ERP · {new Date().getFullYear()}
                </p>
            </div>
        </div>
    )
}