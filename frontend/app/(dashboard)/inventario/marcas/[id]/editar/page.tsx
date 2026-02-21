"use client"

import {useEffect, useRef, useState} from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { MarcaForm } from "@/src/modules/inventario/forms/marca-form"
import { LoadingScreen } from "@/components/ui/loading-screen"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Marca } from "@/src/core/api/types"

export default function EditarMarcaPage() {
    const { id } = useParams()
    const marcaId = id as string

    const [marca, setMarca] = useState<Marca | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const formRef = useRef<HTMLFormElement>(null!)

    useEffect(() => {
        if (!marcaId) return

        async function loadMarca() {
            try {
                const data = await apiFetch<Marca>(`/api/marcas/${marcaId}/`)
                setMarca(data)
                setError(false)
            } catch (err) {
                setError(true)
                if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
                else alertas.error('No se pudo cargar la marca', 'Error')
            } finally {
                setLoading(false)
            }
        }

        loadMarca()
    }, [marcaId])

    if (loading) return <LoadingScreen message="Cargando marca..." />

    if (error || !marca) {
        return (
            <>
                <Header title="Error" breadcrumb={["Inventario", "Marcas", "Error"]} />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-950/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-exclamation text-3xl text-red-600 dark:text-red-400"></i>
                            </div>
                            <h3 className="text-lg font-semibold text-foreground mb-2">No encontrada</h3>
                            <p className="text-sm text-muted-foreground mb-6">
                                La marca no existe o no tienes permisos para acceder a ella.
                            </p>
                            <Link
                                href="/inventario/marcas"
                                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                            >
                                <i className="fa-solid fa-arrow-left"></i>Volver
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
                title="Editar Marca"
                breadcrumb={["Inventario", "Marcas", "Editar", marca.nombre]}
                actions={
                    <div className="flex items-center gap-3">
                        {marca.is_active ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-500/10 text-green-600 border border-green-200 dark:border-green-800">
                                <i className="fa-solid fa-circle-check text-[10px]"></i>Activa
                            </span>
                        ) : (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-600 border border-red-200 dark:border-red-800">
                                <i className="fa-solid fa-ban text-[10px]"></i>Inactiva
                            </span>
                        )}
                        <Link
                            href="/inventario/marcas"
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
                    <MarcaForm mode="edit" marca={marca} formRef={formRef} />
                </div>
            </main>
        </>
    )
}