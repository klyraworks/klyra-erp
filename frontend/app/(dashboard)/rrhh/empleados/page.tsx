"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { EmpleadosSection } from "@/src/modules/rrhh/components/empleados-section"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function EmpleadosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddEmpleado = () => {
        setIsNavigating(true)
        router.push("/rrhh/empleados/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Empleados..." />
    }

    return (
        <>
            <Header
                title="Empleados"
                breadcrumb={["Seguridad", "Empleados"]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleAddEmpleado}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Empleado
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <EmpleadosSection />
            </main>
        </>
    )
}