import {useState, useEffect} from "react"
import {useRouter} from "next/navigation"
import {Categoria} from "@/src/core/api/types"
import {mutate} from "swr"
import {Select} from "@/components/select/select-klyra"
import {alertas} from "@/components/alerts/alertas-toast"
import {useCategoriasArbolExpandido} from "@/src/core/store"
import { apiFetch, ApiError } from "@/src/core/api/client"

interface CategoriaFormProps {
    mode: 'create' | 'edit'
    categoria?: Categoria | null
}

interface SubcategoriaNueva {
    id: string // ID temporal para manejo en el frontend
    nombre: string
    descripcion: string
}

export function CategoriaForm({mode, categoria}: CategoriaFormProps) {
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

        const esValido = validarFormulario()
        if (!esValido) return

        setLoading(true)

        try {
            const formDataToSend = new FormData()

            const categoriaData = {
                nombre: formData.nombre,
                descripcion: formData.descripcion,
                is_active: formData.is_active,
                categoria_padre: formData.categoria_padre
            }

            formDataToSend.append('categoria', JSON.stringify(categoriaData))

            if (subcategoriasNuevas.length > 0) {
                formDataToSend.append('subcategorias_nuevas', JSON.stringify(subcategoriasNuevas))
            }

            if (subcategoriasExistentes.length > 0) {
                formDataToSend.append('subcategorias_existentes', JSON.stringify(subcategoriasExistentes))
            }

            if (formData.imagen) {
                formDataToSend.append('imagen', formData.imagen)
            }

            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'


            const url = isEditMode
                ? `${API_BASE_URL}/api/categorias/${categoria?.id}/actualizar-con-subcategorias/`
                : `${API_BASE_URL}/api/categorias/crear-con-subcategorias/`

            await apiFetch(
                isEditMode
                    ? `/api/categorias/${categoria?.id}/actualizar-con-subcategorias/`
                    : `/api/categorias/crear-con-subcategorias/`,
                {
                    method: isEditMode ? 'PATCH' : 'POST',
                    body: formDataToSend,
                }
            )

            await mutate(['/api/categorias/'])

            alertas.success(
                isEditMode
                    ? `Categoría actualizada con subcategorías`
                    : `Categoría creada con subcategorías`,
                isEditMode ? 'Categoría Actualizada' : 'Categoría Creada'
            )

            await mutate('/api/categorias/arbol_expandido/')

            setTimeout(() => {
                router.push('/inventario/categorias')
            }, 1500)

        } catch (error: any) {
            const mensaje = error.message || 'Error desconocido al guardar la categoría'
            alertas.error(mensaje, isEditMode ? 'Error al Actualizar' : 'Error al Crear')
        } finally {
            setLoading(false)
        }
    }

    const handleCancel = () => {
        router.push('/inventario/categorias')
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
            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    {/* Información básica */}
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-folder-tree text-muted-foreground text-lg"></i>
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
                                    Nombre de la Categoría *
                                </label>
                                <input
                                    type="text"
                                    value={formData.nombre}
                                    onChange={(e) => handleInputChange('nombre', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder={"Ej. Categoría A"}
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-align-left mr-2 text-muted-primary"></i>
                                    Descripción
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
                                    <i className="fa-solid fa-image mr-2 text-muted-primary"></i>
                                    Imagen de la Categoría
                                </label>
                                <div className="flex items-center gap-4">
                                    <div className="flex-1">
                                        <label className="relative cursor-pointer group">
                                            <input
                                                type="file"
                                                onChange={handleImageChange}
                                                accept="image/*"
                                                className="hidden"
                                            />
                                            <div
                                                className="flex items-center justify-center gap-3 px-4 py-3 bg-background border-2 border-dashed border-border rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-all">
                                                <i className="fa-solid fa-cloud-arrow-up text-muted-foreground group-hover:text-primary transition-colors"></i>
                                                <span
                                                    className="text-sm text-muted-foreground group-hover:text-primary transition-colors">
                                                {formData.imagen ? 'Cambiar imagen' : 'Seleccionar imagen'}
                                            </span>
                                            </div>
                                        </label>
                                    </div>
                                    {(categoria?.imagen || formData.imagen) && (
                                        <div
                                            className="w-16 h-16 rounded-lg border border-border overflow-hidden flex-shrink-0">
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
                                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                    Jerarquía</h2>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-folder mr-2 text-muted-foreground"></i>
                                Categoría Padre
                                <span className="text-xs text-muted-foreground font-normal ml-2">(Opcional)</span>
                            </label>
                            <Select
                                options={[
                                    {
                                        value: '',
                                        label: 'Sin padre (Categoría Principal)',
                                        description: 'Nivel 1',
                                        icon: 'fa-solid fa-folder'
                                    },
                                    ...opcionesCategoriasPadre()
                                ]}
                                value={formData.categoria_padre || ''}
                                onChange={(value) => handleInputChange('categoria_padre', value || null)}
                                searchable
                                placeholder="Buscar categoría padre..."
                                className="w-full"
                            />

                            {formData.categoria_padre && getCategoriaPadreInfo() && (
                                <div
                                    className="mt-3 p-3 bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                                    <div
                                        className="flex items-center gap-2 text-sm text-purple-800 dark:text-purple-300">
                                        <i className="fa-solid fa-arrow-right"></i>
                                        <span>Esta será una subcategoría de:</span>
                                        <strong>{getCategoriaPadreInfo()?.nombre}</strong>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="mt-4 p-4 bg-muted/50 rounded-lg border border-border">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-10 h-10 bg-background rounded-lg flex items-center justify-center border border-border">
                                        <i className="fa-solid fa-layer-group text-muted-foreground"></i>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground">Nivel calculado</p>
                                        <p className="text-lg font-bold text-muted-foreground">Nivel {getNivelCalculado()}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-muted-foreground mb-1">Tipo</p>
                                    <span
                                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                                            getNivelCalculado() === 1
                                                ? 'bg-green-100 text-green-800 dark:bg-green-950/20 dark:text-green-400'
                                                : 'bg-purple-100 text-purple-800 dark:bg-purple-950/20 dark:text-purple-400'
                                        }`}>
                                        <i className={`fa-solid ${getNivelCalculado() === 1 ? 'fa-crown' : 'fa-folder'}`}></i>
                                        {getNivelCalculado() === 1 ? 'Principal' : 'Subcategoría'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Columna lateral */}
                <div className="space-y-6">

                    {/* NUEVA SECCIÓN: Gestión de Subcategorías */}
                    <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-folder-plus text-muted-foreground text-lg"></i>
                            </div>
                            <div>
                                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                    Subcategorías</h2>
                                <p className="text-xs text-muted-foreground">
                                    Agregar categorías hijas
                                    ({subcategoriasNuevas.length + subcategoriasExistentes.length} pendientes)
                                </p>
                            </div>
                        </div>

                        {/* Botones de acción */}
                        <div className="grid grid-cols-1 gap-3 mb-4">
                            <div>
                                <Select
                                    options={opcionesCategoriasPadre()}
                                    value=""
                                    onChange={agregarSubcategoriaExistente.toString}
                                    searchable
                                    placeholder="Enlazar existente..."
                                    className="w-full"
                                />
                            </div>
                            <button
                                type="button"
                                onClick={() => setShowModalSubcategoria(true)}
                                className="flex-1 px-4 py-2.5 text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                            >
                                <i className="fa-solid fa-plus mr-2"></i>
                                Nueva Subcategoría
                            </button>
                        </div>

                        {/* Lista de subcategorías nuevas */}
                        {subcategoriasNuevas.length > 0 && (
                            <div className="mb-4">
                                <p className="text-xs font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-sparkles mr-1"></i>
                                    Nuevas ({subcategoriasNuevas.length})
                                </p>
                                <div className="space-y-2">
                                    {subcategoriasNuevas.map(sub => (
                                        <div key={sub.id}
                                             className="flex items-center justify-between p-3 bg-muted/30 border rounded-lg">
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-foreground">{sub.nombre}</p>
                                                {sub.descripcion && (
                                                    <p className="text-xs text-muted-foreground">{sub.descripcion}</p>
                                                )}
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => eliminarSubcategoriaNueva(sub.id)}
                                                className="ml-2 p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-950/20 rounded-lg transition-all"
                                            >
                                                <i className="fa-solid fa-trash text-sm"></i>
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Lista de subcategorías existentes */}
                        {subcategoriasExistentes.length > 0 && (
                            <div>
                                <p className="text-xs font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-link mr-1"></i>
                                    Existentes ({subcategoriasExistentes.length})
                                </p>
                                <div className="space-y-2">
                                    {subcategoriasExistentes.map(id => (
                                        <div key={id}
                                             className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                            <p className="text-sm font-medium text-foreground">{getNombreCategoria(id)}</p>
                                            <button
                                                type="button"
                                                onClick={() => eliminarSubcategoriaExistente(id)}
                                                className="ml-2 p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-950/20 rounded-lg transition-all"
                                            >
                                                <i className="fa-solid fa-unlink text-sm"></i>
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {subcategoriasNuevas.length === 0 && subcategoriasExistentes.length === 0 && (
                            <div className="text-center py-8 text-muted-foreground">
                                <i className="fa-solid fa-folder-open text-4xl mb-3 opacity-20"></i>
                                <p className="text-sm">No hay subcategorías agregadas</p>
                                <p className="text-xs">Crea nuevas o enlaza existentes</p>
                            </div>
                        )}
                    </div>

                    {/* Resumen */}
                    {isEditMode && categoria && (
                        <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                    <i className="fa-solid fa-info-circle text-muted-foreground text-lg"></i>
                                </div>
                                <div>
                                    <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                        Información</h2>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div className="flex justify-between items-center py-2 border-b border-border">

                                    <span className="text-xs text-muted-foreground"><i
                                        className="fa-solid fa-barcode text-muted-foreground mr-2"></i>Código:</span>
                                    <span
                                        className="text-sm font-mono font-medium text-foreground">{categoria.codigo}</span>
                                </div>
                                <div className="flex justify-between items-center py-2 border-b border-border">
                                    <span className="text-xs text-muted-foreground"><i
                                        className="fa-solid fa-angles-up text-muted-foreground mr-2"></i>Nivel actual:</span>
                                    <span className="text-sm font-medium text-foreground">Nivel {categoria.nivel}</span>
                                </div>
                                {categoria?.subcategorias && categoria.subcategorias.length > 0 && (
                                    <div className="flex justify-between items-center py-2 border-b border-border">
                                        <span className="text-xs text-muted-foreground">Subcategorías:</span>
                                        <span
                                            className="text-sm font-medium text-foreground">{categoria.subcategorias.length}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Acciones */}
                    <div className="flex flex-col gap-3">
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"/>
                                    Guardando...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-save"/>
                                    {isEditMode ? 'Actualizar Categoría' : 'Crear Categoría'}
                                </>
                            )}
                        </button>
                        <button
                            type="button"
                            onClick={handleCancel}
                            disabled={loading}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-all disabled:opacity-50"
                        >
                            <i className="fa-solid fa-times"></i>
                            Cancelar
                        </button>
                    </div>
                </div>
            </form>

            {/* MODAL: Agregar Nueva Subcategoría */}
            {showModalSubcategoria && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div
                        className="bg-card rounded-xl border border-border shadow-2xl w-full max-w-lg mx-4 animate-in fade-in zoom-in duration-200">
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-border">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                                    <i className="fa-solid fa-folder-plus text-muted-foreground"></i>
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-muted-foreground">Nueva Subcategoría</h3>
                                    <p className="text-xs text-muted-foreground">Se creará al guardar la categoría
                                        principal</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => {
                                    setShowModalSubcategoria(false)
                                    setNuevaSubcategoria({nombre: '', descripcion: ''})
                                }}
                                className="p-2 hover:bg-muted rounded-lg transition-all"
                            >
                                <i className="fa-solid fa-times text-muted-foreground"></i>
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-tag mr-2"></i>
                                    Nombre de la Subcategoría *
                                </label>
                                <input
                                    type="text"
                                    value={nuevaSubcategoria.nombre}
                                    onChange={(e) => setNuevaSubcategoria(prev => ({...prev, nombre: e.target.value}))}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                                    placeholder={"Ej. Subcategoría A.1"}
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
                                    onChange={(e) => setNuevaSubcategoria(prev => ({
                                        ...prev,
                                        descripcion: e.target.value
                                    }))}
                                    rows={3}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
                                    placeholder="Descripción breve de la subcategoría..."
                                />
                            </div>

                            {/* Vista previa del nivel */}
                            <div
                                className="p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <i className="fa-solid fa-info-circle text-blue-600 dark:text-blue-400"></i>
                                    <div className="text-sm text-blue-800 dark:text-blue-300">
                                        <p className="font-medium">Esta subcategoría tendrá:</p>
                                        <p className="text-xs mt-1">
                                            • Nivel: <strong>{getNivelCalculado() + 1}</strong>
                                            <br/>
                                            •
                                            Padre: <strong>{formData.nombre || '(Nombre de categoría principal)'}</strong>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="flex gap-3 p-6 border-t border-border">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowModalSubcategoria(false)
                                    setNuevaSubcategoria({nombre: '', descripcion: ''})
                                }}
                                className="flex-1 px-4 py-2.5 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-all"
                            >
                                <i className="fa-solid fa-times mr-2"></i>
                                Cancelar
                            </button>
                            <button
                                type="button"
                                onClick={agregarSubcategoriaNueva}
                                className="flex-1 px-4 py-2.5 text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                            >
                                <i className="fa-solid fa-plus mr-2"></i>
                                Agregar Subcategoría
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
