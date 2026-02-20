"use client"

import {useState, useEffect, useMemo} from "react"
import {useRouter} from "next/navigation"
import {
    useProductos,
    useCategorias,
    useUnidadesMedida,
    useMarcas,
} from "@/src/core/store"
import {Producto, Componente, UnidadConversion} from "@/src/core/api/types"
import {mutate} from "swr"
import {Select} from "@/components/select/select-klyra"
import {alertas} from "@/components/alerts/alertas-toast"
import {CheckboxKlyra} from "@/components/ui/checkbox-klyra"
import {apiFetch, ApiError} from "@/src/core/api/client"

interface ProductoFormProps {
    mode: 'create' | 'edit'
    producto?: Producto | null
}

const TIPOS_PRODUCTO = [
    {value: 'simple', label: 'Producto Simple', icon: 'fa-solid fa-box'},
    {value: 'kit', label: 'Kit/Paquete', icon: 'fa-solid fa-boxes-stacked'},
    {value: 'servicio', label: 'Servicio', icon: 'fa-solid fa-screwdriver-wrench'},
]

const IVA_OPTIONS = [
    {value: true, label: 'Si', icon: 'fa-solid fa-percent'},
    {value: false, label: 'No', icon: 'fa-solid fa-ban'},
]

const PERECEDERO_OPTIONS = [
    {value: true, label: 'Si', icon: 'fa-solid fa-clock'},
    {value: false, label: 'No', icon: 'fa-solid fa-infinity'},
]

