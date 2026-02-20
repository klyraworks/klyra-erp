"use client"

import {useState} from "react"
import {useRouter} from "next/navigation"
import {Header} from "@/src/shared/components/header"
import {LoadingScreen} from "@/components/ui/loading-screen"
import {CategoriasSection} from "@/src/modules/inventario/components/categorias-section";

export default function CategoriasPage() {
    const router = useRouter()
    const [isNavigating, setIsNavigating] = useState(false)

    const handleAddCategoria = () => {
        setIsNavigating(true)
        router.push("/inventario/categorias/nuevo")
    }

    if (isNavigating) {
        return <LoadingScreen message="Cargando Categorías..."/>
    }

    return (
        <>
            <Header
                title="Gestión de Productos en el Inventario"
                breadcrumb={["Inventario", "Categorías"]}
                actions={
                    <button
                        onClick={handleAddCategoria}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        <i className="fa-solid fa-plus"></i>
                        Agregar Categoría
                    </button>
                }
            />
            <main className="flex-1 overflow-y-auto p-6">
                <CategoriasSection/>
            </main>
        </>
    )
}