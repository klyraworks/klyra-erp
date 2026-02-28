"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/src/shared/components/header"
import { RolesSection } from "@/src/modules/configuracion/components/roles-section"
import { LoadingScreen } from "@/components/ui/loading-screen"

export default function RolesPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddRol = () => {
        setIsNavigating(true)
        router.push("/configuracion/roles/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Roles..." />
    }

    return (
        <>
            <Header
                title="Roles"
                breadcrumb={["Configuracion", "Roles"]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleAddRol}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Rol
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <RolesSection />
            </main>
        </>
    )
}