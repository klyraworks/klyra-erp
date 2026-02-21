// app/(dashboard)/bodegas/[id]/editar/page.tsx

"use client"

import {useEffect, useRef, useState} from "react"
import { useParams } from "next/navigation"
import Link from "next/link"

import { Header } from "@/src/shared/components/header"
import { BodegaForm } from "@/src/modules/inventario/forms/bodega-form"
import { LoadingScreen } from "@/components/ui/loading-screen"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Bodega } from "@/src/core/api/types"

export default function EditarBodegaPage() {
    const params    = useParams()
    const bodegaId  = params.id as string
    const formRef = useRef<HTMLFormElement>(null!)

    const [bodega,  setBodega]  = useState<Bodega | null>(null)
    const [loading, setLoading] = useState(true)
    const [error,   setError]   = useState(false)

    useEffect(() => {
        if (!bodegaId) return

        async function loadBodega() {
            try {
                setLoading(true)
                const data = await apiFetch<Bodega>(`/api/bodegas/${bodegaId}/`)
                setBodega(data)
                setError(false)
            } catch (err) {
                setError(true)
                if (err instanceof ApiError) {
                    alertas.error(err.mensaje, err.titulo)
                } else {
                    alertas.error('No se pudo cargar la bodega', 'Error')
                }
            } finally {
                setLoading(false)
            }
        }

        loadBodega()
    }, [bodegaId])

    if (loading) {
        return <LoadingScreen message="Cargando datos de la bodega..." />
    }

    if (error || !bodega) {
        return (
            <>
                <Header
                    title="Error"
                    breadcrumb={["Inventario", "Bodegas", "Error"]}
                />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-950/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-exclamation text-3xl text-red-600 dark:text-red-400"></i>
                            </div>
                            <h3 className="text-lg font-semibold text-foreground mb-2">
                                Bodega no encontrada
                            </h3>
                            <p className="text-sm text-muted-foreground mb-6">
                                La bodega que buscas no existe o no tienes permisos para acceder a ella.
                            </p>
                            <Link
                                href="/inventario/bodegas"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                            >
                                <i className="fa-solid fa-arrow-left"></i>
                                Volver a Bodegas
                            </Link>
                        </div>
                    </div>
                </main>
            </>
        )
    }

    return (
        <>
            <Header
                title="Editar Bodega"
                breadcrumb={["Inventario", "Bodegas", "Editar", bodega.nombre]}
                actions={
                    <div className="flex items-center gap-2">
                        {bodega.es_principal && (
                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-yellow-100 dark:bg-yellow-950/20 text-yellow-800 dark:text-yellow-300 rounded-lg text-xs font-medium">
                                <i className="fa-solid fa-crown"></i>
                                Principal
                            </div>
                        )}
                        {bodega.permite_ventas && (
                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-950/20 text-green-800 dark:text-green-300 rounded-lg text-xs font-medium">
                                <i className="fa-solid fa-cash-register"></i>
                                Permite ventas
                            </div>
                        )}
                        {(bodega.total_productos ?? 0) > 0 && (
                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-blue-100 dark:bg-blue-950/20 text-blue-800 dark:text-blue-300 rounded-lg text-xs font-medium">
                                <i className="fa-solid fa-box"></i>
                                {bodega.total_productos} producto{bodega.total_productos !== 1 ? 's' : ''}
                            </div>
                        )}
                        <Link
                            href="/inventario/bodegas"
                            className="flex items-center gap-2 px-4 py-2 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
                        >
                            <i className="fa-solid fa-arrow-left"></i>
                            <span className="hidden sm:inline">Volver</span>
                        </Link>
                        <button
                            onClick={() => formRef.current?.requestSubmit()}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            <i className="fa-solid fa-save"></i>
                            <span className="hidden sm:inline">Editar Marca</span>
                        </button>
                    </div>
                }
            />

            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    {/* Información contextual */}
                    <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                        <div className="flex items-start gap-3">
                            <i className="fa-solid fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"></i>
                            <div className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
                                <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">
                                    Editando bodega: {bodega.codigo}
                                </p>
                                {bodega.responsable && (
                                    <p>
                                        <strong>Responsable:</strong> {bodega.responsable.nombre_completo}
                                    </p>
                                )}
                                {bodega.ciudad && (
                                    <p>
                                        <strong>Ubicación:</strong> {bodega.ciudad.name}
                                        {bodega.ciudad.region && `, ${bodega.ciudad.region.name}`}
                                    </p>
                                )}
                                {(bodega.valor_total_inventario ?? 0) > 0 && (
                                    <p>
                                        <strong>Valor inventario:</strong> ${bodega.valor_total_inventario!.toFixed(2)}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                    <BodegaForm mode="edit" bodega={bodega} formRef={formRef} />
                </div>
            </main>
        </>
    )
}