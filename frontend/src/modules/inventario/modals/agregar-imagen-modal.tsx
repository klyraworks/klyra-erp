// frontend/src/modules/inventario/modals/agregar-imagen-modal.tsx

"use client"

import { useState, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { agregarImagenProducto } from "@/src/core/store"
import { alertas } from "@/components/alerts/alertas-toast"
import type { Producto } from "@/src/core/api/types"
import {mutate} from "swr";

interface AgregarImagenModalProps {
    producto: Producto | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function AgregarImagenModal({ producto, open, onOpenChange }: AgregarImagenModalProps) {
    const [loading, setLoading] = useState(false)
    const [preview, setPreview] = useState<string | null>(null)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        // Validar tipo
        if (!file.type.startsWith('image/')) {
            alertas.warning('Por favor selecciona un archivo de imagen válido', 'Archivo inválido')
            return
        }

        // Validar tamaño (máx 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alertas.warning('La imagen no debe superar 5MB', 'Archivo muy grande')
            return
        }

        setSelectedFile(file)

        // Crear preview
        const reader = new FileReader()
        reader.onloadend = () => {
            setPreview(reader.result as string)
        }
        reader.readAsDataURL(file)
    }

    const handleSubir = async () => {
        if (!producto || !selectedFile) return

        setLoading(true)
        try {
            await agregarImagenProducto(producto.id, selectedFile)

            alertas.success("Imagen actualizada exitosamente", "Éxito")

            // Recargar datos automáticamente
            mutate(["/api/stock/"])
            mutate(["/api/productos/"])

            onOpenChange(false)
            setPreview(null)
            setSelectedFile(null)
        } catch (error: any) {
            alertas.error(error.message || "Error al subir imagen", "Error")
        } finally {
            setLoading(false)
        }
    }

    const handleReset = () => {
        setPreview(null)
        setSelectedFile(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    if (!producto) return null

    return (
        <Dialog open={open} onOpenChange={(open) => {
            if (!open) handleReset()
            onOpenChange(open)
        }}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <i className="fa-solid fa-image text-primary"></i>
                        {producto.imagen ? 'Actualizar Imagen' : 'Agregar Imagen'}
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-4">
                    <div className="bg-muted/30 rounded-lg p-3 border border-border">
                        <p className="text-sm text-muted-foreground mb-1">Producto:</p>
                        <p className="font-medium">{producto.nombre}</p>
                        <p className="text-xs text-muted-foreground font-mono">{producto.codigo}</p>
                    </div>

                    {/* Imagen actual si existe */}
                    {producto.imagen && !preview && (
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-2">Imagen actual:</p>
                            <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                                <img
                                    src={producto.imagen}
                                    alt={producto.nombre}
                                    className="w-full h-48 object-contain"
                                />
                            </div>
                        </div>
                    )}

                    {/* Preview nueva imagen */}
                    {preview && (
                        <div>
                            <p className="text-sm font-medium text-muted-foreground mb-2">Nueva imagen:</p>
                            <div className="border border-border rounded-lg overflow-hidden bg-muted/20 relative">
                                <img
                                    src={preview}
                                    alt="Preview"
                                    className="w-full h-48 object-contain"
                                />
                                <button
                                    onClick={handleReset}
                                    className="absolute top-2 right-2 w-8 h-8 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center hover:bg-destructive/90 transition-colors"
                                >
                                    <i className="fa-solid fa-times text-sm"></i>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Selector de archivo */}
                    {!preview && (
                        <div>
                            <label className="block">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-colors">
                                    <i className="fa-solid fa-cloud-arrow-up text-4xl text-muted-foreground mb-3"></i>
                                    <p className="text-sm font-medium text-foreground mb-1">
                                        Click para seleccionar una imagen
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        PNG, JPG, GIF hasta 5MB
                                    </p>
                                </div>
                            </label>
                        </div>
                    )}

                    <div className="flex gap-2 pt-2">
                        <button
                            onClick={() => {
                                handleReset()
                                onOpenChange(false)
                            }}
                            disabled={loading}
                            className="flex-1 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSubir}
                            disabled={loading || !selectedFile}
                            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <i className="fa-solid fa-spinner fa-spin"></i>
                                    Subiendo...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-upload"></i>
                                    Subir Imagen
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}