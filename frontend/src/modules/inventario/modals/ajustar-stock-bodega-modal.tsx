// frontend/src/modules/inventario/modals/ajustar-stock-bodega-modal.tsx

"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select } from "@/components/select/select-klyra"
import { ajustarStockBodega } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { InventarioBodegaItem, AjustarStockPayload } from "@/src/core/api/types"
import { mutate } from "swr"
import {apiFetch} from "@/src/core/api/client"

interface AjustarStockBodegaModalProps {
    inventario: InventarioBodegaItem | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function AjustarStockBodegaModal({ inventario, open, onOpenChange }: AjustarStockBodegaModalProps) {
    const [loading, setLoading] = useState(false)
    const [cantidad, setCantidad] = useState("")
    const [tipo, setTipo] = useState<'incremento' | 'decremento' | 'establecer'>('establecer')
    const [motivo, setMotivo] = useState("")
    const [referencia, setReferencia] = useState("")

    const handleAjustar = async () => {
        if (!inventario) return

        if (!cantidad || Number(cantidad) <= 0) {
            alertas.warning('Ingresa una cantidad válida', 'Campo requerido')
            return
        }

        if (!motivo.trim()) {
            alertas.warning('El motivo es requerido', 'Campo requerido')
            return
        }

        setLoading(true)
        try {
            await ajustarStockBodega(inventario.id, {
                cantidad: Number(cantidad),
                tipo,
                motivo: motivo.trim(),
                referencia: referencia.trim() || undefined
            })

            alertas.success("Stock ajustado exitosamente", "Éxito")

            // Recargar datos del inventario
            mutate(["/api/stock/"])
            mutate(["/api/productos/"])

            onOpenChange(false)
            resetForm()
        } catch (error: any) {
            alertas.error(error.message || "Error al ajustar stock", "Error")
        } finally {
            setLoading(false)
        }
    }

    const resetForm = () => {
        setCantidad("")
        setTipo('establecer')
        setMotivo("")
        setReferencia("")
    }

    const calcularNuevoStock = () => {
        if (!inventario || !cantidad) return inventario?.cantidad || 0

        const cant = Number(cantidad)
        if (tipo === 'establecer') return cant
        if (tipo === 'incremento') return inventario.cantidad + cant
        return Math.max(0, inventario.cantidad - cant)
    }

    if (!inventario) return null

    return (
        <Dialog open={open} onOpenChange={(open) => {
            if (!open) resetForm()
            onOpenChange(open)
        }}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <i className="fa-solid fa-sliders text-primary"></i>
                        Ajustar Stock en Bodega
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4">
                    {/* Info del producto y bodega */}
                    <div className="bg-muted/30 rounded-lg p-3 border border-border space-y-2">
                        <div>
                            <p className="text-xs text-muted-foreground">Producto:</p>
                            <p className="font-medium">{inventario.producto_nombre}</p>
                            <p className="text-xs text-muted-foreground font-mono">{inventario.producto_codigo}</p>
                        </div>
                        <div className="border-t border-border pt-2">
                            <p className="text-xs text-muted-foreground">Bodega:</p>
                            <p className="font-medium">{inventario.bodega_nombre}</p>
                        </div>
                        <div className="border-t border-border pt-2">
                            <p className="text-xs text-muted-foreground">Stock actual:</p>
                            <p className="text-lg font-bold">{inventario.cantidad} {inventario.unidad_medida}</p>
                        </div>
                    </div>

                    {/* Tipo de ajuste */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Tipo de Ajuste *
                        </label>
                        <Select
                            options={[
                                { value: 'establecer', label: 'Establecer cantidad exacta', description: 'Reemplaza el stock actual' },
                                { value: 'incremento', label: 'Incrementar stock', description: 'Suma al stock actual' },
                                { value: 'decremento', label: 'Decrementar stock', description: 'Resta del stock actual' }
                            ]}
                            value={tipo}
                            onChange={(value) => setTipo(value as any)}
                            className="w-full"
                        />
                    </div>

                    {/* Cantidad */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Cantidad *
                        </label>
                        <input
                            type="number"
                            value={cantidad}
                            onChange={(e) => setCantidad(e.target.value)}
                            min="0"
                            step="1"
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            placeholder={tipo === 'establecer' ? 'Nueva cantidad' : 'Cantidad a ajustar'}
                        />
                        {cantidad && (
                            <p className="text-xs text-muted-foreground mt-1">
                                Nuevo stock: <span className="font-semibold text-foreground">{calcularNuevoStock()} {inventario.unidad_medida}</span>
                            </p>
                        )}
                    </div>

                    {/* Motivo */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Motivo *
                        </label>
                        <textarea
                            value={motivo}
                            onChange={(e) => setMotivo(e.target.value)}
                            rows={2}
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
                            placeholder="Ej: Ajuste por inventario físico"
                        />
                    </div>

                    {/* Referencia (opcional) */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Referencia <span className="text-xs font-normal">(Opcional)</span>
                        </label>
                        <input
                            type="text"
                            value={referencia}
                            onChange={(e) => setReferencia(e.target.value)}
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            placeholder="Ej: INV-2024-001"
                        />
                    </div>

                    {/* Advertencia */}
                    <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                        <div className="flex gap-2 text-yellow-800 dark:text-yellow-300 text-xs">
                            <i className="fa-solid fa-exclamation-triangle mt-0.5"></i>
                            <div>
                                <p className="font-medium">Atención</p>
                                <p className="mt-1">
                                    Este ajuste creará un movimiento de inventario automáticamente.
                                    Asegúrate de que los datos sean correctos.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Botones */}
                    <div className="flex gap-2 pt-2">
                        <button
                            onClick={() => {
                                resetForm()
                                onOpenChange(false)
                            }}
                            disabled={loading}
                            className="flex-1 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleAjustar}
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"></i>
                                    Ajustando...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-check"></i>
                                    Ajustar Stock
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}