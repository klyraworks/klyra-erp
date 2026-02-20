"use client"

import Link from "next/link"
import {Header} from "@/src/shared/components/header"
import {MarcasSection} from "@/src/modules/inventario/components/marca-section"
import {useRouter} from "next/navigation";
import {useState} from "react";
import {LoadingScreen} from "@/components/ui/loading-screen";

export default function NuevaMarcaRoute() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddMarca = () => {
        setIsNavigating(true)
        router.push("/inventario/marcas/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Marcas..."/>
    }
    return (
        <>
            <Header
                title="Gestión de Productos en el Inventario"
                breadcrumb={["Inventario", "Marcas"]}
                actions={
                    <button
                        onClick={handleAddMarca}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        <i className="fa-solid fa-plus"></i>
                        Agregar Marca
                    </button>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <MarcasSection />
            </main>
        </>
    )
}