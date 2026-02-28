// frontend/app/(dashboard)/configuracion/departamentos/nuevo/page.tsx
"use client"

import { useRef } from "react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Header } from "@/src/shared/components/header"
import { DepartamentoForm } from "@/src/modules/configuracion/forms/departamento-form"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function CrearDepartamentoPage() {
    const formRef = useRef<HTMLFormElement>(null!)
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/configuracion/departamentos")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Departamentos..." />
    }

    return (
        <>
            <Header
                title="Nuevo Departamento"
                breadcrumb={["Configuración", "Departamentos", "Nuevo"]}
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
                            <span className="hidden sm:inline">Crear Departamento</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <DepartamentoForm mode="create" formRef={formRef} />
                </div>
            </main>
        </>
    )
}