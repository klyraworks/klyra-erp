"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Header } from "@/src/shared/components/header"
import { ClienteForm } from "@/src/modules/ventas/forms/cliente-form"
import { LoadingScreen } from "@/components/ui/loading-screen"
import { alertas } from "@/components/alerts/alertas-toast"
import { apiFetch, ApiError } from "@/src/core/api/client"
import { Cliente } from "@/src/core/api/types"
import React from "react"

export default function EditarClientePage() {
    const { id } = useParams()
    const clienteId = id as string
    const router = useRouter()
    const formRef = useRef<HTMLFormElement>(null!)

    const [cliente, setCliente] = useState<Cliente | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [isNavigating, setIsNavigating] = useState(false)

    useEffect(() => {
        if (!clienteId) return
        async function loadCliente() {
            try {
                const data = await apiFetch<Cliente>(`/api/personas/clientes/${clienteId}/`)
                setCliente(data)
            } catch (err) {
                setError(true)
                if (err instanceof ApiError) alertas.error(err.mensaje, err.titulo)
                else alertas.error("No se pudo cargar el cliente", "Error")
            } finally {
                setLoading(false)
            }
        }
        loadCliente()
    }, [clienteId])

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/ventas/clientes")
    }

    if (loading || isNavigating) return <LoadingScreen message="Cargando..." />

    if (error || !cliente) {
        return (
            <>
                <Header title="Error" breadcrumb={["Ventas", "Clientes", "Error"]} />
                <main className="flex-1 overflow-y-auto p-6">
                    <div className="max-w-2xl mx-auto">
                        <div className="bg-card rounded-xl border border-border shadow-sm p-8 text-center">
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-950/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i className="fa-solid fa-circle-exclamation text-3xl text-red-600 dark:text-red-400"></i>
                            </div>
                            <h3 className="text-lg font-semibold text-foreground mb-2">No encontrado</h3>
                            <p className="text-sm text-muted-foreground mb-6">
                                El cliente no existe o no tienes permisos para verlo.
                            </p>
                            <Link
                                href="/ventas/clientes"
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
                title="Editar Cliente"
                breadcrumb={["Ventas", "Clientes", "Editar", cliente.razon_social]}
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
                            <span className="hidden sm:inline">Actualizar Cliente</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <ClienteForm mode="edit" cliente={cliente} formRef={formRef} />
                </div>
            </main>
        </>
    )
}