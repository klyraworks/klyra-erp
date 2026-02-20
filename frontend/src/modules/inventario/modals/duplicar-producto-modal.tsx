// frontend/src/modules/inventario/modals/duplicar-producto-modal.tsx

"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { duplicarProducto } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { Producto } from "@/src/core/api/types"
import { mutate } from "swr"

interface DuplicarProductoModalProps {
    producto: Producto | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function DuplicarProductoModal({ producto, open, onOpenChange }: DuplicarProductoModalProps) {
    const [loading, setLoading] = useState(false)
    const [nombre, setNombre] = useState("")
    const [codigoAux, setCodigoAux] = useState("")

    const handleDuplicar = async () => {
        if (!producto) return

        setLoading(true)
        try {
            await duplicarProducto(producto.id, {
                nombre: nombre.trim() || undefined,
                codigo_aux: codigoAux.trim() || undefined
            })

            alertas.success("Producto duplicado exitosamente", "Duplicado")


            // Recargar datos automáticamente
            mutate(["/api/stock/"])
            mutate(["/api/productos/"])

            onOpenChange(false)
            setNombre("")
            setCodigoAux("")
        } catch (error: any) {
            alertas.error(error.message || "Error al duplicar producto", "Error")
        } finally {
            setLoading(false)
        }
    }

    if (!producto) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <i className="fa-solid fa-copy text-primary"></i>
                        Duplicar Producto
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4">
                    <div className="bg-muted/30 rounded-lg p-3 border border-border">
                        <p className="text-sm text-muted-foreground mb-1">Producto original:</p>
                        <p className="font-medium">{producto.nombre}</p>
                        <p className="text-xs text-muted-foreground font-mono">{producto.codigo}</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Nuevo Nombre (opcional)
                        </label>
                        <input
                            type="text"
                            value={nombre}
                            onChange={(e) => setNombre(e.target.value)}
                            placeholder={`${producto.nombre} (Copia)`}
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                            Si se deja vacío, se agregará "(Copia)" al nombre original
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Código Auxiliar (opcional)
                        </label>
                        <input
                            type="text"
                            value={codigoAux}
                            onChange={(e) => setCodigoAux(e.target.value)}
                            placeholder="Nuevo código auxiliar"
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                        />
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <div className="flex gap-2 text-blue-800 dark:text-blue-300 text-xs">
                            <i className="fa-solid fa-info-circle mt-0.5"></i>
                            <div>
                                <p className="font-medium">Información</p>
                                <ul className="mt-1 space-y-0.5 list-disc list-inside">
                                    <li>El stock del duplicado empezará en 0</li>
                                    <li>Se generará un código único automáticamente</li>
                                    <li>El código de barras se dejará vacío</li>
                                    {producto.es_kit && <li>Se copiarán todos los componentes del kit</li>}
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                        <button
                            onClick={() => onOpenChange(false)}
                            disabled={loading}
                            className="flex-1 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleDuplicar}
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"></i>
                                    Duplicando...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-copy"></i>
                                    Duplicar
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}