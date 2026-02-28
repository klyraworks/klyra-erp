// frontend/app/(dashboard)/configuracion/puestos/page.tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { PuestosSection } from "@/src/modules/configuracion/components/puestos-section"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function PuestosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddPuesto = () => {
        setIsNavigating(true)
        router.push("/configuracion/puestos/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Puestos..." />
    }

    return (
        <>
            <Header
                title="Puestos"
                breadcrumb={["RRHH", "Puestos"]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleAddPuesto}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Puesto
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <PuestosSection />
            </main>
        </>
    )
}