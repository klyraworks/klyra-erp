"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Cliente, ClienteTipo, ClienteTipoIdentificacion } from "@/src/core/api/types"
import React from "react"

interface ClienteFormProps {
    mode: "create" | "edit"
    cliente?: Cliente | null
    formRef?: React.RefObject<HTMLFormElement>
}

interface PersonaData {
    nombre1: string
    nombre2: string
    apellido1: string
    apellido2: string
    email: string
    telefono: string
    fecha_nacimiento: string
    sexo: "M" | "F" | "O"
}

interface FormData {
    tipo: ClienteTipo
    tipo_identificacion: ClienteTipoIdentificacion
    identificacion: string
    razon_social: string
    limite_credito: string
    descuento_porcentaje: string
    email_facturacion: string
    telefono_facturacion: string
    direccion: string
    persona: PersonaData
}

const TIPOS_PERSONA: { value: ClienteTipo; label: string; icon: string }[] = [
    { value: "natural", label: "Persona Natural", icon: "fa-user" },
    { value: "juridica", label: "Persona Jurídica", icon: "fa-building" },
]

const TIPOS_IDENTIFICACION: { value: ClienteTipoIdentificacion; label: string }[] = [
    { value: "cedula", label: "Cédula" },
    { value: "ruc", label: "RUC" },
    { value: "pasaporte", label: "Pasaporte" },
    { value: "consumidor_final", label: "Consumidor Final" },
]

const INITIAL_FORM: FormData = {
    tipo: "natural",
    tipo_identificacion: "cedula",
    identificacion: "",
    razon_social: "",
    limite_credito: "0.00",
    descuento_porcentaje: "0.00",
    email_facturacion: "",
    telefono_facturacion: "",
    direccion: "",
    persona: {
        nombre1: "",
        nombre2: "",
        apellido1: "",
        apellido2: "",
        email: "",
        telefono: "",
        fecha_nacimiento: "",
        sexo: "O",
    },
}

