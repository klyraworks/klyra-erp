// frontend/src/modules/inventario/modals/inventario-total-modal.tsx

"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { getInventarioTotal } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { Producto, InventarioTotalResponse } from "@/src/core/api/types"

interface InventarioTotalModalProps {
    producto: Producto | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function InventarioTotalModal({ producto, open, onOpenChange }: InventarioTotalModalProps) {
    const [loading, setLoading] = useState(false)
    const [data, setData] = useState<InventarioTotalResponse | null>(null)

    useEffect(() => {
        if (open && producto) {
            cargarInventario()
        }
    }, [open, producto])

    const cargarInventario = async () => {
        if (!producto) return

        setLoading(true)
        try {
            const resultado = await getInventarioTotal(producto.id)
            setData(resultado)
        } catch (error: any) {
            alertas.error(error.message || "Error al cargar inventario", "Error")
            setData(null)
        } finally {
            setLoading(false)
        }
    }

    const getEstadoBadge = (estado: string) => {
        const estados: Record<string, { color: string; bg: string; icon: string }> = {
            'sin_stock': { color: "text-slate-600 dark:text-slate-400", bg: "bg-slate-500/10", icon: "fa-circle-xmark" },
            'critico': { color: "text-destructive", bg: "bg-destructive/10", icon: "fa-circle-exclamation" },
            'bajo': { color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-500/10", icon: "fa-triangle-exclamation" },
            'normal': { color: "text-success", bg: "bg-success/10", icon: "fa-circle-check" }
        }
        return estados[estado] || estados.normal
    }

    if (!producto) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <i className="fa-solid fa-boxes-stacked text-primary"></i>
                        Inventario Total - {producto.nombre}
                    </DialogTitle>
                </DialogHeader>

                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                            <i className="fa-solid fa-spinner fa-spin text-4xl text-primary mb-4"></i>
                            <p className="text-sm text-muted-foreground">Cargando inventario...</p>
                        </div>
                    </div>
                ) : !data ? (
                    <div className="text-center py-12">
                        <i className="fa-solid fa-inbox text-4xl text-muted-foreground mb-4"></i>
                        <p className="text-muted-foreground">No se pudo cargar la información</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Resumen General */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <div className="flex items-center gap-2 mb-2">
                                    <i className="fa-solid fa-warehouse text-primary"></i>
                                    <p className="text-xs text-muted-foreground uppercase">Bodegas</p>
                                </div>
                                <p className="text-2xl font-bold">{data.resumen.total_bodegas}</p>
                            </div>

                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <div className="flex items-center gap-2 mb-2">
                                    <i className="fa-solid fa-cubes text-primary"></i>
                                    <p className="text-xs text-muted-foreground uppercase">Stock Total</p>
                                </div>
                                <p className="text-2xl font-bold">{data.resumen.stock_total}</p>
                            </div>

                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <div className="flex items-center gap-2 mb-2">
                                    <i className="fa-solid fa-lock text-orange-500"></i>
                                    <p className="text-xs text-muted-foreground uppercase">Reservado</p>
                                </div>
                                <p className="text-2xl font-bold text-orange-500">{data.resumen.stock_reservado}</p>
                            </div>

                            <div className="bg-muted/30 rounded-lg p-4 border border-border">
                                <div className="flex items-center gap-2 mb-2">
                                    <i className="fa-solid fa-check-circle text-success"></i>
                                    <p className="text-xs text-muted-foreground uppercase">Disponible</p>
                                </div>
                                <p className="text-2xl font-bold text-success">{data.resumen.stock_disponible}</p>
                            </div>
                        </div>

                        {/* Valorización (si tiene permiso) */}
                        {data.valorizacion && (
                            <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg p-4 border border-primary/20">
                                <h3 className="text-sm font-semibold text-muted-foreground uppercase mb-3 flex items-center gap-2">
                                    <i className="fa-solid fa-dollar-sign"></i>
                                    Valorización del Inventario
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <p className="text-xs text-muted-foreground mb-1">Valor de Compra</p>
                                        <p className="text-xl font-bold">${data.valorizacion.valor_compra.toFixed(2)}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground mb-1">Valor de Venta</p>
                                        <p className="text-xl font-bold text-success">${data.valorizacion.valor_venta.toFixed(2)}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-muted-foreground mb-1">Utilidad Potencial</p>
                                        <p className="text-xl font-bold text-primary">${data.valorizacion.utilidad_potencial.toFixed(2)}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Estado General */}
                        <div className="flex items-center justify-between bg-muted/20 rounded-lg p-4 border border-border">
                            <div className="flex items-center gap-3">
                                <i className="fa-solid fa-signal text-lg text-muted-foreground"></i>
                                <div>
                                    <p className="text-sm font-medium">Estado General</p>
                                    <p className="text-xs text-muted-foreground">Stock mínimo: {data.producto.stock_minimo}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {(() => {
                                    const estado = getEstadoBadge(data.resumen.estado_general)
                                    return (
                                        <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${estado.bg} ${estado.color}`}>
                                            <i className={`fa-solid ${estado.icon}`}></i>
                                            {data.resumen.estado_general.charAt(0).toUpperCase() + data.resumen.estado_general.slice(1)}
                                        </span>
                                    )
                                })()}
                                {data.resumen.necesita_reposicion && (
                                    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500/10 text-orange-600 dark:text-orange-400">
                                        <i className="fa-solid fa-exclamation-triangle"></i>
                                        Necesita Reposición
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Detalle por Bodega */}
                        <div className="border border-border rounded-lg overflow-hidden">
                            <div className="bg-muted/50 px-4 py-3 border-b">
                                <h3 className="text-sm font-semibold text-muted-foreground uppercase">
                                    Detalle por Bodega
                                </h3>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b bg-muted/20">
                                            <th className="text-left px-4 py-3 font-medium text-muted-foreground">Bodega</th>
                                            <th className="text-left px-4 py-3 font-medium text-muted-foreground">Ubicación</th>
                                            <th className="text-center px-4 py-3 font-medium text-muted-foreground">Stock</th>
                                            <th className="text-center px-4 py-3 font-medium text-muted-foreground">Reservado</th>
                                            <th className="text-center px-4 py-3 font-medium text-muted-foreground">Disponible</th>
                                            <th className="text-center px-4 py-3 font-medium text-muted-foreground">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.por_bodega.map((item, idx) => {
                                            const estado = getEstadoBadge(item.estado)
                                            return (
                                                <tr key={idx} className="border-b hover:bg-muted/30 transition-colors">
                                                    <td className="px-4 py-3">
                                                        <div>
                                                            <p className="font-medium">{item.bodega.nombre}</p>
                                                            <div className="flex items-center gap-2 mt-1">
                                                                <span className="text-xs text-muted-foreground font-mono">{item.bodega.codigo}</span>
                                                                {item.bodega.es_principal && (
                                                                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 rounded text-[10px] font-medium">
                                                                        <i className="fa-solid fa-crown text-[8px]"></i>
                                                                        Principal
                                                                    </span>
                                                                )}
                                                                {item.bodega.permite_ventas && (
                                                                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-500/10 text-green-600 dark:text-green-400 rounded text-[10px] font-medium">
                                                                        <i className="fa-solid fa-cash-register text-[8px]"></i>
                                                                        Ventas
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 text-xs text-muted-foreground">
                                                        {item.ubicacion?.nombre || '—'}
                                                    </td>
                                                    <td className="px-4 py-3 text-center font-semibold">{item.cantidad}</td>
                                                    <td className="px-4 py-3 text-center">
                                                        {item.stock_reservado > 0 ? (
                                                            <span className="text-orange-500 font-medium">{item.stock_reservado}</span>
                                                        ) : (
                                                            <span className="text-muted-foreground">—</span>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 text-center font-semibold text-success">{item.stock_disponible}</td>
                                                    <td className="px-4 py-3 text-center">
                                                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${estado.bg} ${estado.color}`}>
                                                            <i className={`fa-solid ${estado.icon} text-[10px]`}></i>
                                                            {item.estado}
                                                        </span>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}