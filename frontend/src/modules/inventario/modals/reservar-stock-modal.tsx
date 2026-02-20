// frontend/src/modules/inventario/modals/reservar-stock-modal.tsx

"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select } from "@/components/select/select-klyra"
import { reservarStockBodega } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { InventarioBodegaItem, ReservarStockPayload } from "@/src/core/api/types"
import { mutate } from "swr"
import {apiFetch} from "@/src/core/api/client"

interface ReservarStockModalProps {
    inventario: InventarioBodegaItem | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ReservarStockModal({ inventario, open, onOpenChange }: ReservarStockModalProps) {
    const [loading, setLoading] = useState(false)
    const [cantidad, setCantidad] = useState("")
    const [tipo, setTipo] = useState<'reservar' | 'liberar'>('reservar')
    const [referencia, setReferencia] = useState("")
    const [motivo, setMotivo] = useState("")

    const handleReservar = async () => {
        if (!inventario) return

        if (!cantidad || Number(cantidad) <= 0) {
            alertas.warning('Ingresa una cantidad válida', 'Campo requerido')
            return
        }

        // La referencia ahora es opcional - se generará automáticamente en el backend si no se proporciona

        // Validar según tipo
        if (tipo === 'reservar') {
            const disponible = inventario.stock_disponible
            if (Number(cantidad) > disponible) {
                alertas.warning(
                    `Stock disponible insuficiente. Disponible: ${disponible}`,
                    'Stock insuficiente'
                )
                return
            }
        } else {
            // liberar
            if (Number(cantidad) > inventario.stock_reservado) {
                alertas.warning(
                    `No hay suficiente stock reservado. Reservado: ${inventario.stock_reservado}`,
                    'Stock reservado insuficiente'
                )
                return
            }
        }

        setLoading(true)
        try {
            await reservarStockBodega(inventario.id, {
                cantidad: Number(cantidad),
                tipo,
                referencia: referencia.trim() || undefined,
                motivo: motivo.trim() || undefined
            })

            alertas.success(
                tipo === 'reservar' ? "Stock reservado exitosamente" : "Stock liberado exitosamente",
                "Éxito"
            )

            // Recargar datos automáticamente
            mutate(["/api/stock/"])
            mutate(["/api/productos/"])

            onOpenChange(false)
            resetForm()
        } catch (error: any) {
            alertas.error(error.message || "Error al gestionar reserva", "Error")
        } finally {
            setLoading(false)
        }
    }

    const resetForm = () => {
        setCantidad("")
        setTipo('reservar')
        setReferencia("")
        setMotivo("")
    }

    const calcularNuevoEstado = () => {
        if (!inventario || !cantidad) return null

        const cant = Number(cantidad)
        let nuevoReservado = inventario.stock_reservado
        let nuevoDisponible = inventario.stock_disponible

        if (tipo === 'reservar') {
            nuevoReservado += cant
            nuevoDisponible -= cant
        } else {
            nuevoReservado -= cant
            nuevoDisponible += cant
        }

        return { nuevoReservado, nuevoDisponible }
    }

    const nuevoEstado = calcularNuevoEstado()

    if (!inventario) return null

    return (
        <Dialog open={open} onOpenChange={(open) => {
            if (!open) resetForm()
            onOpenChange(open)
        }}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <i className="fa-solid fa-lock text-primary"></i>
                        Reservar/Liberar Stock
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
                        <div className="border-t border-border pt-2 grid grid-cols-3 gap-2">
                            <div>
                                <p className="text-xs text-muted-foreground">Total:</p>
                                <p className="font-semibold">{inventario.cantidad}</p>
                            </div>
                            <div>
                                <p className="text-xs text-orange-600 dark:text-orange-400">Reservado:</p>
                                <p className="font-semibold text-orange-600 dark:text-orange-400">{inventario.stock_reservado}</p>
                            </div>
                            <div>
                                <p className="text-xs text-success">Disponible:</p>
                                <p className="font-semibold text-success">{inventario.stock_disponible}</p>
                            </div>
                        </div>
                    </div>

                    {/* Tipo de operación */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Operación *
                        </label>
                        <Select
                            options={[
                                {
                                    value: 'reservar',
                                    label: 'Reservar stock',
                                    description: 'Reservar para pedidos o ventas'
                                },
                                {
                                    value: 'liberar',
                                    label: 'Liberar stock',
                                    description: 'Liberar reservas existentes'
                                }
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
                            min="1"
                            max={tipo === 'reservar' ? inventario.stock_disponible : inventario.stock_reservado}
                            step="1"
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            placeholder={`Máximo: ${tipo === 'reservar' ? inventario.stock_disponible : inventario.stock_reservado}`}
                        />
                        {nuevoEstado && (
                            <div className="mt-2 text-xs space-y-1">
                                <p className="text-muted-foreground">
                                    Nuevo estado:
                                </p>
                                <div className="flex items-center gap-3">
                                    <span className="text-orange-600 dark:text-orange-400">
                                        Reservado: <span className="font-semibold">{nuevoEstado.nuevoReservado}</span>
                                    </span>
                                    <span className="text-success">
                                        Disponible: <span className="font-semibold">{nuevoEstado.nuevoDisponible}</span>
                                    </span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Referencia */}
                    <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">
                            Referencia <span className="text-xs font-normal text-muted-foreground/70">(Opcional)</span>
                        </label>
                        <input
                            type="text"
                            value={referencia}
                            onChange={(e) => setReferencia(e.target.value)}
                            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                            placeholder="Ej: PEDIDO-001, VENTA-123 (o déjalo vacío)"
                        />
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
                            placeholder={tipo === 'reservar' ? "Ej: Reserva para cliente VIP" : "Ej: Pedido cancelado"}
                        />
                    </div>

                    {/* Info adicional */}
                    <div className={`${tipo === 'reservar' ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800' : 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'} border rounded-lg p-3`}>
                        <div className={`flex gap-2 ${tipo === 'reservar' ? 'text-blue-800 dark:text-blue-300' : 'text-green-800 dark:text-green-300'} text-xs`}>
                            <i className={`fa-solid ${tipo === 'reservar' ? 'fa-lock' : 'fa-lock-open'} mt-0.5`}></i>
                            <div>
                                <p className="font-medium">
                                    {tipo === 'reservar' ? 'Reservar Stock' : 'Liberar Stock'}
                                </p>
                                <p className="mt-1">
                                    {tipo === 'reservar'
                                        ? 'El stock reservado no estará disponible para otras ventas hasta que se libere.'
                                        : 'El stock liberado volverá a estar disponible para ventas.'
                                    }
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
                            onClick={handleReservar}
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"></i>
                                    Procesando...
                                </>
                            ) : (
                                <>
                                    <i className={`fa-solid ${tipo === 'reservar' ? 'fa-lock' : 'fa-lock-open'}`}></i>
                                    {tipo === 'reservar' ? 'Reservar' : 'Liberar'}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}