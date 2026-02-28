// frontend/app/(dashboard)/configuracion/departamentos/page.tsx
"use client"

import Link from "next/link"
import {Header} from "@/src/shared/components/header"
import {DepartamentosSection} from "@/src/modules/configuracion/components/departamentos-section"
import {useRouter} from "next/navigation";
import {useState} from "react";
import {LoadingScreen} from "@/components/ui/loading-screen";

export default function DepartamentosPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddDepartamento = () => {
        setIsNavigating(true)
        router.push("/configuracion/departamentos/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Departamentos..."/>
    }

    return (
        <>
            <Header
                title="Departamentos"
                breadcrumb={["Configuración", "Departamentos"]}
                actions={
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleAddDepartamento}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                            <i className="fa-solid fa-plus"></i>
                            Agregar Departamento
                        </button>
                    </div>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <DepartamentosSection/>
            </main>
        </>
    )
}