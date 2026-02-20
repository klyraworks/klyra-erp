// src/core/auth/login-form.tsx

"use client"

import type React from "react"
import {useState} from "react"
import {login} from "@/src/core/api/client"
import {useRouter} from "next/navigation"
import {useTheme} from "@/src/core/theme/provider"
import { useStore } from "@/src/core/store"

export function LoginForm() {
    const router = useRouter()
    const {setAuth} = useStore()
    const {theme, toggleTheme} = useTheme()
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")
    const [showPassword, setShowPassword] = useState(false)
    const [rememberMe, setRememberMe] = useState(false) // ← AGREGAR ESTA LÍNEA

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        try {
            const result = await login(username, password)
            setAuth(result.user, result.empleado, result.empresa)

            console.log('Login exitoso:', result.empresa)
            router.push('/dashboard')
        } catch (err) {
            setError((err as Error).message || "Error al iniciar sesión")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-background flex">
            {/* Left Side - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-primary relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div
                        className="absolute top-20 left-20 w-72 h-72 border border-primary-foreground rounded-full"></div>
                    <div
                        className="absolute bottom-40 right-10 w-96 h-96 border border-primary-foreground rounded-full"></div>
                    <div
                        className="absolute top-1/2 left-1/3 w-48 h-48 border border-primary-foreground rounded-full"></div>
                </div>

                <div className="relative z-10 flex flex-col justify-between p-12 w-full">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-primary-foreground rounded-xl flex items-center justify-center">
                            <span className="text-2xl font-bold text-primary">K</span>
                        </div>
                        <span className="text-2xl font-bold text-primary-foreground">Klyra</span>
                    </div>

                    {/* Main Content */}
                    <div className="max-w-md">
                        <h1 className="text-4xl font-bold text-primary-foreground mb-6 leading-tight">
                            Sistema de Gestión Empresarial
                        </h1>
                        <p className="text-primary-foreground/80 text-lg mb-8">
                            Administra tu negocio de forma eficiente con nuestro ERP completo. Ventas, inventario,
                            finanzas y más en
                            un solo lugar.
                        </p>

                        {/* Features */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 text-primary-foreground/90">
                                <div
                                    className="w-10 h-10 rounded-lg bg-primary-foreground/20 flex items-center justify-center">
                                    <i className="fa-solid fa-chart-line"></i>
                                </div>
                                <span>Reportes y analíticas en tiempo real</span>
                            </div>
                            <div className="flex items-center gap-3 text-primary-foreground/90">
                                <div
                                    className="w-10 h-10 rounded-lg bg-primary-foreground/20 flex items-center justify-center">
                                    <i className="fa-solid fa-file-invoice-dollar"></i>
                                </div>
                                <span>Facturación electrónica SRI Ecuador</span>
                            </div>
                            <div className="flex items-center gap-3 text-primary-foreground/90">
                                <div
                                    className="w-10 h-10 rounded-lg bg-primary-foreground/20 flex items-center justify-center">
                                    <i className="fa-solid fa-warehouse"></i>
                                </div>
                                <span>Control de inventario multi-bodega</span>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="text-primary-foreground/60 text-sm">
                        <p>Klyra ERP v1.0</p>
                        <p>Desarrollado en Ecuador</p>
                    </div>
                </div>
            </div>

            {/* Right Side - Login Form */}
            <div className="w-full lg:w-1/2 flex flex-col">
                {/* Top Bar */}
                <div className="flex justify-between items-center p-6">
                    <div className="lg:hidden flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                            <span className="text-lg font-bold text-primary-foreground">K</span>
                        </div>
                        <span className="text-xl font-bold text-foreground">Klyra</span>
                    </div>

                    <button
                        onClick={toggleTheme}
                        className="ml-auto p-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                        title={theme === "dark" ? "Modo claro" : "Modo oscuro"}
                    >
                        <i className={`fa-solid ${theme === "dark" ? "fa-sun" : "fa-moon"} text-lg`}></i>
                    </button>
                </div>

                {/* Form Container */}
                <div className="flex-1 flex items-center justify-center p-6">
                    <div className="w-full max-w-md">
                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-foreground mb-2">Bienvenido de nuevo</h2>
                            <p className="text-muted-foreground">Ingresa tus credenciales para acceder al sistema</p>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div
                                className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive text-sm flex items-start gap-3">
                                <i className="fa-solid fa-circle-exclamation mt-0.5"></i>
                                <div>
                                    <p className="font-medium">Error de autenticación</p>
                                    <p className="text-destructive/80">{error}</p>
                                </div>
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Username Field */}
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                    <i className="fa-solid fa-user mr-2 text-muted-foreground"></i>
                                    Usuario
                                </label>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="Ingresa tu nombre de usuario"
                                    className="w-full px-4 py-3 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all placeholder:text-muted-foreground/60"
                                    required
                                    autoComplete="username"
                                />
                            </div>

                            {/* Password Field */}
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                    <i className="fa-solid fa-lock mr-2 text-muted-foreground"></i>
                                    Contraseña
                                </label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Ingresa tu contraseña"
                                        className="w-full px-4 py-3 pr-12 bg-muted border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all placeholder:text-muted-foreground/60"
                                        required
                                        autoComplete="current-password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        <i className={`fa-solid ${showPassword ? "fa-eye-slash" : "fa-eye"}`}></i>
                                    </button>
                                </div>
                            </div>

                            {/* Remember Me & Forgot Password */}
                            <div className="flex items-center justify-between">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={rememberMe}
                                        onChange={(e) => setRememberMe(e.target.checked)}
                                        className="w-4 h-4 rounded border-border text-primary focus:ring-2 focus:ring-primary/30"
                                    />
                                    <span className="text-sm text-muted-foreground">Recordarme</span>
                                </label>
                                <button type="button" className="text-sm text-primary hover:underline font-medium">
                                    Olvidé mi contraseña
                                </button>
                            </div>

                            {/* Submit Button */}
                            <button
                                type="submit"
                                disabled={loading || !username || !password}
                                className="w-full py-3.5 bg-primary text-primary-foreground rounded-xl text-sm font-semibold hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
                            >
                                {loading ? (
                                    <>
                                        <i className="fa-solid fa-circle-notch fa-spin"></i>
                                        Verificando...
                                    </>
                                ) : (
                                    <>
                                        Iniciar Sesión
                                        <i className="fa-solid fa-arrow-right"></i>
                                    </>
                                )}
                            </button>
                        </form>

                        {/* Help Section */}
                        <div className="mt-8 p-4 bg-muted rounded-xl">
                            <p className="text-sm text-muted-foreground text-center">
                                <i className="fa-solid fa-circle-info mr-2"></i>
                                ¿Necesitas ayuda? Contacta al administrador del sistema
                            </p>
                        </div>
                    </div>
                </div>

                {/* Bottom Footer */}
                <div className="p-6 text-center text-sm text-muted-foreground">
                    <p>2024 Klyra ERP. Todos los derechos reservados.</p>
                </div>
            </div>
        </div>
    )
}
