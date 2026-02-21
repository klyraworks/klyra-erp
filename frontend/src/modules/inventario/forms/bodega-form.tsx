// frontend/src/modules/inventario/forms/bodega-form.tsx
"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { mutate } from "swr"
import { Select } from "@/components/select/select-klyra"
import { alertas } from "@/components/alerts/alertas-toast"
import { CheckboxKlyra } from "@/components/ui/checkbox-klyra"
import { Bodega, EmpleadoListItem, BuscarResponse } from "@/src/core/api/types"
import { useCiudades } from "@/src/core/store"
import { apiFetch, ApiError } from "@/src/core/api/client"
import React from "react"

interface BodegaFormProps {
    mode: 'create' | 'edit'
    bodega?: Bodega | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function BodegaForm({ mode, bodega, formRef }: BodegaFormProps) {
    const router = useRouter()
    const isEditMode = mode === 'edit'

    const { data: ciudades } = useCiudades()

    const [loading, setLoading] = useState(false)
    const [loadingEmpleados, setLoadingEmpleados] = useState(false)
    const [empleados, setEmpleados] = useState<EmpleadoListItem[]>([])
    const [empleadoInicial, setEmpleadoInicial] = useState<EmpleadoListItem | null>(null)

    const [formData, setFormData] = useState({
        nombre: '',
        ciudad: null as number | null,
        direccion: '',
        telefono: '',
        capacidad_m3: '',
        responsable: null as string | null,
        es_principal: false,
        permite_ventas: false,
        is_active: true,
    })

    useEffect(() => {
        async function loadEmpleadoInicial() {
            if (!isEditMode || !bodega?.responsable?.id) return
            try {
                const data = await apiFetch<BuscarResponse<EmpleadoListItem>>(
                    `/api/empleados/buscar/?q=${bodega.responsable.id}`
                )
                const empleado = data.results[0] ?? null
                setEmpleadoInicial(empleado)
                setEmpleados(empleado ? [empleado] : [])
            } catch (error) {
                console.warn('Error cargando empleado inicial:', error)
            }
        }

        loadEmpleadoInicial()
    }, [isEditMode, bodega])

    // Cargar datos del formulario en modo edición
    useEffect(() => {
        if (isEditMode && bodega) {
            setFormData({
                nombre:          bodega.nombre || '',
                ciudad:          bodega.ciudad?.id || null,
                direccion:       bodega.direccion || '',
                telefono:        bodega.telefono || '',
                capacidad_m3:    bodega.capacidad_m3?.toString() || '',
                responsable:     bodega.responsable?.id || null,
                es_principal:    bodega.es_principal || false,
                permite_ventas:  bodega.permite_ventas || false,
                is_active:       bodega.is_active ?? true,
            })
        }
    }, [isEditMode, bodega])

    // Búsqueda de empleados para el Select
    const buscarEmpleados = async (query: string) => {
        if (query.trim() === '') {
            setEmpleados(empleadoInicial ? [empleadoInicial] : [])
            return
        }

        setLoadingEmpleados(true)
        try {
            const data = await apiFetch<BuscarResponse<EmpleadoListItem>>(
                `/api/empleados/buscar/?q=${encodeURIComponent(query)}`
            )
            setEmpleados(data.results)
        } catch (err) {
            if (err instanceof ApiError) {
                alertas.error(err.mensaje, err.titulo)
            } else {
                alertas.error('Error al buscar empleados', 'Error')
            }
        } finally {
            setLoadingEmpleados(false)
        }
    }

    const validarFormulario = (): boolean => {
        if (!formData.nombre.trim()) {
            alertas.warning('El nombre de la bodega es requerido', 'Campo Requerido')
            return false
        }
        if (!formData.responsable) {
            alertas.warning('Debe asignar un responsable a la bodega', 'Campo Requerido')
            return false
        }
        if (formData.telefono && !/^[\d\s\-\+\(\)]{7,20}$/.test(formData.telefono)) {
            alertas.warning('El formato del teléfono no es válido', 'Campo Inválido')
            return false
        }
        const capacidad = parseFloat(formData.capacidad_m3)
        if (formData.capacidad_m3 && (isNaN(capacidad) || capacidad <= 0)) {
            alertas.warning('La capacidad debe ser un valor positivo', 'Campo Inválido')
            return false
        }
        return true
    }

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        e.stopPropagation()

        if (loading) return
        if (!validarFormulario()) return

        setLoading(true)
        try {
            const payload: Record<string, any> = {
                nombre:         formData.nombre,
                direccion:      formData.direccion,
                telefono:       formData.telefono,
                responsable:    formData.responsable,
                es_principal:   formData.es_principal,
                permite_ventas: formData.permite_ventas,
                is_active:      formData.is_active,
            }

            if (formData.ciudad)      payload.ciudad      = formData.ciudad
            if (formData.capacidad_m3) payload.capacidad_m3 = parseFloat(formData.capacidad_m3)

            await apiFetch(
                isEditMode ? `/api/bodegas/${bodega?.id}/` : `/api/bodegas/`,
                {
                    method: isEditMode ? 'PATCH' : 'POST',
                    body: JSON.stringify(payload),
                }
            )

            alertas.success(
                isEditMode ? 'Bodega actualizada exitosamente' : 'Bodega creada exitosamente',
                isEditMode ? 'Bodega Actualizada' : 'Bodega Creada'
            )

            await mutate(['/api/bodegas/'])
            setTimeout(() => router.push('/inventario/bodegas'), 1500)

        } catch (error: any) {
            alertas.error(
                error.mensaje || error.message || 'Error desconocido al guardar la bodega',
                isEditMode ? 'Error al Actualizar' : 'Error al Crear'
            )
        } finally {
            setLoading(false)
        }
    }

