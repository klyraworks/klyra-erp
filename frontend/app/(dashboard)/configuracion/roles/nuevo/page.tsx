"use client"

import { useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { RolForm } from "@/src/modules/configuracion/forms/rol-form"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function CrearRolPage() {
    const formRef = useRef<HTMLFormElement>(null!)
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/configuracion/roles")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Roles..." />
    }

    return (
        <>
            <Header
                title="Nuevo Rol"
                breadcrumb={["configuracion", "Roles", "Nuevo"]}
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
                            <span className="hidden sm:inline">Crear Rol</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <RolForm mode="create" formRef={formRef} />
                </div>
            </main>
        </>
    )
}