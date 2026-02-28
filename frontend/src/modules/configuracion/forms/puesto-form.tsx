// frontend/src/modules/configuracion/forms/departamento-form.tsx
"use client"

import { useState, useEffect } from "react"
import React from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Puesto, Departamento, BuscarResponse } from "@/src/core/api/types"
import { Select } from "@/components/select/select-klyra"

interface PuestoFormProps {
    mode: "create" | "edit"
    puesto?: Puesto | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function PuestoForm({ mode, puesto, formRef }: PuestoFormProps) {
    const router = useRouter()
    const isEditMode = mode === "edit"

    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        nombre: "",
        descripcion: "",
        departamento_id: null as string | null,
        salario_minimo: "",
        salario_maximo: "",
    })

    const [departamentos, setDepartamentos] = useState<Departamento[]>([])
    const [departamentoInicial, setDepartamentoInicial] = useState<Departamento | null>(null)
    const [loadingDepartamentos, setLoadingDepartamentos] = useState(false)

    useEffect(() => {
        if (isEditMode && puesto) {
            setFormData({
                nombre:         puesto.nombre ?? "",
                descripcion:    puesto.descripcion ?? "",
                departamento_id: puesto.departamento?.id ?? null,
                salario_minimo: puesto.salario_minimo ? String(puesto.salario_minimo) : "",
                salario_maximo: puesto.salario_maximo ? String(puesto.salario_maximo) : "",
            })
        }
    }, [isEditMode, puesto])

    useEffect(() => {
        async function loadDepartamentoInicial() {
            if (!isEditMode || !puesto?.departamento?.id) return
            try {
                const data = await apiFetch<BuscarResponse<Departamento>>(
                    `/api/rrhh/departamentos/buscar/?q=${encodeURIComponent(puesto.departamento.id)}`
                )
                const dep = data.results[0] ?? null
                setDepartamentoInicial(dep)
                setDepartamentos(dep ? [dep] : [])
            } catch (err) {
                console.warn("Error cargando departamento inicial:", err)
            }
        }
        loadDepartamentoInicial()
    }, [isEditMode, puesto])

    const buscarDepartamentos = async (query: string) => {
        if (query.trim() === "") {
            setDepartamentos(departamentoInicial ? [departamentoInicial] : [])
            return
        }
        setLoadingDepartamentos(true)
        try {
            const data = await apiFetch<BuscarResponse<Departamento>>(
                `/api/rrhh/departamentos/buscar/?q=${encodeURIComponent(query)}`
            )
            setDepartamentos(data.results)
        } catch (err) {
            console.log(err)
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar departamentos", "Error")
        } finally {
            setLoadingDepartamentos(false)
        }
    }

    const handleInputChange = (field: string, value: unknown) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const validarFormulario = (): boolean => {
        if (!formData.nombre.trim()) {
            alertas.warning("El nombre del puesto es requerido", "Campo requerido")
            return false
        }
        if (!isEditMode && !formData.departamento_id) {
            alertas.warning("El departamento es requerido", "Campo requerido")
            return false
        }
        if (formData.salario_minimo && formData.salario_maximo) {
            if (parseFloat(formData.salario_maximo) < parseFloat(formData.salario_minimo)) {
                alertas.warning("El salario máximo debe ser mayor o igual al mínimo", "Validación")
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
                nombre:      formData.nombre.trim(),
                descripcion: formData.descripcion.trim() || "",
                salario_minimo: formData.salario_minimo ? parseFloat(formData.salario_minimo) : null,
                salario_maximo: formData.salario_maximo ? parseFloat(formData.salario_maximo) : null,
            }
            if (!isEditMode) {
                payload.departamento_id = formData.departamento_id
            } else if (formData.departamento_id !== (puesto?.departamento?.id ?? null)) {
                payload.departamento_id = formData.departamento_id
            }

            await apiFetch(
                isEditMode ? `/api/rrhh/puestos/${puesto?.id}/` : `/api/rrhh/puestos/`,
                { method: isEditMode ? "PATCH" : "POST", body: JSON.stringify(payload) }
            )
            alertas.success(
                isEditMode ? "Puesto actualizado exitosamente" : "Puesto creado exitosamente",
                isEditMode ? "Puesto Actualizado" : "Puesto Creado"
            )
            await mutate(["/api/rrhh/puestos/"])
            setTimeout(() => router.push("/configuracion/puestos"), 1500)
        } catch (err) {
            console.log("Error:", err)
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
                            <i className="fa-solid fa-briefcase text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">
                            {isEditMode ? "Editar Puesto" : "Nuevo Puesto"}
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Nombre <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange("nombre", e.target.value)}
                                placeholder="Ej: Desarrollador Backend"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Descripción
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange("descripcion", e.target.value)}
                                placeholder="Descripción del cargo..."
                                rows={3}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                            />
                        </div>
                    </div>
                </div>

                {/* Rango salarial */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-dollar-sign text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">Rango Salarial</h2>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Salario mínimo
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">$</span>
                                <input
                                    type="number"
                                    value={formData.salario_minimo}
                                    onChange={(e) => handleInputChange("salario_minimo", e.target.value)}
                                    placeholder="0.00"
                                    min="0"
                                    step="0.01"
                                    className="pl-7 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Salario máximo
                            </label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm pointer-events-none">$</span>
                                <input
                                    type="number"
                                    value={formData.salario_maximo}
                                    onChange={(e) => handleInputChange("salario_maximo", e.target.value)}
                                    placeholder="0.00"
                                    min="0"
                                    step="0.01"
                                    className="pl-7 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="mt-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <div className="flex gap-2">
                            <i className="fa-solid fa-circle-info text-blue-500 text-xs mt-0.5 flex-shrink-0"></i>
                            <p className="text-xs text-blue-600 dark:text-blue-400">
                                El rango salarial es solo referencial para nuevas contrataciones. No afecta los salarios de empleados existentes.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Información de solo lectura — modo edición */}
                {isEditMode && puesto && (
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
                                    {puesto.codigo}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-users"></i>Empleados activos
                                </span>
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted/60 text-foreground">
                                    {puesto.total_empleados}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-calendar"></i>Creado
                                </span>
                                <span className="text-xs font-medium text-foreground">
                                    {new Date(puesto.created_at).toLocaleDateString("es-EC", {
                                        day: "2-digit", month: "short", year: "numeric"
                                    })}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Columna lateral */}
            <div className="space-y-6">
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-building text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">Departamento</h2>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Departamento {!isEditMode && <span className="text-destructive">*</span>}
                        </label>
                        <Select
                            options={departamentos.map(d => ({
                                value: d.id,
                                label: d.nombre,
                                description: d.codigo,
                                icon: "fas fa-building"
                            }))}
                            value={formData.departamento_id || ""}
                            onChange={(value) => handleInputChange("departamento_id", value || null)}
                            onSearch={buscarDepartamentos}
                            searchable
                            placeholder="Buscar departamento..."
                            loading={loadingDepartamentos}
                            className="w-full"
                        />
                        {!isEditMode && (
                            <p className="text-xs text-muted-foreground mt-1">
                                Requerido. El departamento no podrá cambiarse una vez asignado empleados.
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </form>
    )
}