    const handleCancel = () => {
        router.push('/inventario/bodegas')
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 gap-6">
            <div className="lg:col-span-2 space-y-6">
                {/* Información básica */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-warehouse text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">INFORMACIÓN
                                BÁSICA</h2>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-tag mr-2 text-muted-primary"></i>
                                Nombre de la Bodega *
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange('nombre', e.target.value)}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Ej: Bodega Central, Almacén Norte..."
                                required
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-map-marker-alt mr-2 text-muted-primary"></i>
                                    Ciudad
                                </label>
                                <Select
                                    options={ciudades?.map(c => ({
                                        value: c.id,
                                        label: c.name,
                                        description: c.region?.name,
                                        icon: 'fas fa-city'
                                    })) || []}
                                    value={formData.ciudad || ''}
                                    onChange={(value) => handleInputChange('ciudad', value ? Number(value) : null)}
                                    searchable
                                    placeholder="Seleccionar ciudad"
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-phone mr-2 text-muted-primary"></i>
                                    Teléfono
                                </label>
                                <input
                                    type="tel"
                                    value={formData.telefono}
                                    onChange={(e) => handleInputChange('telefono', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="+593 2 123-4567"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-location-dot mr-2 text-muted-primary"></i>
                                Dirección
                            </label>
                            <textarea
                                value={formData.direccion}
                                onChange={(e) => handleInputChange('direccion', e.target.value)}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                                placeholder="Dirección completa de la bodega..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-cubes mr-2 text-muted-primary"></i>
                                Capacidad (m³)
                                <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                            </label>
                            <input
                                type="number"
                                value={formData.capacidad_m3}
                                onChange={(e) => handleInputChange('capacidad_m3', e.target.value)}
                                min="0"
                                step="0.01"
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="1000.00"
                            />
                        </div>
                    </div>
                </div>

                {/* Configuración */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-sliders text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">Configuración</h2>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-user-tie mr-2 text-muted-primary"></i>
                                Responsable *
                            </label>
                            <Select
                                options={empleados.map(e => ({
                                    value: e.id,
                                    label: e.nombre_completo.toUpperCase(),
                                    description: e.puesto,
                                    icon: 'fas fa-user'
                                }))}
                                value={formData.responsable || ''}
                                onChange={(value) => handleInputChange('responsable', value || null)}
                                onSearch={buscarEmpleados}
                                searchable
                                placeholder="Buscar responsable..."
                                className="w-full"
                                loading={loadingEmpleados}
                            />
                            <p className="text-xs text-muted-foreground mt-1.5">
                                <i className="fa-solid fa-info-circle mr-1"></i>
                                Empleado a cargo de esta bodega
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <CheckboxKlyra
                                    checked={formData.es_principal}
                                    onChange={(checked) => handleInputChange('es_principal', checked)}
                                    label="Bodega Principal"
                                    className="mb-2"
                                />
                                <p className="text-xs text-muted-foreground ml-6">
                                    Solo puede haber una bodega principal en el sistema
                                </p>
                            </div>

                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <CheckboxKlyra
                                    checked={formData.permite_ventas}
                                    onChange={(checked) => handleInputChange('permite_ventas', checked)}
                                    label="Permite Ventas"
                                    className="mb-2"
                                />
                                <p className="text-xs text-muted-foreground ml-6">
                                    Esta bodega puede realizar ventas directas
                                </p>
                            </div>
                        </div>

                        {formData.es_principal && (
                            <div
                                className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                                <div className="flex gap-2 text-yellow-800 dark:text-yellow-300 text-sm">
                                    <i className="fa-solid fa-crown mt-0.5"></i>
                                    <div>
                                        <p className="font-medium">Bodega Principal</p>
                                        <p className="text-xs mt-1">
                                            Esta bodega será la principal del sistema. Si ya existe otra bodega
                                            principal,
                                            será reemplazada automáticamente.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.permite_ventas && (
                            <div
                                className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                                <div className="flex gap-2 text-green-800 dark:text-green-300 text-sm">
                                    <i className="fa-solid fa-cash-register mt-0.5"></i>
                                    <div>
                                        <p className="font-medium">Ventas Habilitadas</p>
                                        <p className="text-xs mt-1">
                                            Esta bodega podrá procesar ventas y generar facturas desde su inventario.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Columna lateral */}
            <div className="space-y-6">
                {/* Información adicional (solo en edición) */}
                {isEditMode && bodega && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-chart-line text-muted-foreground text-lg"></i>
                            </div>
                            <div>
                                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">ESTADÍSTICAS</h2>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground">Código:</span>
                                <span className="text-sm font-mono font-medium text-foreground">{bodega.codigo}</span>
                            </div>
                            {bodega.total_productos !== undefined && (
                                <div className="flex justify-between items-center py-2 border-b border-border">
                                    <span className="text-xs text-muted-foreground">Productos:</span>
                                    <span
                                        className="text-sm font-medium text-foreground">{bodega.total_productos}</span>
                                </div>
                            )}
                            {bodega.valor_total_inventario !== undefined && (
                                <div className="flex justify-between items-center py-2 border-b border-border">
                                    <span className="text-xs text-muted-foreground">Valor inventario:</span>
                                    <span className="text-sm font-medium text-foreground">
                                        ${bodega.valor_total_inventario.toFixed(2)}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Advertencias */}
                {isEditMode && bodega && bodega.total_productos !== undefined && bodega.total_productos > 0 && (
                    <div
                        className="bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
                        <div className="flex gap-2 text-orange-800 dark:text-orange-300">
                            <i className="fa-solid fa-exclamation-triangle mt-0.5"></i>
                            <div className="text-xs">
                                <p className="font-medium mb-1">Bodega con inventario</p>
                                <p>Esta bodega tiene {bodega.total_productos} productos. No podrá ser eliminada mientras
                                    tenga inventario.</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </form>
    )
}