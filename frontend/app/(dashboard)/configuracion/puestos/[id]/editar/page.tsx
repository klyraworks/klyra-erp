"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { PuestoForm } from "@/src/modules/configuracion/forms/puesto-form"
import { LoadingScreen } from "@/components/ui/loading-screen"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Puesto } from "@/src/core/api/types"

export default function EditarPuestoPage() {
    const { id } = useParams()
    const puestoId = id as string
    const router = useRouter()
    const formRef = useRef<HTMLFormElement>(null!)

    const [puesto, setPuesto]           = useState<Puesto | null>(null)
    const [loading, setLoading]         = useState(true)
    const [error, setError]             = useState(false)
    const [isNavigating, setIsNavigating] = useState(false)

    useEffect(() => {
        if (!puestoId) return
        async function loadPuesto() {
            try {
                const data = await apiFetch<Puesto>(`/api/puestos/${puestoId}/`)
                setPuesto(data)
            } catch (err) {
                setError(true)
                if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
                else alertas.error("No se pudo cargar el puesto", "Error")
            } finally {
                setLoading(false)
            }
        }
        loadPuesto()
    }, [puestoId])

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/configuracion/puestos")
    }

    if (loading || isNavigating) {
        return <LoadingScreen message="Cargando Puesto..." />
    }

    if (error || !puesto) {
        return (
            <>
                <Header title="Error" breadcrumb={["RRHH", "Puestos", "Error"]} />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-950/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-exclamation text-3xl text-red-600 dark:text-red-400"></i>
                            </div>
                            <h3 className="text-lg font-semibold text-foreground mb-2">No encontrado</h3>
                            <p className="text-sm text-muted-foreground mb-6">El puesto no existe o no tienes permisos para editarlo.</p>
                            <Link
                                href="/configuracion/puestos"
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
                title="Editar Puesto"
                breadcrumb={["RRHH", "Puestos", "Editar", puesto.nombre]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleVolver}
                            className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                        >
                            <i className="fa-solid fa-arrow-left"></i>
                            <span className="hidden sm:inline">Volver</span>
                        </button>
                        <button
                            onClick={() => formRef.current?.requestSubmit()}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                        >
                            <i className="fa-solid fa-save"></i>
                            <span className="hidden sm:inline">Actualizar Puesto</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <PuestoForm mode="edit" puesto={puesto} formRef={formRef} />
                </div>
            </main>
        </>
    )
}