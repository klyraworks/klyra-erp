"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Rol, GrupoDjango } from "@/src/core/api/types"
import { CheckboxKlyra } from "@/components/ui/checkbox-klyra"
import React from "react"

interface RolFormProps {
    mode: "create" | "edit"
    rol?: Rol | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function RolForm({ mode, rol, formRef }: RolFormProps) {
    const router = useRouter()
    const isEditMode = mode === "edit"

    const [loading, setLoading] = useState(false)

    const [formData, setFormData] = useState({
        nombre: "",
        descripcion: "",
        nivel_jerarquico: 1,
        monto_maximo_descuento: "",
        monto_maximo_aprobacion: "",
        limite_credito_clientes: "",
        puede_aprobar_vacaciones: false,
        puede_ver_salarios: false,
        puede_modificar_precios: false,
        puede_anular_documentos: false,
    })

    const [gruposDisponibles, setGruposDisponibles] = useState<GrupoDjango[]>([])
    const [gruposSeleccionados, setGruposSeleccionados] = useState<number[]>([])
    const [loadingGrupos, setLoadingGrupos] = useState(false)
    const [busquedaGrupos, setBusquedaGrupos] = useState("")

    useEffect(() => {
        if (isEditMode && rol) {
            setFormData({
                nombre: rol.nombre ?? "",
                descripcion: rol.descripcion ?? "",
                nivel_jerarquico: rol.nivel_jerarquico ?? 1,
                monto_maximo_descuento: rol.monto_maximo_descuento ? String(rol.monto_maximo_descuento) : "",
                monto_maximo_aprobacion: rol.monto_maximo_aprobacion ? String(rol.monto_maximo_aprobacion) : "",
                limite_credito_clientes: rol.limite_credito_clientes ? String(rol.limite_credito_clientes) : "",
                puede_aprobar_vacaciones: rol.puede_aprobar_vacaciones ?? false,
                puede_ver_salarios: rol.puede_ver_salarios ?? false,
                puede_modificar_precios: rol.puede_modificar_precios ?? false,
                puede_anular_documentos: rol.puede_anular_documentos ?? false,
            })
            setGruposSeleccionados(rol.grupos_django?.map(g => g.id) ?? [])
        }
    }, [isEditMode, rol])

    useEffect(() => {
        async function loadGrupos() {
            setLoadingGrupos(true)
            try {
                const data = await apiFetch<{ data: { grupos: GrupoDjango[], total: number } }>(
                    "/api/roles/grupos-disponibles/"
                )
                setGruposDisponibles(data.data.grupos)
            } catch (err) {
                console.warn("Error cargando grupos disponibles:", err)
            } finally {
                setLoadingGrupos(false)
            }
        }
        loadGrupos()
    }, [])

    const handleInputChange = (field: string, value: unknown) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const toggleGrupo = (id: number) => {
        setGruposSeleccionados(prev =>
            prev.includes(id) ? prev.filter(g => g !== id) : [...prev, id]
        )
    }

    const gruposFiltrados = gruposDisponibles.filter(g =>
        g.nombre.toLowerCase().includes(busquedaGrupos.toLowerCase())
    )

    const validarFormulario = (): boolean => {
        if (!formData.nombre.trim()) {
            alertas.warning("El nombre del rol es requerido", "Campo requerido")
            return false
        }
        if (formData.nivel_jerarquico < 1 || formData.nivel_jerarquico > 10) {
            alertas.warning("El nivel jerárquico debe estar entre 1 y 10", "Validación")
            return false
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
                nombre: formData.nombre.trim(),
                descripcion: formData.descripcion.trim() || "",
                nivel_jerarquico: formData.nivel_jerarquico,
                grupos_django_ids: gruposSeleccionados,
                monto_maximo_descuento: formData.monto_maximo_descuento ? parseFloat(formData.monto_maximo_descuento) : null,
                monto_maximo_aprobacion: formData.monto_maximo_aprobacion ? parseFloat(formData.monto_maximo_aprobacion) : null,
                limite_credito_clientes: formData.limite_credito_clientes ? parseFloat(formData.limite_credito_clientes) : null,
                puede_aprobar_vacaciones: formData.puede_aprobar_vacaciones,
                puede_ver_salarios: formData.puede_ver_salarios,
                puede_modificar_precios: formData.puede_modificar_precios,
                puede_anular_documentos: formData.puede_anular_documentos,
            }

            await apiFetch(
                isEditMode ? `/api/roles/${rol?.id}/` : `/api/roles/`,
                { method: isEditMode ? "PATCH" : "POST", body: JSON.stringify(payload) }
            )
            alertas.success(
                isEditMode ? "Rol actualizado exitosamente" : "Rol creado exitosamente",
                isEditMode ? "Rol Actualizado" : "Rol Creado"
            )
            await mutate(["/api/roles/"])
            setTimeout(() => router.push("/seguridad/roles"), 1500)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error desconocido al guardar", isEditMode ? "Error al Actualizar" : "Error al Crear")
        } finally {
            setLoading(false)
        }
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Columna principal */}
            <div className="lg:col-span-2 space-y-6">