export function ProductoForm({mode, producto}: ProductoFormProps) {
    const router = useRouter()
    const isEditMode = mode === 'edit'

    const {data: productos} = useProductos()
    const {data: categoriasData} = useCategorias()
    const {data: unidadesMedidaData} = useUnidadesMedida()
    const {data: marcasData} = useMarcas()

    const [loading, setLoading] = useState(false)

    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: '',
        tipo: 'simple' as 'simple' | 'kit' | 'servicio',
        categoria_id: null as string | null,
        marca_id: null as string | null,
        unidad_medida_id: null as string | null,
        precio_compra: '',
        precio_venta: '',
        stock_minimo: '',
        iva: true,
        codigo_barras: '',
        es_perecedero: false,
        dias_vida_util: '',
        peso: '',
        es_kit: false,
    })

    const [imagen, setImagen] = useState<File | null>(null)
    const [componentes, setComponentes] = useState<Componente[]>([])
    const [searchProducto, setSearchProducto] = useState("")
    const [showProductoDropdown, setShowProductoDropdown] = useState(false)
    const [conversiones, setConversiones] = useState<UnidadConversion[]>([])

    const [nuevoComponente, setNuevoComponente] = useState({
        componente: null as string | null,
        cantidad: 1,
        es_opcional: false,
        observaciones: '',
    })

    const [nuevaConversion, setNuevaConversion] = useState({
        unidad_origen: null as string | null,
        unidad_destino: null as string | null,
        factor_conversion: '',
    })

    useEffect(() => {
        if (isEditMode && producto) {
            setFormData({
                nombre: producto.nombre || '',
                descripcion: producto.descripcion || '',
                tipo: producto.tipo as 'simple' | 'kit' | 'servicio',
                categoria_id: producto.categoria?.id || null,
                marca_id: producto.marca?.id || null,
                unidad_medida_id: producto.unidad_medida?.id || null,
                precio_compra: producto.precio_compra?.toString() || '',
                precio_venta: producto.precio_venta?.toString() || '',
                stock_minimo: producto.stock_minimo?.toString() || '',
                iva: producto.iva ?? true,
                codigo_barras: producto.codigo_barras || '',
                es_perecedero: producto.es_perecedero || false,
                dias_vida_util: producto.dias_vida_util?.toString() || '',
                peso: producto.peso?.toString() || '',
                es_kit: producto.es_kit || false,
            })

            if (producto.es_kit && producto.componentes) {
                setComponentes(producto.componentes.map((c: any, index: number) => ({
                    id: `temp-${index}`,
                    componente: c.componente,
                    cantidad: c.cantidad,
                    es_opcional: c.es_opcional,
                    observaciones: c.observaciones || '',
                    nombre: c.componente_nombre,
                    codigo: c.componente_codigo,
                    precio_venta: parseFloat(c.componente_precio || '0'),
                })))
            }

            if (producto.conversiones && producto.conversiones.length > 0) {
                setConversiones(producto.conversiones.map((c: any, index: number) => ({
                    id: `temp-${index}`,
                    unidad_origen: c.unidad_origen,
                    unidad_origen_nombre: c.unidad_origen_nombre,
                    unidad_destino: c.unidad_destino,
                    unidad_destino_nombre: c.unidad_destino_nombre,
                    factor_conversion: parseFloat(c.factor_conversion || '0'),
                })))
            }
        }
    }, [isEditMode, producto])

    const productosFiltrados = useMemo(() => {
        if (!productos || !searchProducto) return []
        const search = searchProducto.toLowerCase()
        return productos
            .filter((p) =>
                (p.codigo?.toLowerCase().includes(search) ||
                    p.nombre?.toLowerCase().includes(search)) &&
                p.id !== producto?.id
            )
            .slice(0, 10)
    }, [productos, searchProducto, producto?.id])

    const validarFormulario = () => {
        if (!formData.nombre.trim()) {
            alertas.warning('El nombre del producto es requerido', 'Campo Requerido')
            return false
        }
        const precioVenta = parseFloat(formData.precio_venta)
        if (!formData.precio_venta || isNaN(precioVenta) || precioVenta <= 0) {
            alertas.warning('El precio de venta debe ser mayor a 0', 'Campo Inválido')
            return false
        }
        if (formData.es_perecedero) {
            const diasVida = parseInt(formData.dias_vida_util)
            if (!formData.dias_vida_util || isNaN(diasVida) || diasVida <= 0) {
                alertas.warning('Los productos perecederos requieren días de vida útil', 'Campo Requerido')
                return false
            }
        }
        if (formData.tipo === 'kit' && componentes.length === 0) {
            alertas.warning('Los kits deben tener al menos un componente', 'Componentes Requeridos')
            return false
        }
        return true
    }

    const handleInputChange = (field: string, value: any) => {
        setFormData(prev => {
            const newData = {...prev, [field]: value}
            if (field === 'tipo') {
                newData.es_kit = value === 'kit'
            }
            if (field === 'es_perecedero' && !value) {
                newData.dias_vida_util = ''
            }
            return newData
        })
    }

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0]
            if (file.size > 5 * 1024 * 1024) {
                alertas.error('La imagen no debe superar los 5MB', 'Error de Tamaño')
                return
            }
            if (!file.type.startsWith('image/')) {
                alertas.error('Solo se permiten archivos de imagen', 'Error de Formato')
                return
            }
            setImagen(file)
        }
    }

    const agregarComponente = () => {
        if (!nuevoComponente.componente || nuevoComponente.cantidad <= 0) {
            alertas.warning('Seleccione un producto válido y una cantidad mayor a 0', 'Datos Inválidos')
            return
        }
        const prod = productos?.find(p => p.id === nuevoComponente.componente)
        if (!prod) return
        if (componentes.some(c => c.componente === nuevoComponente.componente)) {
            alertas.warning('Este producto ya fue agregado al kit', 'Componente Duplicado')
            return
        }
        setComponentes(prev => [...prev, {
            id: `temp-${Date.now()}`,
            componente: nuevoComponente.componente!,
            cantidad: nuevoComponente.cantidad,
            es_opcional: nuevoComponente.es_opcional,
            observaciones: nuevoComponente.observaciones,
            nombre: prod.nombre,
            codigo: prod.codigo,
            precio_venta: prod.precio_venta,
        }])
        setNuevoComponente({componente: null, cantidad: 1, es_opcional: false, observaciones: ''})
        setSearchProducto('')
        setShowProductoDropdown(false)
        alertas.success('Componente agregado al kit', 'Éxito')
    }

    const eliminarComponente = (id: string) => {
        setComponentes(prev => prev.filter(c => c.id !== id))
    }

    const agregarConversion = () => {
        if (!nuevaConversion.unidad_origen || !nuevaConversion.unidad_destino) {
            alertas.warning('Seleccione ambas unidades de medida', 'Datos Incompletos')
            return
        }
        if (nuevaConversion.unidad_origen === nuevaConversion.unidad_destino) {
            alertas.warning('Las unidades origen y destino no pueden ser iguales', 'Error de Validación')
            return
        }
        const factor = parseFloat(nuevaConversion.factor_conversion)
        if (!nuevaConversion.factor_conversion || isNaN(factor) || factor <= 0) {
            alertas.warning('El factor de conversión debe ser mayor a 0', 'Factor Inválido')
            return
        }
        if (conversiones.some(c =>
            String(c.unidad_origen) === nuevaConversion.unidad_origen &&
            String(c.unidad_destino) === nuevaConversion.unidad_destino
        )) {
            alertas.warning('Esta conversión ya fue agregada', 'Conversión Duplicada')
            return
        }
        const unidadOrigen = unidadesMedidaData.find(u => String(u.id) === nuevaConversion.unidad_origen)
        const unidadDestino = unidadesMedidaData.find(u => String(u.id) === nuevaConversion.unidad_destino)
        if (!unidadOrigen || !unidadDestino) return

        setConversiones(prev => [...prev, {
            id: `temp-${Date.now()}`,
            unidad_origen: Number(nuevaConversion.unidad_origen),
            unidad_origen_nombre: `${unidadOrigen.nombre} (${unidadOrigen.abreviatura})`,
            unidad_destino: Number(nuevaConversion.unidad_destino),
            unidad_destino_nombre: `${unidadDestino.nombre} (${unidadDestino.abreviatura})`,
            factor_conversion: factor,
        }])
        setNuevaConversion({unidad_origen: null, unidad_destino: null, factor_conversion: ''})
        alertas.success('Conversión agregada exitosamente', 'Éxito')
    }

    const eliminarConversion = (id: string) => {
        setConversiones(prev => prev.filter(c => c.id !== id))
        alertas.info('Conversión eliminada', 'Eliminada')
    }

    const calcularCostoKit = () =>
        componentes.reduce((total, comp) => total + ((comp.precio_venta || 0) * comp.cantidad), 0)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (loading) return
        if (!validarFormulario()) return

        setLoading(true)

        try {
            // Payload JSON (sin imagen, sin stock)
            const payload: Record<string, any> = {
                nombre: formData.nombre,
                descripcion: formData.descripcion,
                tipo: formData.tipo,
                es_kit: formData.es_kit,
                precio_venta: parseFloat(formData.precio_venta),
                precio_compra: parseFloat(formData.precio_compra || '0'),
                stock_minimo: parseFloat(formData.stock_minimo || '0'),
                iva: formData.iva,
                es_perecedero: formData.es_perecedero,
            }

            if (formData.categoria_id)    payload.categoria_id    = formData.categoria_id
            if (formData.marca_id)        payload.marca_id        = formData.marca_id
            if (formData.unidad_medida_id) payload.unidad_medida_id = formData.unidad_medida_id
            if (formData.codigo_barras)   payload.codigo_barras   = formData.codigo_barras
            if (formData.dias_vida_util)  payload.dias_vida_util  = parseInt(formData.dias_vida_util)
            if (formData.peso)            payload.peso            = parseFloat(formData.peso)

            if (formData.tipo === 'kit' && componentes.length > 0) {
                payload.componentes_data = componentes.map(c => ({
                    componente: c.componente,
                    cantidad: c.cantidad,
                    es_opcional: c.es_opcional,
                    observaciones: c.observaciones || '',
                }))
            }

            if (conversiones.length > 0) {
                payload.conversiones_data = conversiones.map(c => ({
                    unidad_origen: c.unidad_origen,
                    unidad_destino: c.unidad_destino,
                    factor_conversion: c.factor_conversion,
                }))
            }

            const respuesta = await apiFetch<{id: string}>(
                isEditMode ? `/api/productos/${producto?.id}/` : '/api/productos/',
                {
                    method: isEditMode ? 'PATCH' : 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload),
                }
            )

            // Subir imagen por separado si existe
            if (imagen) {
                const productoId = isEditMode ? producto?.id : respuesta.id
                const formDataImg = new FormData()
                formDataImg.append('imagen', imagen)
                await apiFetch(`/api/productos/${productoId}/agregar_imagen/`, {
                    method: 'POST',
                    body: formDataImg,
                })
            }

            alertas.success(
                isEditMode ? 'El producto ha sido actualizado exitosamente' : 'El producto ha sido creado exitosamente',
                isEditMode ? 'Producto Actualizado' : 'Producto Creado'
            )

            await mutate(['/api/productos/'])
            setTimeout(() => router.push('/inventario/productos'), 1500)

        } catch (error) {
            if (error instanceof ApiError) {
                alertas.error(error.mensaje, error.titulo)
            } else {
                alertas.error(
                    'Error desconocido al guardar el producto',
                    isEditMode ? 'Error al Actualizar' : 'Error al Crear'
                )
            }
        } finally {
            setLoading(false)
        }
    }

    const handleCancel = () => router.push('/inventario/productos')

    return (
        <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
                {/* Información básica */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-folder-tree text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información Básica</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-tag mr-2"></i>Nombre *
                                </label>
                                <input
                                    type="text"
                                    value={formData.nombre}
                                    onChange={(e) => handleInputChange('nombre', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="Ej: Producto A"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-barcode mr-1"></i>Código de Barras
                                </label>
                                <input
                                    type="text"
                                    value={formData.codigo_barras}
                                    onChange={(e) => handleInputChange('codigo_barras', e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="7801234567890"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-align-left mr-1"></i>Descripción
                            </label>
                            <textarea
                                value={formData.descripcion}
                                onChange={(e) => handleInputChange('descripcion', e.target.value)}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Descripción detallada del producto..."
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-box mr-1"></i>Tipo de Producto *
                                </label>
                                <Select
                                    options={TIPOS_PRODUCTO.map(t => ({value: t.value, label: t.label}))}
                                    value={formData.tipo}
                                    onChange={(value) => handleInputChange('tipo', value)}
                                    placeholder="Seleccionar tipo"
                                    className="w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-percent mr-1"></i>Aplica IVA
                                </label>
                                <div className="flex gap-2">
                                    {IVA_OPTIONS.map((option) => (
                                        <button
                                            key={String(option.value)}
                                            type="button"
                                            onClick={() => handleInputChange('iva', option.value)}
                                            className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                                formData.iva === option.value
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                                            }`}
                                        >
                                            {option.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Precios y Stock */}
                <div className="bg-card rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-money-bill-wave text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Precios y Stock</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-cart-shopping mr-1"></i>Precio Compra
                            </label>
                            <input
                                type="number"
                                value={formData.precio_compra}
                                onChange={(e) => handleInputChange('precio_compra', e.target.value)}
                                min="0"
                                step="0.01"
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="0.00"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-tag mr-1"></i>Precio Venta *
                            </label>
                            <input
                                type="number"
                                value={formData.precio_venta}
                                onChange={(e) => handleInputChange('precio_venta', e.target.value)}
                                min="0.01"
                                step="0.01"
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="0.00"
                                required
                            />
                            {formData.precio_venta && parseFloat(formData.precio_venta) <= 0 && (
                                <p className="text-xs text-red-500 mt-1">El precio debe ser mayor a 0</p>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-exclamation-triangle mr-1"></i>Stock Mínimo
                            </label>
                            <input
                                type="number"
                                value={formData.stock_minimo}
                                onChange={(e) => handleInputChange('stock_minimo', e.target.value)}
                                min="0"
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="0"
                            />
                        </div>
                    </div>
                </div>

                {/* Características adicionales */}
                <div className="bg-card rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-sliders text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Características Adicionales</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-clock mr-1"></i>Es Perecedero
                                </label>
                                <div className="flex gap-2">
                                    {PERECEDERO_OPTIONS.map((option) => (
                                        <button
                                            key={String(option.value)}
                                            type="button"
                                            onClick={() => handleInputChange('es_perecedero', option.value)}
                                            className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                                formData.es_perecedero === option.value
                                                    ? "bg-primary text-primary-foreground"
                                                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                                            }`}
                                        >
                                            {option.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            {formData.es_perecedero && (
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-calendar-day mr-1"></i>Días de Vida Útil *
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.dias_vida_util}
                                        onChange={(e) => handleInputChange('dias_vida_util', e.target.value)}
                                        min="1"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        placeholder="30"
                                        required={formData.es_perecedero}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-weight-hanging mr-1"></i>Peso (kg)
                                </label>
                                <input
                                    type="number"
                                    value={formData.peso}
                                    onChange={(e) => handleInputChange('peso', e.target.value)}
                                    min="0"
                                    step="0.001"
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="0.000"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-image mr-1"></i>Imagen del Producto
                                </label>
                                <input
                                    type="file"
                                    onChange={handleImageChange}
                                    accept="image/*"
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Conversiones de Unidad */}
                <div className="bg-card rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-exchange-alt text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Conversiones de Unidad</h2>
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
                        <div className="flex gap-2 text-blue-800 dark:text-blue-300">
                            <i className="fa-solid fa-info-circle mt-0.5"></i>
                            <div className="text-xs">
                                <p className="font-medium mb-1">¿Para qué sirven las conversiones?</p>
                                <p>Permiten vender/comprar el producto en diferentes unidades de medida.</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-muted/50 rounded-lg p-4 mb-4">
                        <h3 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                            <i className="fa-solid fa-plus"></i>Agregar Conversión
                        </h3>
                        <div className="space-y-3">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-arrow-right mr-1"></i>Unidad Origen *
                                    </label>
                                    <Select
                                        options={unidadesMedidaData.map(u => ({
                                            value: u.id,
                                            label: `${u.nombre} (${u.abreviatura})`,
                                            description: u.tipo
                                        }))}
                                        value={nuevaConversion.unidad_origen || ''}
                                        onChange={(value) => setNuevaConversion(prev => ({...prev, unidad_origen: value || null}))}
                                        searchable
                                        placeholder="Ej: Galón"
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-arrow-left mr-1"></i>Unidad Destino *
                                    </label>
                                    <Select
                                        options={unidadesMedidaData.map(u => ({
                                            value: u.id,
                                            label: `${u.nombre} (${u.abreviatura})`,
                                            description: u.tipo
                                        }))}
                                        value={nuevaConversion.unidad_destino || ''}
                                        onChange={(value) => setNuevaConversion(prev => ({...prev, unidad_destino: value || null}))}
                                        searchable
                                        placeholder="Ej: Litro"
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-calculator mr-1"></i>Factor *
                                    </label>
                                    <input
                                        type="number"
                                        value={nuevaConversion.factor_conversion}
                                        onChange={(e) => setNuevaConversion(prev => ({...prev, factor_conversion: e.target.value}))}
                                        min="0.0001"
                                        step="0.0001"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        placeholder="Ej: 3.785"
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">1 origen = X destino</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={agregarConversion}
                                className="flex items-center justify-center gap-2 px-4 py-2 bg-primary/10 text-primary border border-primary/20 rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors w-full"
                            >
                                <i className="fa-solid fa-plus"></i>Agregar Conversión
                            </button>
                        </div>
                    </div>

                    {conversiones.length > 0 ? (
                        <div className="space-y-2">
                            <span className="text-sm font-medium text-foreground">
                                Conversiones configuradas ({conversiones.length})
                            </span>
                            {conversiones.map((conversion) => (
                                <div key={conversion.id} className="flex items-center justify-between p-3 bg-muted/30 border rounded-lg">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 text-sm">
                                            <span className="font-medium text-primary">1 {conversion.unidad_origen_nombre}</span>
                                            <i className="fa-solid fa-equals text-muted-foreground text-xs"></i>
                                            <span className="font-medium text-green-600">{conversion.factor_conversion} {conversion.unidad_destino_nombre}</span>
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => eliminarConversion(conversion.id)}
                                        className="ml-4 p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors"
                                    >
                                        <i className="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <i className="fa-solid fa-exchange-alt text-3xl mb-2 opacity-50"></i>
                            <p className="text-sm">No hay conversiones configuradas</p>
                        </div>
                    )}
                </div>

                {/* Componentes del Kit */}
                {formData.tipo === 'kit' && (
                    <div className="bg-card rounded-xl border border-border p-6">
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                                <i className="fa-solid fa-boxes-stacked text-muted-foreground text-lg"></i>
                            </div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Componentes del Kit</h2>
                        </div>

                        <div className="bg-muted/50 rounded-lg p-4 mb-4">
                            <h3 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                                <i className="fa-solid fa-plus"></i>Agregar Componente
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-box mr-1"></i>Buscar Producto *
                                    </label>
                                    <div className="relative">
                                        <input
                                            type="text"
                                            value={searchProducto}
                                            onChange={(e) => {setSearchProducto(e.target.value); setShowProductoDropdown(true)}}
                                            onFocus={() => setShowProductoDropdown(true)}
                                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                            placeholder="Buscar por código o nombre..."
                                        />
                                        {showProductoDropdown && productosFiltrados.length > 0 && (
                                            <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-60 overflow-auto">
                                                {productosFiltrados.map((prod) => (
                                                    <button
                                                        key={prod.id}
                                                        type="button"
                                                        onClick={() => {
                                                            setNuevoComponente(prev => ({...prev, componente: prod.id}))
                                                            setSearchProducto(`${prod.codigo} - ${prod.nombre}`)
                                                            setShowProductoDropdown(false)
                                                        }}
                                                        className="w-full px-4 py-2 text-left hover:bg-muted text-sm border-b border-border last:border-b-0"
                                                    >
                                                        <div className="font-medium">{prod.codigo}</div>
                                                        <div className="text-muted-foreground text-xs truncate">{prod.nombre}</div>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                                            <i className="fa-solid fa-hashtag mr-1"></i>Cantidad *
                                        </label>
                                        <input
                                            type="number"
                                            value={nuevoComponente.cantidad}
                                            onChange={(e) => setNuevoComponente(prev => ({...prev, cantidad: parseFloat(e.target.value) || 1}))}
                                            min="0.01"
                                            step="0.01"
                                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                                            <i className="fa-solid fa-circle-question mr-1"></i>Opcional
                                        </label>
                                        <div className="flex items-center h-10">
                                            <CheckboxKlyra
                                                className="w-full justify-center"
                                                checked={nuevoComponente.es_opcional}
                                                onChange={(checked) => setNuevoComponente(prev => ({...prev, es_opcional: checked}))}
                                                label="Opcional"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                                            <i className="fa-solid fa-note-sticky mr-1"></i>Observaciones
                                        </label>
                                        <input
                                            type="text"
                                            value={nuevoComponente.observaciones}
                                            onChange={(e) => setNuevoComponente(prev => ({...prev, observaciones: e.target.value}))}
                                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                            placeholder="Notas adicionales..."
                                        />
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={agregarComponente}
                                    className="flex items-center justify-center gap-2 px-4 py-2 bg-primary/10 text-primary border border-primary/20 rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
                                >
                                    <i className="fa-solid fa-plus"></i>Agregar al Kit
                                </button>
                            </div>
                        </div>

                        {componentes.length > 0 ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-foreground">Componentes ({componentes.length})</span>
                                    <span className="text-sm text-muted-foreground">Costo total: ${calcularCostoKit().toFixed(2)}</span>
                                </div>
                                {componentes.map((componente) => (
                                    <div key={componente.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-medium">{componente.codigo}</span>
                                                {componente.es_opcional && (
                                                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full">Opcional</span>
                                                )}
                                            </div>
                                            <div className="text-sm text-muted-foreground">{componente.nombre}</div>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                Cantidad: {componente.cantidad} × ${componente.precio_venta} = ${(componente.cantidad * (componente.precio_venta || 0)).toFixed(2)}
                                                {componente.observaciones && ` • ${componente.observaciones}`}
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => eliminarComponente(componente.id)}
                                            className="ml-4 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                        >
                                            <i className="fa-solid fa-trash"></i>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                <i className="fa-solid fa-box-open text-3xl mb-2"></i>
                                <p className="text-sm">No hay componentes agregados</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Columna lateral */}
            <div className="space-y-6">
                {/* Relaciones */}
                <div className="bg-card rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-link text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Relaciones</h2>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-folder mr-1"></i>Categoría
                            </label>
                            <Select
                                options={[
                                    {value: '', label: 'Sin categoría'},
                                    ...categoriasData.map(c => ({value: c.id, label: c.nombre}))
                                ]}
                                value={formData.categoria_id || ''}
                                onChange={(value) => handleInputChange('categoria_id', value || null)}
                                searchable
                                placeholder="Seleccionar categoría"
                                className="w-full"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-copyright mr-1"></i>Marca
                            </label>
                            <Select
                                options={[
                                    {value: '', label: 'Sin marca'},
                                    ...marcasData.map(m => ({value: m.id, label: m.nombre, description: m.codigo}))
                                ]}
                                value={formData.marca_id || ''}
                                onChange={(value) => handleInputChange('marca_id', value || null)}
                                searchable
                                placeholder="Seleccionar marca"
                                className="w-full"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-ruler mr-1"></i>Unidad de Medida
                            </label>
                            <Select
                                options={[
                                    {value: '', label: 'Seleccionar unidad'},
                                    ...unidadesMedidaData.map(u => ({
                                        value: u.id,
                                        label: `${u.nombre} (${u.abreviatura})`,
                                        description: u.tipo
                                    }))
                                ]}
                                value={formData.unidad_medida_id || ''}
                                onChange={(value) => handleInputChange('unidad_medida_id', value || null)}
                                searchable
                                placeholder="Seleccionar unidad"
                                className="w-full"
                            />
                        </div>
                    </div>
                </div>

                {/* Resumen */}
                <div className="bg-card rounded-xl border border-border p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-clipboard-check text-muted-foreground text-lg"></i>
                        </div>
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Resumen</h2>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-border">
                            <span className="text-sm text-muted-foreground">Tipo:</span>
                            <span className="text-sm font-medium capitalize">{formData.tipo}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-border">
                            <span className="text-sm text-muted-foreground">IVA:</span>
                            <span className="text-sm font-medium">{formData.iva ? 'Sí' : 'No'}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-border">
                            <span className="text-sm text-muted-foreground">Perecedero:</span>
                            <span className="text-sm font-medium">{formData.es_perecedero ? 'Sí' : 'No'}</span>
                        </div>
                        {formData.precio_venta && (
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-sm text-muted-foreground">Precio Venta:</span>
                                <span className="text-sm font-medium">${parseFloat(formData.precio_venta).toFixed(2)}</span>
                            </div>
                        )}
                        {formData.tipo === 'kit' && componentes.length > 0 && (
                            <>
                                <div className="flex justify-between items-center py-2 border-b border-border">
                                    <span className="text-sm text-muted-foreground">Componentes:</span>
                                    <span className="text-sm font-medium">{componentes.length}</span>
                                </div>
                                <div className="flex justify-between items-center py-2 border-b border-border">
                                    <span className="text-sm text-muted-foreground">Costo Kit:</span>
                                    <span className="text-sm font-medium">${calcularCostoKit().toFixed(2)}</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Acciones */}
                <div className="flex flex-col gap-3">
                    <button
                        type="button"
                        onClick={handleCancel}
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                    >
                        <i className="fa-solid fa-times"></i>Cancelar
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? (
                            <><i className="fa-solid fa-spinner fa-spin"/>Guardando...</>
                        ) : (
                            <><i className="fa-solid fa-save"/>Guardar Producto</>
                        )}
                    </button>
                </div>
            </div>
        </form>
    )
}