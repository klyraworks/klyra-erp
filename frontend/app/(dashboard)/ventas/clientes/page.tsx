"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { ClientesSection } from "@/src/modules/ventas/components/clientes-section"
import { LoadingScreen } from "@/components/ui/loading-screen"
import React from "react"

export default function ClientesPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAdd = () => {
        setIsNavigating(true)
        router.push("/ventas/clientes/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando..." />
    }

    return (
        <>
            <Header
                title="Clientes"
                breadcrumb={["Ventas", "Clientes"]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleAdd}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Cliente
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <ClientesSection />
            </main>
        </>
    )
}