                {/* Información general */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-shield-halved text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">
                            {isEditMode ? "Editar Rol" : "Nuevo Rol"}
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Nombre <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange("nombre", e.target.value)}
                                placeholder="Ej: Supervisor de Ventas"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5 sm:col-span-2">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Descripción
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange("descripcion", e.target.value)}
                                placeholder="Descripción del rol..."
                                rows={2}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Nivel jerárquico <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="number"
                                value={formData.nivel_jerarquico}
                                onChange={(e) => handleInputChange("nivel_jerarquico", parseInt(e.target.value) || 1)}
                                min={1}
                                max={10}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                            <p className="text-xs text-muted-foreground">Del 1 al 10. Mayor número = mayor jerarquía.</p>
                        </div>
                    </div>
                </div>

                {/* Permisos de negocio */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-sliders text-primary text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">Permisos de Negocio</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Capacidades operativas del rol en el ERP</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Descuento máximo (%)
                            </label>
                            <div className="relative">
                                <input
                                    type="number"
                                    value={formData.monto_maximo_descuento}
                                    onChange={(e) => handleInputChange("monto_maximo_descuento", e.target.value)}
                                    placeholder="0.00"
                                    min="0"
                                    max="100"
                                    step="0.01"
                                    className="px-4 py-2.5 pr-8 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs pointer-events-none">%</span>
                            </div>
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Monto máximo de aprobación
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">$</span>
                                <input
                                    type="number"
                                    value={formData.monto_maximo_aprobacion}
                                    onChange={(e) => handleInputChange("monto_maximo_aprobacion", e.target.value)}
                                    placeholder="0.00"
                                    min="0"
                                    step="0.01"
                                    className="pl-7 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Límite de crédito a clientes
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">$</span>
                                <input
                                    type="number"
                                    value={formData.limite_credito_clientes}
                                    onChange={(e) => handleInputChange("limite_credito_clientes", e.target.value)}
                                    placeholder="0.00"
                                    min="0"
                                    step="0.01"
                                    className="pl-7 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5 pt-5 border-t border-border">
                        <CheckboxKlyra
                            checked={formData.puede_aprobar_vacaciones}
                            onChange={(v) => handleInputChange("puede_aprobar_vacaciones", v)}
                            label="Aprobar vacaciones"
                            className="w-full justify-start"
                        />
                        <CheckboxKlyra
                            checked={formData.puede_ver_salarios}
                            onChange={(v) => handleInputChange("puede_ver_salarios", v)}
                            label="Ver salarios"
                            className="w-full justify-start"
                        />
                        <CheckboxKlyra
                            checked={formData.puede_modificar_precios}
                            onChange={(v) => handleInputChange("puede_modificar_precios", v)}
                            label="Modificar precios"
                            className="w-full justify-start"
                        />
                        <CheckboxKlyra
                            checked={formData.puede_anular_documentos}
                            onChange={(v) => handleInputChange("puede_anular_documentos", v)}
                            label="Anular documentos"
                            className="w-full justify-start"
                        />
                    </div>
                </div>

                {/* Información de solo lectura — modo edición */}
                {isEditMode && rol && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-circle-info text-muted-foreground text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información</h2>
                        </div>
                        <div className="space-y-1">
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-barcode"></i>Código
                                </span>
                                <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">
                                    {rol.codigo}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-users"></i>Empleados activos
                                </span>
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted/60 text-foreground">
                                    {rol.total_empleados}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-calendar"></i>Creado
                                </span>
                                <span className="text-xs font-medium text-foreground">
                                    {new Date(rol.created_at).toLocaleDateString("es-EC", {
                                        day: "2-digit", month: "short", year: "numeric"
                                    })}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Columna lateral — Grupos Django */}
            <div className="space-y-6">
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-cubes text-primary text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">Grupos de Permisos</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {gruposSeleccionados.length} seleccionado{gruposSeleccionados.length !== 1 ? "s" : ""}
                            </p>
                        </div>
                    </div>

                    {/* Buscador */}
                    <div className="relative mb-3">
                        <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs pointer-events-none"></i>
                        <input
                            type="text"
                            value={busquedaGrupos}
                            onChange={(e) => setBusquedaGrupos(e.target.value)}
                            placeholder="Filtrar grupos..."
                            className="pl-8 pr-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                        />
                    </div>

                    {loadingGrupos ? (
                        <div className="space-y-2">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-10 bg-muted/40 animate-pulse rounded-lg"></div>
                            ))}
                        </div>
                    ) : gruposFiltrados.length === 0 ? (
                        <div className="py-8 text-center">
                            <i className="fa-solid fa-inbox text-2xl text-muted-foreground/40 mb-2"></i>
                            <p className="text-xs text-muted-foreground">Sin grupos disponibles</p>
                        </div>
                    ) : (
                        <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
                            {gruposFiltrados.map((grupo) => {
                                const seleccionado = gruposSeleccionados.includes(grupo.id)
                                return (
                                    <button
                                        key={grupo.id}
                                        type="button"
                                        onClick={() => toggleGrupo(grupo.id)}
                                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-all ${
                                            seleccionado
                                                ? "border-primary/40 bg-primary/5"
                                                : "border-border hover:bg-muted/40"
                                        }`}
                                    >
                                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                                            seleccionado
                                                ? "border-primary bg-primary"
                                                : "border-muted-foreground/40"
                                        }`}>
                                            {seleccionado && (
                                                <i className="fa-solid fa-check text-primary-foreground text-[8px]"></i>
                                            )}
                                        </div>
                                        <div className="flex flex-col flex-1 min-w-0">
                                            <span className={`text-xs font-medium truncate ${seleccionado ? "text-primary" : "text-foreground"}`}>
                                                {grupo.nombre}
                                            </span>
                                            <span className="text-xs text-muted-foreground mt-0.5">
                                                {grupo.permisos?.length ?? 0} permiso{(grupo.permisos?.length ?? 0) !== 1 ? "s" : ""}
                                            </span>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    )}

                    {gruposSeleccionados.length > 0 && (
                        <button
                            type="button"
                            onClick={() => setGruposSeleccionados([])}
                            className="mt-3 w-full text-xs text-muted-foreground hover:text-destructive transition-colors py-1"
                        >
                            <i className="fa-solid fa-xmark mr-1"></i>
                            Limpiar selección
                        </button>
                    )}
                </div>

                {/* Alerta informativa */}
                <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                    <div className="flex gap-3">
                        <i className="fa-solid fa-circle-info text-blue-500 text-sm mt-0.5 flex-shrink-0"></i>
                        <div>
                            <p className="text-xs font-medium text-blue-700 dark:text-blue-300">Sincronización inmediata</p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                                Los cambios en grupos se aplican de inmediato a todos los empleados con este rol, sin necesidad de re-login.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </form>
    )
}