import {useState, useEffect} from "react"
import {useRouter} from "next/navigation"
import {Categoria} from "@/src/core/api/types"
import {mutate} from "swr"
import {Select} from "@/components/select/select-klyra"
import {alertas} from "@/components/alerts/alertas-toast"
import {useCategoriasArbolExpandido} from "@/src/core/store"
import {apiFetch, ApiError} from "@/src/core/api/client"
import type React from "react"

interface CategoriaFormProps {
    mode: 'create' | 'edit'
    categoria?: Categoria | null
    formRef?: React.RefObject<HTMLFormElement>
}

interface SubcategoriaNueva {
    id: string
    nombre: string
    descripcion: string
}

export function CategoriaForm({mode, categoria, formRef}: CategoriaFormProps) {
    const router = useRouter()
    const isEditMode = mode === 'edit'

    const {data: categoriasData} = useCategoriasArbolExpandido()

    const [loading, setLoading] = useState(false)
    const [showModalSubcategoria, setShowModalSubcategoria] = useState(false)

    // Estado para subcategorías nuevas (a crear)
    const [subcategoriasNuevas, setSubcategoriasNuevas] = useState<SubcategoriaNueva[]>([])

    // Estado para subcategorías existentes (a enlazar)
    const [subcategoriasExistentes, setSubcategoriasExistentes] = useState<string[]>([])

    // Estado para el modal
    const [nuevaSubcategoria, setNuevaSubcategoria] = useState({
        nombre: '',
        descripcion: ''
    })

    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: '',
        categoria_padre: null as string | null,
        imagen: null as File | null,
        is_active: true,
    })

    // Cargar datos en modo edición
    useEffect(() => {
        if (isEditMode && categoria) {
            setFormData({
                nombre: categoria.nombre || '',
                descripcion: categoria.descripcion || '',
                categoria_padre: categoria.categoria_padre || null,
                imagen: null,
                is_active: categoria.is_active ?? true,
            })
        }
    }, [isEditMode, categoria])

    const validarFormulario = () => {
        if (!formData.nombre.trim()) {
            alertas.warning('El nombre de la categoría es requerido', 'Campo Requerido')
            return false
        }

        if (isEditMode && categoria && formData.categoria_padre === categoria.id) {
            alertas.warning('Una categoría no puede ser su propio padre', 'Error de Jerarquía')
            return false
        }

        if (formData.categoria_padre && isEditMode && categoria) {
            const verificarCiclo = (padreId: string, visitados = new Set<string>()): boolean => {
                if (visitados.has(padreId)) return true
                visitados.add(padreId)

                const padre = categoriasData?.find(c => c.id === padreId)
                if (!padre) return false
                if (padre.id === categoria.id) return true
                if (padre.categoria_padre) {
                    return verificarCiclo(padre.categoria_padre, visitados)
                }
                return false
            }

            if (verificarCiclo(formData.categoria_padre)) {
                alertas.warning('No se puede crear un ciclo en la jerarquía', 'Error de Jerarquía')
                return false
            }
        }

        return true
    }

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => ({...prev, [field]: value}))
    }

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0]
            if (file.size > 5 * 1024 * 1024) {
                alertas.error('La imagen no debe superar los 5MB', "Error de Tamaño")
                return
            }
            if (!file.type.startsWith('image/')) {
                alertas.error('Solo se permiten archivos de imagen', "Error de Formato")
                return
            }
            handleInputChange('imagen', file)
        }
    }

    // ==================== GESTIÓN DE SUBCATEGORÍAS ====================

    const agregarSubcategoriaNueva = () => {
        if (!nuevaSubcategoria.nombre.trim()) {
            alertas.warning('El nombre de la subcategoría es requerido', 'Campo Requerido')
            return
        }

        const nuevaSub: SubcategoriaNueva = {
            id: `temp-${Date.now()}`, // ID temporal
            nombre: nuevaSubcategoria.nombre,
            descripcion: nuevaSubcategoria.descripcion
        }

        setSubcategoriasNuevas(prev => [...prev, nuevaSub])
        setNuevaSubcategoria({nombre: '', descripcion: ''})
        setShowModalSubcategoria(false)

        alertas.success('Subcategoría agregada', 'Se creará al guardar la categoría principal')
    }

    const eliminarSubcategoriaNueva = (id: string) => {
        setSubcategoriasNuevas(prev => prev.filter(sub => sub.id !== id))
        alertas.info('Subcategoría eliminada de la lista', 'Cambios Pendientes')
    }

    const agregarSubcategoriaExistente = (categoriaId: string) => {
        if (!categoriaId || subcategoriasExistentes.includes(categoriaId)) return

        setSubcategoriasExistentes(prev => [...prev, categoriaId])
        alertas.success('Categoría agregada como subcategoría', 'Se enlazará al guardar')
    }

    const eliminarSubcategoriaExistente = (categoriaId: string) => {
        setSubcategoriasExistentes(prev => prev.filter(id => id !== categoriaId))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        e.stopPropagation()

        if (loading) return
        if (!validarFormulario()) return

        setLoading(true)
        try {
            const formDataToSend = new FormData()

            formDataToSend.append('categoria', JSON.stringify({
                nombre: formData.nombre,
                descripcion: formData.descripcion,
                is_active: formData.is_active,
                categoria_padre: formData.categoria_padre
            }))

            if (subcategoriasNuevas.length > 0)
                formDataToSend.append('subcategorias_nuevas', JSON.stringify(subcategoriasNuevas))

            if (subcategoriasExistentes.length > 0)
                formDataToSend.append('subcategorias_existentes', JSON.stringify(subcategoriasExistentes))

            if (formData.imagen)
                formDataToSend.append('imagen', formData.imagen)

            await apiFetch(
                isEditMode
                    ? `/api/categorias/${categoria?.id}/actualizar-con-subcategorias/`
                    : `/api/categorias/crear-con-subcategorias/`,
                {method: isEditMode ? 'PATCH' : 'POST', body: formDataToSend}
            )

            alertas.success(
                isEditMode ? 'Categoría actualizada con subcategorías' : 'Categoría creada con subcategorías',
                isEditMode ? 'Categoría Actualizada' : 'Categoría Creada'
            )

            await Promise.all([
                mutate(['/api/categorias/']),
                mutate('/api/categorias/arbol_expandido/')
            ])

            setTimeout(() => router.push('/inventario/categorias'), 1500)

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

    const opcionesCategoriasPadre = () => {
        if (!categoriasData) return []

        let categoriasDisponibles = [...categoriasData]

        if (isEditMode && categoria) {
            const excluirIds = new Set<string>([categoria.id])

            const agregarSubcategorias = (cat: Categoria) => {
                cat.subcategorias?.forEach(sub => {
                    excluirIds.add(sub.id)
                    agregarSubcategorias(sub)
                })
            }

            agregarSubcategorias(categoria)
            categoriasDisponibles = categoriasDisponibles.filter(c => !excluirIds.has(c.id))
        }

        // Excluir categorías ya seleccionadas como subcategorías existentes
        categoriasDisponibles = categoriasDisponibles.filter(
            c => !subcategoriasExistentes.includes(c.id)
        )

        return categoriasDisponibles.map(cat => {
            const icono = cat.subcategorias?.length > 0 ? 'fa-solid fa-folder-tree' : 'fa-solid fa-sitemap'

            return {
                value: cat.id,
                label: `${cat.nombre}`,
                description: `Nivel ${cat.nivel}${cat.codigo ? ` • ${cat.codigo}` : ''}`,
                nivel: cat.nivel,
                icon: `${icono}`
            }
        })
    }

    const getCategoriaPadreInfo = () => {
        if (!formData.categoria_padre || !categoriasData) return null
        return categoriasData.find(c => c.id === formData.categoria_padre)
    }

    const getNivelCalculado = () => {
        const padre = getCategoriaPadreInfo()
        return padre ? padre.nivel + 1 : 1
    }

    const getNombreCategoria = (id: string) => {
        return categoriasData?.find(c => c.id === id)?.nombre || 'Categoría'
    }

    return (
    <>
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
                {/* Información básica */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-folder-tree text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información Básica</h2>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-tag mr-2"></i>Nombre de la Categoría *
                            </label>
                            <input
                                type="text"
                                value={formData.nombre}
                                onChange={(e) => handleInputChange('nombre', e.target.value)}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Ej. Categoría A"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-align-left mr-2"></i>Descripción
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange('descripcion', e.target.value)}
                                rows={4}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                                placeholder="Descripción detallada de la categoría..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-image mr-2"></i>Imagen de la Categoría
                            </label>
                            <div className="flex items-center gap-4">
                                <div className="flex-1">
                                    <label className="relative cursor-pointer group">
                                        <input type="file" onChange={handleImageChange} accept="image/*" className="hidden"/>
                                        <div className="flex items-center justify-center gap-3 px-4 py-3 bg-background border-2 border-dashed border-border rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-all">
                                            <i className="fa-solid fa-cloud-arrow-up text-muted-foreground group-hover:text-primary transition-colors text-sm"></i>
                                            <span className="text-sm text-muted-foreground group-hover:text-primary transition-colors">
                                                {formData.imagen ? 'Cambiar imagen' : 'Seleccionar imagen'}
                                            </span>
                                        </div>
                                    </label>
                                </div>
                                {(categoria?.imagen || formData.imagen) && (
                                    <div className="w-16 h-16 rounded-lg border border-border overflow-hidden flex-shrink-0">
                                        <img
                                            src={formData.imagen ? URL.createObjectURL(formData.imagen) : categoria?.imagen || ''}
                                            alt="Preview"
                                            className="w-full h-full object-cover"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Jerarquía */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-sitemap text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Jerarquía</h2>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            <i className="fa-solid fa-folder mr-2"></i>
                            Categoría Padre
                            <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                        </label>
                        <Select
                            options={[
                                { value: '', label: 'Sin padre (Categoría Principal)', description: 'Nivel 1', icon: 'fa-solid fa-folder' },
                                ...opcionesCategoriasPadre()
                            ]}
                            value={formData.categoria_padre || ''}
                            onChange={(value) => handleInputChange('categoria_padre', value || null)}
                            searchable
                            placeholder="Buscar categoría padre..."
                            className="w-full"
                        />

                        {formData.categoria_padre && getCategoriaPadreInfo() && (
                            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                <div className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-300">
                                    <i className="fa-solid fa-arrow-right text-xs"></i>
                                    <span>Esta será una subcategoría de:</span>
                                    <strong>{getCategoriaPadreInfo()?.nombre}</strong>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="mt-4 p-4 bg-muted/30 rounded-lg border border-border">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 bg-background rounded-lg flex items-center justify-center border border-border">
                                    <i className="fa-solid fa-layer-group text-muted-foreground text-sm"></i>
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground">Nivel calculado</p>
                                    <p className="text-base font-bold text-foreground">Nivel {getNivelCalculado()}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-xs text-muted-foreground mb-1">Tipo</p>
                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                                    getNivelCalculado() === 1
                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                        : 'bg-primary/10 text-primary'
                                }`}>
                                    <i className={`fa-solid ${getNivelCalculado() === 1 ? 'fa-crown' : 'fa-folder'} text-[9px]`}></i>
                                    {getNivelCalculado() === 1 ? 'Principal' : 'Subcategoría'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Información — solo en modo edición, movida a columna principal */}
                {isEditMode && categoria && (
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-circle-info text-muted-foreground text-lg"></i>
                            </div>
                            <div>
                                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información</h2>
                            </div>
                        </div>

                        <div className="space-y-1">
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-barcode"></i>Código
                                </span>
                                <span className="font-mono text-xs font-semibold text-foreground bg-muted/50 px-2 py-1 rounded-md">{categoria.codigo}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-xs text-muted-foreground flex items-center gap-2">
                                    <i className="fa-solid fa-angles-up"></i>Nivel actual
                                </span>
                                <span className="text-sm font-medium text-foreground">Nivel {categoria.nivel}</span>
                            </div>
                            {categoria?.subcategorias && categoria.subcategorias.length > 0 && (
                                <div className="flex justify-between items-center py-2">
                                    <span className="text-xs text-muted-foreground flex items-center gap-2">
                                        <i className="fa-solid fa-folder-tree"></i>Subcategorías
                                    </span>
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary">
                                        {categoria.subcategorias.length}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Columna lateral — solo Subcategorías */}
            <div className="space-y-6">
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-folder-plus text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Subcategorías</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {subcategoriasNuevas.length + subcategoriasExistentes.length} pendientes
                            </p>
                        </div>
                    </div>

                    <div className="space-y-3 mb-4">
                        <Select
                            options={opcionesCategoriasPadre()}
                            value=""
                            onChange={agregarSubcategoriaExistente.toString}
                            searchable
                            placeholder="Enlazar existente..."
                            className="w-full"
                        />
                        <button
                            type="button"
                            onClick={() => setShowModalSubcategoria(true)}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg text-sm font-medium transition-all shadow-sm"
                        >
                            <i className="fa-solid fa-plus text-xs"></i>
                            Nueva Subcategoría
                        </button>
                    </div>

                    {subcategoriasNuevas.length > 0 && (
                        <div className="mb-3">
                            <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
                                <i className="fa-solid fa-sparkles text-[9px]"></i>
                                Nuevas ({subcategoriasNuevas.length})
                            </p>
                            <div className="space-y-2">
                                {subcategoriasNuevas.map(sub => (
                                    <div key={sub.id} className="flex items-center justify-between p-3 bg-muted/30 border border-border rounded-lg">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-foreground truncate">{sub.nombre}</p>
                                            {sub.descripcion && (
                                                <p className="text-xs text-muted-foreground truncate">{sub.descripcion}</p>
                                            )}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => eliminarSubcategoriaNueva(sub.id)}
                                            className="ml-2 w-7 h-7 flex items-center justify-center text-destructive hover:bg-destructive/10 rounded-md transition-all flex-shrink-0"
                                        >
                                            <i className="fa-solid fa-trash text-xs"></i>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {subcategoriasExistentes.length > 0 && (
                        <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
                                <i className="fa-solid fa-link text-[9px]"></i>
                                Existentes ({subcategoriasExistentes.length})
                            </p>
                            <div className="space-y-2">
                                {subcategoriasExistentes.map(id => (
                                    <div key={id} className="flex items-center justify-between p-3 bg-primary/5 border border-primary/20 rounded-lg">
                                        <p className="text-sm font-medium text-foreground truncate">{getNombreCategoria(id)}</p>
                                        <button
                                            type="button"
                                            onClick={() => eliminarSubcategoriaExistente(id)}
                                            className="ml-2 w-7 h-7 flex items-center justify-center text-destructive hover:bg-destructive/10 rounded-md transition-all flex-shrink-0"
                                        >
                                            <i className="fa-solid fa-unlink text-xs"></i>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {subcategoriasNuevas.length === 0 && subcategoriasExistentes.length === 0 && (
                        <div className="py-8 text-center">
                            <i className="fa-solid fa-folder-open text-3xl text-muted-foreground/20 mb-3 block"></i>
                            <p className="text-sm text-muted-foreground">No hay subcategorías agregadas</p>
                            <p className="text-xs text-muted-foreground/70 mt-0.5">Crea nuevas o enlaza existentes</p>
                        </div>
                    )}
                </div>
            </div>
        </form>

        {/* Modal */}
        {showModalSubcategoria && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <div className="bg-card rounded-xl border border-border shadow-2xl w-full max-w-lg mx-4 animate-in fade-in zoom-in duration-200">
                    <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-folder-plus text-muted-foreground text-sm"></i>
                            </div>
                            <div>
                                <h3 className="text-sm font-semibold text-foreground">Nueva Subcategoría</h3>
                                <p className="text-xs text-muted-foreground mt-0.5">Se creará al guardar la categoría principal</p>
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => { setShowModalSubcategoria(false); setNuevaSubcategoria({nombre: '', descripcion: ''}) }}
                            className="w-7 h-7 flex items-center justify-center hover:bg-muted rounded-md transition-all text-muted-foreground hover:text-foreground"
                        >
                            <i className="fa-solid fa-times text-xs"></i>
                        </button>
                    </div>

                    <div className="p-6 space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-tag mr-2"></i>Nombre de la Subcategoría *
                            </label>
                            <input
                                type="text"
                                value={nuevaSubcategoria.nombre}
                                onChange={(e) => setNuevaSubcategoria(prev => ({...prev, nombre: e.target.value}))}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Ej. Subcategoría A.1"
                                autoFocus
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-align-left mr-2"></i>
                                Descripción
                                <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                            </label>
                            <textarea
                                value={nuevaSubcategoria.descripcion}
                                onChange={(e) => setNuevaSubcategoria(prev => ({...prev, descripcion: e.target.value}))}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                                placeholder="Descripción breve de la subcategoría..."
                            />
                        </div>

                        <div className="p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                            <div className="flex items-start gap-3">
                                <i className="fa-solid fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5 text-sm"></i>
                                <div className="text-xs text-blue-800 dark:text-blue-300">
                                    <p className="font-medium text-sm mb-1">Esta subcategoría tendrá:</p>
                                    <p>Nivel: <strong>{getNivelCalculado() + 1}</strong></p>
                                    <p className="mt-0.5">Padre: <strong>{formData.nombre || '(Nombre de categoría principal)'}</strong></p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3 px-6 py-4 border-t border-border">
                        <button
                            type="button"
                            onClick={() => { setShowModalSubcategoria(false); setNuevaSubcategoria({nombre: '', descripcion: ''}) }}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-all"
                        >
                            <i className="fa-solid fa-times text-xs"></i>Cancelar
                        </button>
                        <button
                            type="button"
                            onClick={agregarSubcategoriaNueva}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg text-sm font-medium transition-all shadow-sm"
                        >
                            <i className="fa-solid fa-plus text-xs"></i>Agregar
                        </button>
                    </div>
                </div>
            </div>
        )}
    </>
)
}
