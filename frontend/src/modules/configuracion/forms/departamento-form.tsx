// frontend/src/modules/configuracion/forms/departamento-form.tsx
"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Departamento, EmpleadoListItem, BuscarResponse } from "@/src/core/api/types"
import { Select } from "@/components/select/select-klyra"
import React from "react"

interface DepartamentoFormProps {
    mode: "create" | "edit"
    departamento?: Departamento | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function DepartamentoForm({ mode, departamento, formRef }: DepartamentoFormProps) {
    console.log(departamento, "departamento form")
    const router = useRouter()
    const isEditMode = mode === "edit"

    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        nombre: "",
        descripcion: "",
        jefe_id: null as string | null,
    })

    const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([])
    const [empleadoInicial, setEmpleadoInicial] = useState<EmpleadoListItem | null>(null)
    const [loadingEmpleados, setLoadingEmpleados] = useState(false)

    useEffect(() => {
        if (isEditMode && departamento) {
            setFormData({
                nombre: departamento.nombre ?? "",
                descripcion: departamento.descripcion ?? "",
                jefe_id: departamento.jefe?.id ?? null,
            })
        }
    }, [isEditMode, departamento])

    useEffect(() => {
        async function loadEmpleadoInicial() {
            if (!isEditMode || !departamento?.jefe?.id) return
            try {
                const data = await apiFetch<BuscarResponse<EmpleadoListItem>>(
                    `/api/seguridad/empleados/buscar/?q=${encodeURIComponent(departamento.jefe.id)}`
                )
                const empleado = data.results[0] ?? null
                setEmpleadoInicial(empleado)
                setEmpleados(empleado ? [empleado] : [])
            } catch (err) {
                console.warn("Error cargando empleado inicial:", err)
            }
        }
        loadEmpleadoInicial()
    }, [isEditMode, departamento])

    const handleInputChange = (field: string, value: unknown) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const buscarEmpleados = async (query: string) => {
        if (query.trim() === "") {
            setEmpleados(empleadoInicial ? [empleadoInicial] : [])
            return
        }
        setLoadingEmpleados(true)
        try {
            const data = await apiFetch<BuscarResponse<EmpleadoListItem>>(
                `/api/seguridad/empleados/buscar/?q=${encodeURIComponent(query)}`
            )
            setEmpleados(data.results)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error al buscar empleados", "Error")
        } finally {
            setLoadingEmpleados(false)
        }
    }

    const validarFormulario = (): boolean => {
        if (!formData.nombre.trim()) {
            alertas.warning("El nombre del departamento es requerido", "Campo requerido")
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
                jefe_id: formData.jefe_id,
            }
            await apiFetch(
                isEditMode ? `/api/rrhh/departamentos/${departamento?.id}/` : `/api/rrhh/departamentos/`,
                { method: isEditMode ? "PATCH" : "POST", body: JSON.stringify(payload) }
            )
            alertas.success(
                isEditMode ? "Departamento actualizado exitosamente" : "Departamento creado exitosamente",
                isEditMode ? "Departamento Actualizado" : "Departamento Creado"
            )
            await mutate(["/api/rrhh/departamentos/"])
            setTimeout(() => router.push("/configuracion/departamentos"), 1500)
        } catch (err) {
            if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
            else alertas.error("Error desconocido al guardar", isEditMode ? "Error al Actualizar" : "Error al Crear")
        } finally {
            setLoading(false)
        }
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 gap-6">
            {/* Columna principal */}
            <div className="lg:col-span-2 space-y-6">
                {/* Alerta informativa */}
                {!isEditMode && (
                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                        <div className="flex gap-3">
                            <i className="fa-solid fa-circle-info text-blue-500 text-sm mt-0.5 flex-shrink-0"></i>
                            <div>
                                <p className="text-xs font-medium text-blue-700 dark:text-blue-300">Código automático</p>
                                <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                                    El código del departamento se generará automáticamente al crear el registro.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-building text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">
                            {isEditMode ? "Editar Departamento" : "Nuevo Departamento"}
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 gap-5">
                        {/* Nombre */}
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Nombre <span className="text-destructive">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange("nombre", e.target.value)}
                                placeholder="Ej: Tecnología"
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            />
                        </div>

                        {/* Descripción */}
                        <div className="flex flex-col gap-1.5">
                            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                Descripción
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange("descripcion", e.target.value)}
                                placeholder="Descripción opcional del departamento..."
                                rows={3}
                                className="px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                            />
                        </div>
                    </div>
                </div>

                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-user-tie text-primary text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-foreground">Jefe de Departamento</h2>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Empleado
                        </label>
                        <Select
                            options={empleados.map(e => ({
                                value: e.id,
                                label: e.nombre_completo,
                                description: e.codigo,
                                icon: "fas fa-user"
                            }))}
                            value={formData.jefe_id || ""}
                            onChange={(value) => handleInputChange("jefe_id", value || null)}
                            onSearch={buscarEmpleados}
                            searchable
                            placeholder="Buscar empleado..."
                            loading={loadingEmpleados}
                            className="w-full"
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                            Opcional. Debe ser un empleado activo de la empresa.
                        </p>
                    </div>
                </div>

                {/* Información de solo lectura — modo edición */}
                {isEditMode && departamento && (
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
                                    {departamento.codigo}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-users"></i>Empleados activos
                                </span>
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-muted/60 text-foreground">
                                    {departamento.total_empleados}
                                </span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-circle-dot"></i>Estado
                                </span>
                                {departamento.is_active ? (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                        <i className="fa-solid fa-circle-check text-[9px]"></i>Activo
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                                        <i className="fa-solid fa-ban text-[9px]"></i>Inactivo
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center justify-between py-2">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-calendar"></i>Creado
                                </span>
                                <span className="text-xs font-medium text-foreground">
                                    {departamento.created_at ? new Date(departamento.created_at).toLocaleDateString("es-EC", {
                                        day: "2-digit", month: "short", year: "numeric"
                                    }) : "Sin fecha"}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </form>
    )
}