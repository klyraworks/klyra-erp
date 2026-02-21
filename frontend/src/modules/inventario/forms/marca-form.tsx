// frontend/src/modules/inventario/forms/marca-form.tsx

"use client"

import {useState, useEffect, useRef} from "react"
import {useRouter} from "next/navigation"
import {mutate} from "swr"
import {alertas} from "@/components/alerts/alertas-toast"
import {apiFetch, ApiError} from "@/src/core/api/client"
import {Marca} from "@/src/core/api/types"
import React from "react"

interface PaisListItem {
    id: number
    nombre: string
}

interface MarcaFormProps {
    mode: 'create' | 'edit'
    marca?: Marca | null
    formRef?: React.RefObject<HTMLFormElement>
}

export function MarcaForm({mode, marca, formRef}: MarcaFormProps) {
    const router = useRouter()
    const isEditMode = mode === 'edit'
    const fileInputRef = useRef<HTMLInputElement>(null)

    const [loading, setLoading] = useState(false)
    const [paises, setPaises] = useState<PaisListItem[]>([])
    const [logoPreview, setLogoPreview] = useState<string | null>(null)
    const [logoFile, setLogoFile] = useState<File | null>(null)
    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: '',
        pais_origen: '' as string | number,
    })

    useEffect(() => {
        async function loadPaises() {
            try {
                const data = await apiFetch<{ results: PaisListItem[] }>('/api/paises/?page_size=300')
                setPaises(data.results ?? (data as unknown as PaisListItem[]))
            } catch {
                // silencioso — no crítico
            }
        }

        loadPaises()
    }, [])

    useEffect(() => {
        if (isEditMode && marca) {
            setFormData({
                nombre: marca.nombre || '',
                descripcion: marca.descripcion || '',
                pais_origen: marca.pais_origen ?? '',
            })
            if (marca.logo) setLogoPreview(marca.logo)
        }
    }, [isEditMode, marca])

    const handleInputChange = (field: string, value: string | number) => {
        setFormData(prev => ({...prev, [field]: value}))
    }

    const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return
        setLogoFile(file)
        const reader = new FileReader()
        reader.onload = (ev) => setLogoPreview(ev.target?.result as string)
        reader.readAsDataURL(file)
    }

    const handleRemoveLogo = () => {
        setLogoFile(null)
        setLogoPreview(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const validarFormulario = (): boolean => {
        if (!formData.nombre.trim()) {
            alertas.warning('El nombre de la marca es requerido', 'Campo Requerido')
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
            const body = new FormData()
            body.append('nombre', formData.nombre.trim())
            if (formData.descripcion.trim()) body.append('descripcion', formData.descripcion.trim())
            if (formData.pais_origen) body.append('pais_origen', String(formData.pais_origen))
            if (logoFile) body.append('logo', logoFile)
            body.append('is_active', String(true))

            await apiFetch(
                isEditMode ? `/api/marcas/${marca?.id}/` : '/api/marcas/',
                {
                    method: isEditMode ? 'PATCH' : 'POST',
                    body,
                }
            )

            alertas.success(
                isEditMode ? 'Marca actualizada exitosamente' : 'Marca creada exitosamente',
                isEditMode ? 'Marca Actualizada' : 'Marca Creada'
            )

            await mutate(['/api/marcas/'])
            setTimeout(() => router.push('/inventario/marcas'), 1500)
        } catch (err) {
            if (err instanceof ApiError) {
                alertas.error(err.mensaje, err.titulo)
            } else {
                alertas.error('Error desconocido al guardar', isEditMode ? 'Error al Actualizar' : 'Error al Crear')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 gap-6">
            {/* Columna principal */}
            <div className="lg:col-span-2 space-y-6">
                {/* Alerta info */}
                <div
                    className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <i className="fa-solid fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"></i>
                        <div className="text-xs text-blue-700 dark:text-blue-400">
                            <p className="font-medium text-sm text-blue-800 dark:text-blue-300 mb-1">Sobre las
                                marcas</p>
                            <p>El código se genera automáticamente. No se puede eliminar una marca que tenga productos
                                activos asociados.</p>
                        </div>
                    </div>
                </div>
                {/* Información general */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-tag text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                                Información General
                            </h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Datos principales de la marca</p>
                        </div>
                    </div>

                    <div className="space-y-5">
                        {/* Nombre */}
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-font mr-2"></i>Nombre *
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange('nombre', e.target.value)}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Nombre de la marca..."
                            />
                        </div>

                        {/* Descripción */}
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-align-left mr-2"></i>Descripción
                                <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange('descripcion', e.target.value)}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                                placeholder="Descripción de la marca..."
                            />
                        </div>

                        {/* País de origen */}
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-earth-americas mr-2"></i>País de Origen
                                <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                            </label>
                            <select
                                value={formData.pais_origen}
                                onChange={(e) => handleInputChange('pais_origen', e.target.value ? Number(e.target.value) : '')}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                            >
                                <option value="">Seleccionar país...</option>
                                {paises.map((p) => (
                                    <option key={p.id} value={p.id}>{p.nombre}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Logo */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-image text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                                Logo de la Marca
                            </h2>
                            <p className="text-xs text-muted-foreground mt-0.5">Imagen representativa (opcional)</p>
                        </div>
                    </div>

                    <div className="flex items-start gap-6">
                        {/* Preview */}
                        <div className="flex-shrink-0">
                            <div
                                className="w-24 h-24 bg-muted/30 border border-border rounded-xl flex items-center justify-center overflow-hidden">
                                {logoPreview ? (
                                    <img src={logoPreview} alt="Logo" className="w-full h-full object-contain p-2"/>
                                ) : (
                                    <i className="fa-solid fa-image text-3xl text-muted-foreground/40"></i>
                                )}
                            </div>
                        </div>

                        {/* Controles */}
                        <div className="flex-1 space-y-3">
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                onChange={handleLogoChange}
                                className="hidden"
                                id="logo-input"
                            />
                            <label
                                htmlFor="logo-input"
                                className="inline-flex items-center gap-2 px-4 py-2.5 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-all cursor-pointer"
                            >
                                <i className="fa-solid fa-upload"></i>
                                {logoPreview ? 'Cambiar logo' : 'Subir logo'}
                            </label>
                            {logoPreview && (
                                <button
                                    type="button"
                                    onClick={handleRemoveLogo}
                                    className="flex items-center gap-2 px-4 py-2.5 border border-border rounded-lg text-sm font-medium text-destructive hover:bg-muted transition-all"
                                >
                                    <i className="fa-solid fa-trash"></i>
                                    Eliminar logo
                                </button>
                            )}
                            <p className="text-xs text-muted-foreground">
                                <i className="fa-solid fa-info-circle mr-1"></i>
                                Formatos aceptados: PNG, JPG, SVG. Tamaño máximo: 2MB.
                            </p>
                        </div>
                    </div>
                </div>


                {isEditMode && marca && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-circle-info text-muted-foreground text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Detalles</h2>
                        </div>
                        <div className="space-y-1">
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-barcode"></i>Código
                                </span>
                                <span
                                    className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">{marca.codigo}</span>
                            </div>
                            <div className="flex items-center justify-between py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-circle-dot"></i>Estado
                                </span>
                                {marca.is_active ? (
                                    <span
                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                        <i className="fa-solid fa-circle-check text-[9px]"></i>Activa
                                    </span>
                                ) : (
                                    <span
                                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-destructive/10 text-destructive">
                                        <i className="fa-solid fa-ban text-[9px]"></i>Inactiva
                                    </span>
                                )}
                            </div>
                            <div
                                className={`flex items-center justify-between py-2 ${marca.pais_origen_nombre ? 'border-b border-border' : ''}`}>
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-box"></i>Productos
                                </span>
                                <span
                                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                                    {marca.total_productos}
                                </span>
                            </div>
                            {marca.pais_origen_nombre && (
                                <div className="flex items-center justify-between py-2">
                                    <span className="text-xs text-muted-foreground flex items-center gap-2">
                                        <i className="fa-solid fa-earth-americas"></i>País
                                    </span>
                                    <span
                                        className="text-xs font-medium text-foreground">{marca.pais_origen_nombre}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </form>
    )
}