// src/modules/inventario/forms/movimiento-form.tsx

"use client"

import React, { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useStore, useBodegas, useProductos } from "@/src/core/store"
import { Select } from "@/components/select/select-klyra"
import { alertas } from "@/components/alerts/alertas-toast"
import type { Producto } from "@/src/core/api/types"

interface MovimientoFormProps {
    tipo: 'entrada' | 'salida' | 'transferencia'
    bodegaIdInicial?: string
    productoIdInicial?: string
    formRef?: React.RefObject<HTMLFormElement>
}

interface DetalleProducto {
    id: string
    producto: Producto
    cantidad: number
    costo_unitario?: number
    lote?: string
    observaciones?: string
}

export function MovimientoForm({ tipo, bodegaIdInicial, productoIdInicial, formRef }: MovimientoFormProps) {
    const router = useRouter()
    const { data: bodegas, isLoading: loadingBodegas } = useBodegas()
    const { data: productos, isLoading: loadingProductos } = useProductos()

    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        bodega_destino: tipo === 'entrada' ? (bodegaIdInicial || '') : '',
        bodega_origen: tipo === 'salida' ? (bodegaIdInicial || '') : tipo === 'transferencia' ? (bodegaIdInicial || '') : '',
        referencia: '',
        observaciones: ''
    })

    const [detalles, setDetalles] = useState<DetalleProducto[]>([])
    const [productoSeleccionado, setProductoSeleccionado] = useState('')
    const [cantidadNueva, setCantidadNueva] = useState('')
    const [costoUnitario, setCostoUnitario] = useState('')
    const [lote, setLote] = useState('')

    // Pre-cargar producto si viene en los parámetros
    useEffect(() => {
        if (productoIdInicial && productos && productos.length > 0) {
            const producto = productos.find(p => p.id === productoIdInicial)
            if (producto) {
                agregarProductoInicial(producto)
            }
        }
    }, [productoIdInicial, productos])

    const agregarProductoInicial = (producto: Producto) => {
        if (!detalles.find(d => d.producto.id === producto.id)) {
            setDetalles([{
                id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                producto,
                cantidad: 1,
                costo_unitario: tipo === 'entrada' ? Number(producto.precio_compra) : undefined,
                lote: '',
                observaciones: ''
            }])
        }
    }

    const agregarProducto = () => {
        if (!productoSeleccionado) {
            alertas.warning('Selecciona un producto', 'Campo requerido')
            return
        }

        if (!cantidadNueva || Number(cantidadNueva) <= 0) {
            alertas.warning('Ingresa una cantidad válida', 'Campo requerido')
            return
        }

        // Verificar que no esté ya agregado
        if (detalles.find(d => d.producto.id === productoSeleccionado)) {
            alertas.warning('Este producto ya está en la lista', 'Producto duplicado')
            return
        }

        const producto = productos?.find(p => p.id === productoSeleccionado)
        if (!producto) return

        // Para salidas, verificar stock disponible
        if (tipo === 'salida' && formData.bodega_origen) {
            // Aquí podrías agregar validación de stock si tienes esa info
            // Por ahora el backend lo validará
        }

        const nuevoDetalle: DetalleProducto = {
            id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            producto,
            cantidad: Number(cantidadNueva),
            costo_unitario: tipo === 'entrada' && costoUnitario ? Number(costoUnitario) : undefined,
            lote: lote.trim() || undefined,
            observaciones: ''
        }

        setDetalles([...detalles, nuevoDetalle])

        // Limpiar campos
        setProductoSeleccionado('')
        setCantidadNueva('')
        setCostoUnitario('')
        setLote('')
    }

    const eliminarProducto = (id: string) => {
        setDetalles(detalles.filter(d => d.id !== id))
    }

    const actualizarDetalle = (id: string, campo: keyof DetalleProducto, valor: any) => {
        setDetalles(detalles.map(d =>
            d.id === id ? { ...d, [campo]: valor } : d
        ))
    }

    const validarFormulario = () => {
        // Validar bodega destino para entradas
        if (tipo === 'entrada' && !formData.bodega_destino) {
            alertas.warning('Selecciona una bodega de destino', 'Campo requerido')
            return false
        }

        // Validar bodega origen para salidas
        if (tipo === 'salida' && !formData.bodega_origen) {
            alertas.warning('Selecciona una bodega de origen', 'Campo requerido')
            return false
        }

        // Validar bodegas para transferencias
        if (tipo === 'transferencia') {
            if (!formData.bodega_origen) {
                alertas.warning('Selecciona una bodega de origen', 'Campo requerido')
                return false
            }
            if (!formData.bodega_destino) {
                alertas.warning('Selecciona una bodega de destino', 'Campo requerido')
                return false
            }
            if (formData.bodega_origen === formData.bodega_destino) {
                alertas.warning('Las bodegas de origen y destino deben ser diferentes', 'Error de validación')
                return false
            }
        }

        // Validar que haya al menos un producto
        if (detalles.length === 0) {
            alertas.warning('Debes agregar al menos un producto', 'Sin productos')
            return false
        }

        // Validar cantidades
        for (const detalle of detalles) {
            if (detalle.cantidad <= 0) {
                alertas.warning(`La cantidad para ${detalle.producto.nombre} debe ser mayor a 0`, 'Cantidad inválida')
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
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

            // Preparar payload según el tipo
            const payload: any = {
                referencia: formData.referencia.trim() || undefined,
                observaciones: formData.observaciones.trim() || undefined,
                detalles_data: detalles.map(d => ({
                    producto: d.producto.id,
                    cantidad: d.cantidad,
                    costo_unitario: d.costo_unitario,
                    lote: d.lote,
                    observaciones: d.observaciones
                }))
            }

            // Agregar campos específicos según tipo
            if (tipo === 'entrada') {
                payload.bodega_destino = formData.bodega_destino
            } else if (tipo === 'salida') {
                payload.bodega_origen = formData.bodega_origen
            } else if (tipo === 'transferencia') {
                payload.bodega_origen = formData.bodega_origen
                payload.bodega_destino = formData.bodega_destino
            }

            // Endpoint según tipo
            const endpoints = {
                entrada: '/api/movimientos-inventario/crear-entrada/',
                salida: '/api/movimientos-inventario/crear-salida/',
                transferencia: '/api/movimientos-inventario/crear-transferencia/'
            }

            const response = await fetch(`${API_BASE_URL}${endpoints[tipo]}`, {
                method: 'POST',
                credentials: 'include',
                body: JSON.stringify(payload),
            })

            if (!response.ok) {
                const data = await response.json().catch(() => ({}))
                throw new Error(
                    data.error ||
                    data.message ||
                    data.detail ||
                    'Error al registrar movimiento'
                )
            }

            const resultado = await response.json()

            alertas.success(
                resultado.message || 'Movimiento registrado exitosamente',
                'Éxito'
            )

            setTimeout(() => {
                router.push('/inventario/movimientos')
            }, 1500)

        } catch (error: any) {
            const mensaje = error.message || 'Error desconocido al registrar movimiento'
            alertas.error(mensaje, 'Error')
        } finally {
            setLoading(false)
        }
    }

    const handleCancel = () => {
        router.push('/inventario/movimientos')
    }

    return (
        <form ref={formRef} onSubmit={handleSubmit} className="grid grid-cols-1 gap-6">
            <div className="lg:col-span-2 space-y-6">
                {/* Información de Bodegas */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-warehouse text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información
                                de Bodegas</h2>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {/* Bodega Origen (Salida y Transferencia) */}
                        {(tipo === 'salida' || tipo === 'transferencia') && (
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-warehouse mr-1"></i>
                                    Bodega de Origen *
                                </label>
                                <Select
                                    options={bodegas?.map(b => ({
                                        value: b.id,
                                        label: b.nombre,
                                        description: b.codigo
                                    })) || []}
                                    value={formData.bodega_origen}
                                    onChange={(value) => setFormData(prev => ({
                                        ...prev,
                                        bodega_origen: value.toString()
                                    }))}
                                    searchable
                                    placeholder="Seleccionar bodega"
                                    className="w-full"
                                    disabled={loadingBodegas}
                                />
                            </div>
                        )}

                        {/* Bodega Destino (Entrada y Transferencia) */}
                        {(tipo === 'entrada' || tipo === 'transferencia') && (
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-warehouse mr-1"></i>
                                    Bodega de Destino *
                                </label>
                                <Select
                                    options={bodegas?.map(b => ({
                                        value: b.id,
                                        label: b.nombre,
                                        description: b.codigo
                                    })) || []}
                                    value={formData.bodega_destino}
                                    onChange={(value) => setFormData(prev => ({
                                        ...prev,
                                        bodega_destino: value.toString()
                                    }))}
                                    searchable
                                    placeholder="Seleccionar bodega"
                                    className="w-full"
                                    disabled={loadingBodegas}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Información Adicional */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-file-lines text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Información
                                Adicional</h2>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-hashtag mr-1"></i>
                                Referencia
                                <span className="text-xs font-normal text-muted-foreground ml-2">(Opcional)</span>
                            </label>
                            <input
                                type="text"
                                value={formData.referencia}
                                onChange={(e) => setFormData(prev => ({...prev, referencia: e.target.value}))}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Ej: FACT-001, OC-123"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-muted-foreground mb-2">
                                <i className="fa-solid fa-comment mr-1"></i>
                                Observaciones
                                <span className="text-xs font-normal text-muted-foreground ml-2">(Opcional)</span>
                            </label>
                            <input
                                type="text"
                                value={formData.observaciones}
                                onChange={(e) => setFormData(prev => ({...prev, observaciones: e.target.value}))}
                                className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                placeholder="Observaciones generales del movimiento"
                            />
                        </div>
                    </div>
                </div>

                {/* Agregar Productos */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-box text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Agregar
                                Productos</h2>
                        </div>
                    </div>

                    <div className="bg-muted/50 rounded-lg p-4 mb-4">
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                            <div className="md:col-span-4">
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-search mr-1"></i>
                                    Producto *
                                </label>
                                <Select
                                    options={productos?.filter(p => !detalles.find(d => d.producto.id === p.id)).map(p => ({
                                        value: p.id,
                                        label: p.nombre,
                                        description: `${p.codigo} - Stock: ${p.stock_total}`
                                    })) || []}
                                    value={productoSeleccionado}
                                    onChange={(value) => setProductoSeleccionado(value.toString())}
                                    searchable
                                    placeholder="Buscar producto"
                                    className="w-full"
                                    disabled={loadingProductos}
                                />
                            </div>

                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-hashtag mr-1"></i>
                                    Cantidad *
                                </label>
                                <input
                                    type="number"
                                    value={cantidadNueva}
                                    onChange={(e) => setCantidadNueva(e.target.value)}
                                    min="1"
                                    step="1"
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="0"
                                />
                            </div>

                            {tipo === 'entrada' && (
                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-muted-foreground mb-2">
                                        <i className="fa-solid fa-dollar-sign mr-1"></i>
                                        Costo Unit.
                                    </label>
                                    <input
                                        type="number"
                                        value={costoUnitario}
                                        onChange={(e) => setCostoUnitario(e.target.value)}
                                        min="0"
                                        step="0.01"
                                        className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        placeholder="0.00"
                                    />
                                </div>
                            )}

                            <div className={tipo === 'entrada' ? 'md:col-span-2' : 'md:col-span-4'}>
                                <label className="block text-sm font-medium text-muted-foreground mb-2">
                                    <i className="fa-solid fa-barcode mr-1"></i>
                                    Lote/Serie
                                </label>
                                <input
                                    type="text"
                                    value={lote}
                                    onChange={(e) => setLote(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                    placeholder="Opcional"
                                />
                            </div>

                            <div className="md:col-span-2 flex items-end">
                                <button
                                    type="button"
                                    onClick={agregarProducto}
                                    className="w-full px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                                >
                                    <i className="fa-solid fa-plus"></i>
                                    Agregar
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Lista de Productos */}
                    {detalles.length > 0 ? (
                        <div className="border border-border rounded-lg overflow-hidden">
                            <div className="bg-muted/50 px-4 py-3 border-b">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
                                        <i className="fa-solid fa-list"></i>
                                        Productos agregados
                                    </h3>
                                    <span className="text-sm font-medium text-primary">
                                        {detalles.length} {detalles.length === 1 ? 'producto' : 'productos'}
                                    </span>
                                </div>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                    <tr className="border-b bg-muted/20">
                                        <th className="text-left px-4 py-3 font-medium text-muted-foreground">Producto</th>
                                        <th className="text-center px-4 py-3 font-medium text-muted-foreground w-32">Cantidad</th>
                                        {tipo === 'entrada' && (
                                            <th className="text-center px-4 py-3 font-medium text-muted-foreground w-32">Costo
                                                Unit.</th>
                                        )}
                                        <th className="text-left px-4 py-3 font-medium text-muted-foreground w-40">Lote</th>
                                        <th className="text-center px-4 py-3 font-medium text-muted-foreground w-20">Acción</th>
                                    </tr>
                                    </thead>
                                    <tbody>
                                    {detalles.map((detalle) => (
                                        <tr key={detalle.id} className="border-b hover:bg-muted/30 transition-colors">
                                            <td className="px-4 py-3">
                                                <div>
                                                    <p className="font-medium text-foreground">{detalle.producto.nombre}</p>
                                                    <p className="text-xs text-muted-foreground font-mono">{detalle.producto.codigo}</p>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <input
                                                    type="number"
                                                    value={detalle.cantidad}
                                                    onChange={(e) => actualizarDetalle(detalle.id, 'cantidad', Number(e.target.value))}
                                                    min="1"
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-center text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                                />
                                            </td>
                                            {tipo === 'entrada' && (
                                                <td className="px-4 py-3">
                                                    <input
                                                        type="number"
                                                        value={detalle.costo_unitario || ''}
                                                        onChange={(e) => actualizarDetalle(detalle.id, 'costo_unitario', e.target.value ? Number(e.target.value) : undefined)}
                                                        min="0"
                                                        step="0.01"
                                                        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-center text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                                        placeholder="0.00"
                                                    />
                                                </td>
                                            )}
                                            <td className="px-4 py-3">
                                                <input
                                                    type="text"
                                                    value={detalle.lote || ''}
                                                    onChange={(e) => actualizarDetalle(detalle.id, 'lote', e.target.value)}
                                                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                                    placeholder="-"
                                                />
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                <button
                                                    type="button"
                                                    onClick={() => eliminarProducto(detalle.id)}
                                                    className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-950/20 rounded-lg transition-colors"
                                                    title="Eliminar producto"
                                                >
                                                    <i className="fa-solid fa-trash text-sm"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <i className="fa-solid fa-box-open text-4xl mb-3 opacity-20"></i>
                            <p className="text-sm">No hay productos agregados</p>
                            <p className="text-xs mt-1">Busca y agrega productos al movimiento</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Columna lateral */}
            <div className="space-y-6">
                {/* Resumen */}
                <div className="bg-card rounded-xl border border-border shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <i className="fa-solid fa-clipboard-check text-muted-foreground text-lg"></i>
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Resumen</h2>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-border">
                            <span className="text-sm text-muted-foreground">Tipo:</span>
                            <span className="text-sm font-medium capitalize">{tipo}</span>
                        </div>

                        {formData.bodega_origen && (
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-sm text-muted-foreground">Bodega Origen:</span>
                                <span
                                    className="text-sm font-medium">{bodegas?.find(b => b.id === formData.bodega_origen)?.nombre}</span>
                            </div>
                        )}

                        {formData.bodega_destino && (
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-sm text-muted-foreground">Bodega Destino:</span>
                                <span
                                    className="text-sm font-medium">{bodegas?.find(b => b.id === formData.bodega_destino)?.nombre}</span>
                            </div>
                        )}

                        <div className="flex justify-between items-center py-2 border-b border-border">
                            <span className="text-sm text-muted-foreground">Productos:</span>
                            <span className="text-sm font-medium">{detalles.length}</span>
                        </div>

                        {tipo === 'entrada' && detalles.length > 0 && (
                            <div className="flex justify-between items-center py-2 border-b border-border">
                                <span className="text-sm text-muted-foreground">Costo Total:</span>
                                <span className="text-sm font-medium">
                                    ${detalles.reduce((sum, d) => sum + (d.cantidad * (d.costo_unitario || 0)), 0).toFixed(2)}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </form>
    )
}