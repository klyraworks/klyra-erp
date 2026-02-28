"use client"

import { useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { ClienteForm } from "@/src/modules/ventas/forms/cliente-form"
import { LoadingScreen } from "@/components/ui/loading-screen"
import React from "react"

export default function NuevoClientePage() {
    const formRef = useRef<HTMLFormElement>(null!)
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/ventas/clientes")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando..." />
    }

    return (
        <>
            <Header
                title="Nuevo Cliente"
                breadcrumb={["Ventas", "Clientes", "Nuevo"]}
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
                            <span className="hidden sm:inline">Crear Cliente</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <ClienteForm mode="create" formRef={formRef} />
                </div>
            </main>
        </>
    )
}