export function ClienteForm({ mode, cliente, formRef }: ClienteFormProps) {
    const router = useRouter()
    const isEditMode = mode === "edit"

    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState<FormData>(INITIAL_FORM)

    useEffect(() => {
        if (isEditMode && cliente) {
            setFormData(prev => ({
                ...prev,
                tipo: cliente.tipo,
                tipo_identificacion: cliente.tipo_identificacion,
                identificacion: cliente.identificacion,
                razon_social: cliente.razon_social,
                limite_credito: cliente.limite_credito,
                descuento_porcentaje: cliente.descuento_porcentaje,
                email_facturacion: cliente.email_facturacion ?? "",
                telefono_facturacion: cliente.telefono_facturacion ?? "",
                direccion: cliente.direccion ?? "",
            }))
        }
    }, [isEditMode, cliente])

    // Si cambia a jurídica, forzar RUC
    useEffect(() => {
        if (formData.tipo === "juridica" && formData.tipo_identificacion !== "ruc") {
            setFormData(prev => ({ ...prev, tipo_identificacion: "ruc" }))
        }
    }, [formData.tipo])

    const handleInputChange = (field: keyof Omit<FormData, "persona">, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handlePersonaChange = (field: keyof PersonaData, value: string) => {
        setFormData(prev => ({ ...prev, persona: { ...prev.persona, [field]: value } }))
    }

    const validarFormulario = (): boolean => {
        if (!formData.razon_social.trim()) {
            alertas.warning("El nombre o razón social es obligatorio", "Campo requerido")
            return false
        }
        if (!formData.identificacion.trim() && formData.tipo_identificacion !== "consumidor_final") {
            alertas.warning("La identificación es obligatoria", "Campo requerido")
            return false
        }
        if (formData.tipo === "juridica" && formData.tipo_identificacion !== "ruc") {
            alertas.warning("Las personas jurídicas deben tener RUC", "Validación")
            return false
        }
        if (!isEditMode && esPersonaNatural && !esConsumidorFinal) {
            if (!formData.persona.nombre1.trim()) {
                alertas.warning("El primer nombre es obligatorio", "Campo requerido")
                return false
            }
            if (!formData.persona.apellido1.trim()) {
                alertas.warning("El primer apellido es obligatorio", "Campo requerido")
                return false
            }
        }
        return true
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (loading) return
        if (!validarFormulario()) return
        setLoading(true)
        try {
            const payload: Record<string, unknown> = {
                tipo: formData.tipo,
                tipo_identificacion: formData.tipo_identificacion,
                identificacion: formData.identificacion,
                razon_social: formData.razon_social,
                limite_credito: formData.limite_credito || "0.00",
                descuento_porcentaje: formData.descuento_porcentaje || "0.00",
                email_facturacion: formData.email_facturacion || null,
                telefono_facturacion: formData.telefono_facturacion || null,
                direccion: formData.direccion || null,
            }

            // En creación siempre persona_data
            if (!isEditMode) {
                const pd = formData.persona
                payload.persona_data = {
                    nombre1: pd.nombre1,
                    apellido1: pd.apellido1,
                    ...(pd.nombre2 && { nombre2: pd.nombre2 }),
                    ...(pd.apellido2 && { apellido2: pd.apellido2 }),
                    ...(pd.email && { email: pd.email }),
                    ...(pd.telefono && { telefono: pd.telefono }),
                    ...(pd.fecha_nacimiento && { fecha_nacimiento: pd.fecha_nacimiento }),
                    sexo: pd.sexo,
                    ...(formData.tipo_identificacion === "cedula" && formData.identificacion && {
                        cedula: formData.identificacion,
                    }),
                }
            }

            await apiFetch(
                isEditMode ? `/api/personas/clientes/${cliente?.id}/` : `/api/personas/clientes/`,
                {
                    method: isEditMode ? "PATCH" : "POST",
                    body: JSON.stringify(payload),
                }
            )

            alertas.success(
                isEditMode ? "Cliente actualizado exitosamente" : "Cliente creado exitosamente",
                isEditMode ? "Cliente Actualizado" : "Cliente Creado"
            )
            await mutate(["/api/personas/clientes/"])
            setTimeout(() => router.push("/ventas/clientes"), 1500)
        } catch (err) {
            if (err instanceof ApiError) {
                alertas.error(err.mensaje, err.titulo)
            } else {
                alertas.error(
                    "Error desconocido al guardar",
                    isEditMode ? "Error al Actualizar" : "Error al Crear"
                )
            }
        } finally {
            setLoading(false)
        }
    }

    const tiposIdDisponibles =
        formData.tipo === "juridica"
            ? TIPOS_IDENTIFICACION.filter(t => t.value === "ruc")
            : TIPOS_IDENTIFICACION.filter(t => t.value !== "ruc")

    const esPersonaNatural = formData.tipo === "natural"
    const esConsumidorFinal = formData.tipo_identificacion === "consumidor_final"

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* ── Columna principal ── */}
            <div className="lg:col-span-2 space-y-6">

                {/* Datos del cliente */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-user-tie text-primary"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">Datos del Cliente</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Información principal de identificación</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {/* Tipo de persona */}
                        <div>
                            <label className="block text-xs font-medium text-muted-foreground mb-2">
                                Tipo de persona <span className="text-destructive">*</span>
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                {TIPOS_PERSONA.map(t => (
                                    <button
                                        key={t.value}
                                        type="button"
                                        onClick={() => handleInputChange("tipo", t.value)}
                                        className={`flex items-center gap-2 px-4 py-2.5 border rounded-lg text-sm font-medium transition-all ${
                                            formData.tipo === t.value
                                                ? "border-primary bg-primary/5 text-primary"
                                                : "border-border text-foreground hover:bg-muted"
                                        }`}
                                    >
                                        <i className={`fa-solid ${t.icon} text-xs`}></i>
                                        {t.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Razón social */}
                        <div>
                            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                {formData.tipo === "juridica" ? "Razón social" : "Nombre completo"}{" "}
                                <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.razon_social}
                                onChange={e => handleInputChange("razon_social", e.target.value)}
                                placeholder={formData.tipo === "juridica" ? "Empresa S.A." : "Juan Pérez"}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        {/* Tipo identificación + Número */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    Tipo de identificación <span className="text-destructive">*</span>
                                </label>
                                <select
                                    value={formData.tipo_identificacion}
                                    onChange={e =>
                                        handleInputChange("tipo_identificacion", e.target.value as ClienteTipoIdentificacion)
                                    }
                                    disabled={formData.tipo === "juridica"}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                                >
                                    {tiposIdDisponibles.map(t => (
                                        <option key={t.value} value={t.value}>
                                            {t.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    Número de identificación
                                    {!esConsumidorFinal && <span className="text-destructive"> *</span>}
                                </label>
                                <input
                                    type="text"
                                    value={formData.identificacion}
                                    onChange={e => handleInputChange("identificacion", e.target.value)}
                                    disabled={esConsumidorFinal}
                                    placeholder={
                                        formData.tipo_identificacion === "ruc"
                                            ? "0000000000001"
                                            : formData.tipo_identificacion === "cedula"
                                            ? "0000000000"
                                            : esConsumidorFinal
                                            ? "9999999999999"
                                            : "Número"
                                    }
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Datos de persona — solo en creación, persona natural, no consumidor final */}
                {!isEditMode && esPersonaNatural && !esConsumidorFinal && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-id-card text-primary"></i>
                            </div>
                            <div>
                                <h2 className="text-sm font-semibold text-foreground">Datos Personales</h2>
                                <p className="text-xs text-muted-foreground mt-0.5">Información de la persona vinculada al cliente</p>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Primer nombre <span className="text-destructive">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.persona.nombre1}
                                        onChange={e => handlePersonaChange("nombre1", e.target.value)}
                                        placeholder="Carlos"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Segundo nombre
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.persona.nombre2}
                                        onChange={e => handlePersonaChange("nombre2", e.target.value)}
                                        placeholder="Andrés"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Primer apellido <span className="text-destructive">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.persona.apellido1}
                                        onChange={e => handlePersonaChange("apellido1", e.target.value)}
                                        placeholder="Mendoza"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Segundo apellido
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.persona.apellido2}
                                        onChange={e => handlePersonaChange("apellido2", e.target.value)}
                                        placeholder="Torres"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Sexo
                                    </label>
                                    <select
                                        value={formData.persona.sexo}
                                        onChange={e => handlePersonaChange("sexo", e.target.value)}
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    >
                                        <option value="O">No especificado</option>
                                        <option value="M">Masculino</option>
                                        <option value="F">Femenino</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                        Fecha de nacimiento
                                    </label>
                                    <input
                                        type="date"
                                        value={formData.persona.fecha_nacimiento}
                                        onChange={e => handlePersonaChange("fecha_nacimiento", e.target.value)}
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Contacto y dirección */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-address-book text-primary"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">Contacto y Facturación</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Datos de contacto para documentos fiscales</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    <i className="fa-solid fa-envelope mr-1.5"></i>Email de facturación
                                </label>
                                <input
                                    type="email"
                                    value={formData.email_facturacion}
                                    onChange={e => handleInputChange("email_facturacion", e.target.value)}
                                    placeholder="correo@empresa.com"
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                    <i className="fa-solid fa-phone mr-1.5"></i>Teléfono
                                </label>
                                <input
                                    type="tel"
                                    value={formData.telefono_facturacion}
                                    onChange={e => handleInputChange("telefono_facturacion", e.target.value)}
                                    placeholder="0991234567"
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                <i className="fa-solid fa-location-dot mr-1.5"></i>Dirección
                            </label>
                            <textarea
                                value={formData.direccion}
                                onChange={e => handleInputChange("direccion", e.target.value)}
                                placeholder="Av. Principal 123, Ciudad"
                                rows={3}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                            />
                        </div>
                    </div>
                </div>

                {/* Información de solo lectura — modo edición */}
                {isEditMode && cliente && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-circle-info text-muted-foreground text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                                Información
                            </h2>
                        </div>
                        <div className="space-y-1">
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-barcode"></i>Código
                                </span>
                                <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                    {cliente.codigo}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-toggle-on"></i>Estado
                                </span>
                                <span
                                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                                        cliente.is_active
                                            ? "bg-emerald-500/10 text-emerald-600"
                                            : "bg-destructive/10 text-destructive"
                                    }`}
                                >
                                    <i className={`fa-solid ${cliente.is_active ? "fa-circle-check" : "fa-ban"} text-[9px]`}></i>
                                    {cliente.is_active ? "Activo" : "Inactivo"}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-calendar"></i>Creado
                                </span>
                                <span className="text-xs font-medium text-foreground">
                                    {new Date(cliente.created_at).toLocaleDateString("es-EC", {
                                        day: "2-digit",
                                        month: "short",
                                        year: "numeric",
                                    })}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Columna lateral ── */}
            <div className="space-y-6">
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-handshake text-primary"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">Condiciones</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Crédito y descuentos</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                <i className="fa-solid fa-credit-card mr-1.5"></i>Límite de crédito
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground font-medium">$</span>
                                <input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={formData.limite_credito}
                                    onChange={e => handleInputChange("limite_credito", e.target.value)}
                                    className="w-full pl-7 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                                <i className="fa-solid fa-percent mr-1.5"></i>Descuento
                            </label>
                            <div className="relative">
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="0.01"
                                    value={formData.descuento_porcentaje}
                                    onChange={e => handleInputChange("descuento_porcentaje", e.target.value)}
                                    className="w-full px-4 pr-8 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground font-medium">%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                    <div className="flex gap-3">
                        <i className="fa-solid fa-circle-info text-blue-500 mt-0.5 text-sm flex-shrink-0"></i>
                        <div>
                            <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-1">
                                Gestión de crédito
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-500 leading-relaxed">
                                El saldo disponible se calcula automáticamente al registrar ventas a crédito y pagos.
                            </p>
                        </div>
                    </div>
                </div>

                {formData.tipo === "juridica" && (
                    <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
                        <div className="flex gap-3">
                            <i className="fa-solid fa-triangle-exclamation text-yellow-500 mt-0.5 text-sm flex-shrink-0"></i>
                            <div>
                                <p className="text-xs font-semibold text-yellow-700 dark:text-yellow-400 mb-1">
                                    Persona Jurídica
                                </p>
                                <p className="text-xs text-yellow-600 dark:text-yellow-500 leading-relaxed">
                                    Las personas jurídicas deben usar RUC como identificación (13 dígitos).
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </form>
    )
}