// frontend/src/modules/inventario/modals/cambiar-ubicacion-modal.tsx

"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select } from "@/components/select/select-klyra"
import { cambiarUbicacionBodega, useUbicaciones } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { InventarioBodegaItem, CambiarUbicacionPayload } from "@/src/core/api/types"
import { mutate } from "swr"
import {apiFetch} from "@/src/core/api/client"

interface CambiarUbicacionModalProps {
    inventario: InventarioBodegaItem | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function CambiarUbicacionModal({ inventario, open, onOpenChange }: CambiarUbicacionModalProps) {
    const [loading, setLoading] = useState(false)
    const [ubicacionId, setUbicacionId] = useState("")
    const [motivo, setMotivo] = useState("")

    // Cargar ubicaciones de la bodega
    const { data: ubicaciones, isLoading: loadingUbicaciones } = useUbicaciones(inventario?.bodega_id)

    const handleCambiar = async () => {
        if (!inventario) return

        if (!ubicacionId) {
            alertas.warning('Selecciona una ubicación', 'Campo requerido')
            return
        }

        setLoading(true)
        try {
            await cambiarUbicacionBodega(inventario.id, {
                ubicacion_id: ubicacionId,
                motivo: motivo.trim() || undefined
            })

            alertas.success("Ubicación actualizada exitosamente", "Éxito")

            // Recargar datos automáticamente
            mutate(["/api/stock/"])
            mutate(["/api/productos/"])

            onOpenChange(false)
            resetForm()
        } catch (error: any) {
            alertas.error(error.message || "Error al cambiar ubicación", "Error")
        } finally {
            setLoading(false)
        }
    }

    const resetForm = () => {
        setUbicacionId("")
        setMotivo("")
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
                        <i className="fa-solid fa-location-dot text-primary"></i>
                        Cambiar Ubicación
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
                            <p className="text-xs text-muted-foreground">Stock:</p>
                            <p className="font-semibold">{inventario.cantidad} {inventario.unidad_medida}</p>
                        </div>
                    </div>

                    {/* Selector de ubicación */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Nueva Ubicación *
                        </label>
                        {loadingUbicaciones ? (
                            <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
                                <i className="fa-solid fa-spinner fa-spin mr-2"></i>
                                Cargando ubicaciones...
                            </div>
                        ) : ubicaciones && ubicaciones.length > 0 ? (
                            <Select
                                options={ubicaciones.map(u => ({
                                    value: u.id,
                                    label: `${u.pasillo}-${u.estante}-${u.nivel}`,
                                    description: u.descripcion || undefined
                                }))}
                                value={ubicacionId}
                                onChange={(value) => setUbicacionId(value.toString())}
                                searchable
                                placeholder="Seleccionar ubicación"
                                className="w-full"
                            />
                        ) : (
                            <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                                <div className="flex gap-2 text-yellow-800 dark:text-yellow-300 text-xs">
                                    <i className="fa-solid fa-exclamation-triangle"></i>
                                    <p>No hay ubicaciones disponibles en esta bodega. Crea ubicaciones primero.</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Motivo (opcional) */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Motivo <span className="text-xs font-normal">(Opcional)</span>
                        </label>
                        <textarea
                            value={motivo}
                            onChange={(e) => setMotivo(e.target.value)}
                            rows={2}
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
                            placeholder="Ej: Reorganización de bodega"
                        />
                    </div>

                    {/* Info adicional */}
                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <div className="flex gap-2 text-blue-800 dark:text-blue-300 text-xs">
                            <i className="fa-solid fa-info-circle mt-0.5"></i>
                            <div>
                                <p className="font-medium">Información</p>
                                <p className="mt-1">
                                    El cambio de ubicación se registrará en el historial del producto.
                                    El stock no se verá afectado.
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
                            onClick={handleCambiar}
                            disabled={loading || !ubicaciones || ubicaciones.length === 0}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"></i>
                                    Cambiando...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-check"></i>
                                    Cambiar Ubicación
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}