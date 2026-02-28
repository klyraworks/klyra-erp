"use client"

import { useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { EmpleadoForm } from "@/src/modules/rrhh/forms/empleado-form"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function CrearEmpleadoPage() {
    const formRef = useRef<HTMLFormElement>(null!)
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleVolver = () => {
        setIsNavigating(true)
        router.push("/rrhh/empleados")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Empleados..." />
    }

    return (
        <>
            <Header
                title="Nuevo Empleado"
                breadcrumb={["Seguridad", "Empleados", "Nuevo"]}
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
                            <span className="hidden sm:inline">Crear Empleado</span>
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <EmpleadoForm mode="create" formRef={formRef} />
                </div>
            </main>
        </>
    )
}